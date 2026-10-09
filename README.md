Ported from dissected.notion.site using Codex. Apologies for the ugly format.

# disSECted

An example-driven analysis of AI disclosure and SEC comment letters.

The site is plain HTML, CSS, and JavaScript and deploys through GitHub Pages.

## Local preview

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Source fidelity and datasets

The copy and three Parquet downloads come from [the original Notion site](https://dissected.notion.site/). Keep the author's wording and punctuation intact, including the text inside collapsible sections.

Run the deployment checks locally with:

```bash
python3 scripts/verify_site.py
```

`tests/notion-source.json` records the public source text and SHA-256 checksums of the original attachments as captured on October 9, 2026. The check ignores layout whitespace, but fails if source text is missing/changed, a dataset is missing/modified, or a local link is broken. GitHub Pages runs it before deployment. Update the fixture only when intentionally updating the source material.
