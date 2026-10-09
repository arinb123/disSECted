#!/usr/bin/env python3
"""Check the migration against the public Notion copy and original attachments.

Only layout whitespace is ignored; wording and punctuation remain significant.
This uses the standard library so it can run before deployment without installs.
"""

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.sections = {}
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        section = attrs.get("id")
        if section:
            if section in self.ids:
                raise ValueError(f"Duplicate HTML id: {section}")
            self.ids.add(section)
            self.sections[section] = []
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.references.append(attrs[attribute])
        if tag not in VOID_TAGS:
            self.stack.append((tag, section))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, text):
        for _, section in self.stack:
            if section:
                self.sections[section].append(text)


def compact(text):
    return re.sub(r"\s+", "", text)


def verify(root=ROOT):
    fixture = json.loads((root / "tests/notion-source.json").read_text(encoding="utf-8"))
    parser = SiteParser()
    parser.feed((root / "index.html").read_text(encoding="utf-8"))
    errors = []
    count = 0
    for section, source in fixture["sections"].items():
        actual = compact("".join(parser.sections.get(section, [])))
        for block in source["blocks"]:
            count += 1
            if compact(block["text"]) not in actual:
                errors.append(f"Source text changed/missing in #{section} ({block['id']}): {block['text'][:100]}")
    for reference in parser.references:
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            continue
        if not url.path and url.fragment and unquote(url.fragment) not in parser.ids:
            errors.append(f"Broken section link: {reference}")
        if url.path and not (root / unquote(url.path)).is_file():
            errors.append(f"Missing local asset: {reference}")
    for name, expected in fixture["datasets"].items():
        path = root / "data" / name
        if not path.is_file():
            errors.append(f"Missing original dataset: {name}")
            continue
        data = path.read_bytes()
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            errors.append(f"Dataset differs from the original Notion attachment: {name}")
        if data[:4] != b"PAR1" or data[-4:] != b"PAR1":
            errors.append(f"Invalid Parquet header/footer: {name}")
        if f"data/{name}" not in parser.references:
            errors.append(f"Original dataset is not linked: {name}")
    if errors:
        raise ValueError("\n".join(errors))
    return f"Verified {count} source text blocks, {len(fixture['datasets'])} original datasets, and all local links/assets."


if __name__ == "__main__":
    try:
        print(verify())
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
