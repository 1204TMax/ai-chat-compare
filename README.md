# AI chat tools compared — data + generator

Source data and the static-site generator behind **https://compare.chattcy.top** — a comparison site for AI chat assistants.

## What's here

- `data/en/products.json` — 11 tools with pricing, context windows, platforms and strengths, each field checked against the vendor's own page (see `sources` / `uncertain` per product).
- `data/en/compare*.json` — head-to-head write-ups.
- `build.py` — generates a fully server-rendered static site (unique title/description/canonical per page, JSON-LD, sitemap).
- `lint.py` — pre-publish checks: unique metadata, one `h1` per page, word count, broken internal links, JSON-LD validity.

```bash
python3 build.py     # writes dist/
python3 lint.py      # fails loudly on duplicates, short pages, broken links
```

## Live pages worth a look

- [All comparisons](https://compare.chattcy.top/vs/)
- [Context-limit checker](https://compare.chattcy.top/tools/context-check/) — paste text, see which tools can hold it
- [Free tiers compared](https://compare.chattcy.top/free/)

Facts are dated: every page states the day it was checked, and where a number couldn't be confirmed it says so instead of guessing.

MIT for the code; the written content is © the site.
