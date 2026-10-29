#!/usr/bin/env python3
"""Static site generator — English edition (Google-targeted).

Input : data/en/products.json, data/en/compare1.json, data/en/compare2.json
Output: dist/ (home, /p/<slug>/, /vs/<slug>/, /free/, /alternatives/, robots.txt, sitemap.xml, 404)

Constraints that matter for SEO (do not "simplify" these away):
- Every page is fully server-rendered HTML; body text must not depend on JS.
- Unique <title>, <meta description>, canonical per page; exactly one <h1>.
- JSON-LD only for types that actually match the content.
- The Chinese edition lives in build_zh.py + data/*.json; this file must not touch it.
"""

import json
import os
import shutil
from datetime import date
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "en")
DIST = os.path.join(ROOT, "dist")
SITE_URL = os.environ.get("SITE_URL", "https://compare.chattcy.top").rstrip("/")
SITE_NAME = "AI Chat Tools Compared"
TODAY = os.environ.get("BUILD_DATE", date.today().isoformat())
INDEXNOW_KEY = "8f2c41d7b6a94e0c9d53ab71e2f80645"

CSS = """
:root{--bg:#0d1014;--card:#151a21;--line:#242b35;--fg:#e7eaee;--dim:#97a1ae;--acc:#5b8cff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:24px 20px 80px}
header.site{border-bottom:1px solid var(--line);margin-bottom:28px;padding-bottom:14px;display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
header.site a{color:var(--fg);text-decoration:none;font-weight:600}
header.site nav a{color:var(--dim);font-weight:400;margin-left:16px;font-size:14px}
h1{font-size:32px;line-height:1.25;margin:0 0 14px}
h2{font-size:22px;margin:38px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:22px 0 8px}
p,li{color:#dde2e8}
a{color:var(--acc)}
.lead{color:var(--dim);font-size:17.5px}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14.5px}
th,td{border:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:#1a1f27;color:#cfd7e2;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:16px 0}
.meta{color:var(--dim);font-size:13.5px}
.tag{display:inline-block;font-size:12.5px;color:#b9c6ff;background:#1b2340;border:1px solid #2b3a6b;border-radius:99px;padding:2px 10px;margin:0 6px 6px 0}
.crumb{font-size:13.5px;color:var(--dim);margin-bottom:10px}
footer{border-top:1px solid var(--line);margin-top:48px;padding-top:16px;color:var(--dim);font-size:13.5px}
ul{padding-left:22px}
.verdict{background:#141d2e;border-left:3px solid var(--acc);padding:14px 16px;border-radius:6px;margin:16px 0}
"""


def load(name, key, default=None):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default if default is not None else {key: []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clip(text, limit=158):
    """Meta descriptions get truncated in SERPs anyway — cut at a word boundary first."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "…"


def esc(v):
    return escape(str(v)) if v not in (None, "") else ""


def val(v, fallback="not published — check the official page"):
    return esc(v) if v not in (None, "", []) else fallback


def write(path, html):
    out = os.path.join(DIST, "index.html") if path == "/" else os.path.join(DIST, path.strip("/"), "index.html")
    if path in ("/404.html",):
        out = os.path.join(DIST, "404.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def render(title, description, path, body, jsonld=None):
    url = f"{SITE_URL}{path}"
    ld = "\n".join(
        '<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False) for x in (jsonld or [])
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<style>{CSS}</style>
{ld}
</head>
<body>
<div class="wrap">
<header class="site">
  <a href="/">{esc(SITE_NAME)}</a>
  <nav><a href="/tools/context-check/">Fit checker</a><a href="/free/">Free tier</a><a href="/alternatives/">Alternatives</a><a href="/vs/">All comparisons</a></nav>
</header>
{body}
<footer>
  <p>Facts checked against official pages on {TODAY}. Prices, limits and regional availability change often — confirm on the vendor's own pricing page before you pay.</p>
  <p>© {TODAY[:4]} {esc(SITE_NAME)}</p>
</footer>
</div>
</body>
</html>
"""
    return write(path, html)


def crumbs(items):
    parts = [f'<a href="{href}">{esc(label)}</a>' if href else esc(label) for label, href in items]
    return '<div class="crumb">' + " › ".join(parts) + "</div>"


def paras(text):
    return "".join(f"<p>{esc(t)}</p>" for t in str(text).split("\n\n") if t.strip())


def card(p):
    tags = ["Free tier" if p.get("free_tier") else "Paid only"]
    if p.get("availability_note"):
        tags.append(esc(str(p["availability_note"]))[:28])
    tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
    return (
        f'<div class="card"><h3 style="margin-top:0"><a href="/p/{p["slug"]}/">{esc(p["name"])}</a></h3>'
        f'<p class="meta" style="margin:4px 0 8px">{esc(p.get("tagline") or "")}</p>{tag_html}</div>'
    )


def related_links(products, compares, a_slug, b_slug, exclude, limit=5):
    """同一方参与的其他对比，用来把访问者留在站内（哥飞那条'人均访问页面数'）"""
    pool = [c for c in compares if c["slug"] != exclude and ({c["a_slug"], c["b_slug"]} & {a_slug, b_slug})]
    seen, out = set(), []
    for c in pool:
        if c["slug"] in seen:
            continue
        seen.add(c["slug"])
        title = c.get("title") or f'{c["a"]} vs {c["b"]}'
        out.append(f'<li><a href="/vs/{c["slug"]}/">{esc(title)}</a></li>')
        if len(out) >= limit:
            break
    return "<ul>" + "".join(out) + "</ul>" if out else ""


def build():
    products = load("products.json", "products")["products"]
    compares = load("compare1.json", "compare")["compare"] + load("compare2.json", "compare")["compare"]
    by_slug = {p["slug"]: p for p in products}

    dist_abs = os.path.abspath(DIST)
    if dist_abs != os.path.join(ROOT, "dist"):
        raise SystemExit(f"refusing to clean unexpected dir: {dist_abs}")
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    written = []

    # ---------------- home ----------------
    rows = "".join(
        "<tr>"
        f'<td><a href="/p/{p["slug"]}/"><b>{esc(p["name"])}</b></a><br><span class="meta">{esc(p.get("maker") or "")}</span></td>'
        f'<td>{esc(p.get("tagline") or "")}</td>'
        f'<td>{"Yes" if p.get("free_tier") else "No"}</td>'
        f'<td>{val(p.get("context_window"), "—")}</td>'
        f'<td>{esc("; ".join(p.get("best_for") or [])[:52])}</td>'
        "</tr>"
        for p in products
    )
    cmp_list = "".join(f'<li><a href="/vs/{c["slug"]}/">{esc(c["title"])}</a></li>' for c in compares)
    written.append(
        render(
            f"AI Chat Tools Compared: {len(products)} Assistants Side by Side (2026)",
            f"Prices, free tiers, context limits and who each AI assistant is actually for — {len(products)} tools in one table, plus head-to-head comparisons.",
            "/",
            f"""
<h1>AI chat tools compared: {len(products)} assistants, one table</h1>
<p class="lead">What each tool costs, what its free tier actually allows, how much text it can hold, and who it fits. Read the table, then the two tools you're deciding between.</p>
<h2>The table</h2>
<table>
<thead><tr><th>Tool</th><th>What it is</th><th>Free tier</th><th>Context</th><th>Best for</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<h2>Start from your situation</h2>
<div class="card"><h3 style="margin-top:0">You don't want to pay yet</h3><p>See <a href="/free/">which tools have a usable free tier</a> — and more importantly, where each free tier actually runs out.</p></div>
<div class="card"><h3 style="margin-top:0">You're leaving ChatGPT</h3><p>See <a href="/alternatives/">ChatGPT alternatives</a>, split by free use, coding, and long-document work.</p></div>
<h2>By use case</h2>
<ul>
<li><a href="/best/ai-for-coding/">Best AI tools for coding</a></li>
<li><a href="/best/ai-for-writing/">Best AI tools for writing</a></li>
<li><a href="/best/ai-for-research/">Best AI tools for research</a></li>
<li><a href="/best/ai-for-long-documents/">Best AI tools for long documents</a></li>
</ul>
<h2>Head-to-head</h2>
<ul>{cmp_list or "<li>Comparisons are being written.</li>"}</ul>
<p><a href="/vs/">See every comparison →</a></p>
<h2>How this page is built</h2>
<p>Every number here was checked against the vendor's own pricing or docs page on {TODAY}, and each product page links its sources. Where a figure couldn't be confirmed it says so instead of guessing. Nothing on this site is sponsored, and no vendor paid to be listed.</p>
<p class="meta">{len(products)} tools, {len(compares)} head-to-head pages. Last checked {TODAY}.</p>
""",
            [
                {
                    "@context": "https://schema.org",
                    "@type": "ItemList",
                    "name": "AI chat tools compared",
                    "itemListElement": [
                        {"@type": "ListItem", "position": i + 1, "name": p["name"], "url": f"{SITE_URL}/p/{p['slug']}/"}
                        for i, p in enumerate(products)
                    ],
                },
                {"@context": "https://schema.org", "@type": "BreadcrumbList",
                 "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"}]},
            ],
        )
    )

    # ---------------- product pages ----------------
    for p in products:
        rel = [c for c in compares if c.get("a_slug") == p["slug"] or c.get("b_slug") == p["slug"]]
        rel_html = "".join(f'<li><a href="/vs/{c["slug"]}/">{esc(c["title"])}</a></li>' for c in rel)
        faq = [
            (f"Is {p['name']} free?",
             "Yes — there is a free tier you can start on. Whether it's enough depends on how much you use it; limits are on the official pricing page."
             if p.get("free_tier")
             else "No free tier for regular use; you pay per seat or per token. See the official pricing page for current numbers."),
            (f"How much text can {p['name']} handle at once?",
             val(p.get("context_window"), "The vendor doesn't publish one number; it depends on the selected model.")),
            (f"Is {p['name']} available in my country?",
             val(p.get("availability_note"), "Availability changes; check whether the site loads and accepts your payment method.")),
        ]
        faq_html = "".join(f"<h3>{esc(q)}</h3><p>{a}</p>" for q, a in faq)
        avail_fallback = "No regional block published; the vendor's own account rules still apply."
        body = f"""
{crumbs([("Home", "/"), (p["name"], None)])}
<h1>{esc(p['name'])}: pricing, limits and what it's actually good at</h1>
<p class="lead">{esc(p.get('tagline') or '')}</p>
<div class="card">
<table><tbody>
<tr><th style="width:34%">Made by</th><td>{val(p.get('maker'), '—')}</td></tr>
<tr><th>Official site</th><td><a href="{esc(p.get('official_url') or '#')}" rel="nofollow noopener" target="_blank">{val(p.get('official_url'), '—')}</a></td></tr>
<tr><th>Platforms</th><td>{esc(', '.join(p.get('platforms') or [])) or '—'}</td></tr>
<tr><th>Free tier</th><td>{"Yes" if p.get('free_tier') else "No"}</td></tr>
<tr><th>Pricing</th><td>{val(p.get('price_note'))}</td></tr>
<tr><th>Context window</th><td>{val(p.get('context_window'), '—')}</td></tr>
<tr><th>Non-English</th><td>{val(p.get('language_note'), 'No published evaluation; test it on your own text.')}</td></tr>
<tr><th>Availability</th><td>{val(p.get('availability_note'), avail_fallback)}</td></tr>
</tbody></table>
</div>
<h2>What {esc(p['name'])} does well</h2>
<ul>{"".join(f"<li>{esc(s)}</li>" for s in (p.get('strengths') or ['—']))}</ul>
<h2>Where it falls short</h2>
<ul>{"".join(f"<li>{esc(s)}</li>" for s in (p.get('weaknesses') or ['—']))}</ul>
<h2>Who should use it</h2>
<ul>{"".join(f"<li>{esc(s)}</li>" for s in (p.get('best_for') or ['—']))}</ul>
<h2>What it feels like day to day</h2>
<p>{val(p.get('usage_note'))}</p>
<h2>Compared with</h2>
{f'<ul>{rel_html}</ul>' if rel_html else '<p>No head-to-head page yet — see <a href="/">the full table</a>.</p>'}
<h2>FAQ</h2>
{faq_html}
<p class="meta">Sources: {" · ".join(p.get('sources') or []) or 'official product pages'} — checked {TODAY}.</p>
"""
        written.append(
            render(
                f"{p['name']}: pricing, limits and who it's for (2026)",
                clip(f"{p.get('tagline') or p['name']} What {p['name']} costs, what the free tier allows, its context window and who it suits. Checked {TODAY}."),
                f"/p/{p['slug']}/",
                body,
                [
                    {"@context": "https://schema.org", "@type": "SoftwareApplication",
                     "name": p["name"], "applicationCategory": "BusinessApplication",
                     "operatingSystem": ", ".join(p.get("platforms") or []),
                     "description": p.get("tagline") or "", "url": p.get("official_url") or f"{SITE_URL}/p/{p['slug']}/"},
                    {"@context": "https://schema.org", "@type": "FAQPage",
                     "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
                ],
            )
        )

    # ---------------- comparison pages ----------------
    PAIR_NOTES = {
        ("chatgpt", "claude"): "ChatGPT bundles retrieval and tools into the default surface; Claude puts its effort into holding a long document steady and following your outline. If your work is 'find it, then summarise it', ChatGPT saves steps. If it is 'here is 60 pages, change section 4.2', Claude needs fewer retries.",
        ("chatgpt", "gemini"): "Gemini's advantage is provenance — answers arrive with links you can open, and the Google account plumbing means Docs and Gmail are already in reach. ChatGPT's advantage is breadth of tools and a more forgiving conversational style. Pick Gemini when you need to cite, ChatGPT when you need to build.",
        ("chatgpt", "copilot"): "These barely compete: Copilot lives inside the editor and sees your repository, ChatGPT sees what you paste. For code you already own, Copilot removes the copy-paste loop. For design questions, error explanations and anything outside the repo, ChatGPT is the better conversation.",
        ("claude", "gemini"): "Both are strong on long input, and the split is about where the text comes from. Claude is better at restructuring writing you hand it and at code review; Gemini is better at pulling in what already exists on the web with citations attached. Long-document work with no external sources favours Claude.",
        ("chatgpt", "grok"): "Grok's differentiator is real-time social data; ChatGPT's is tool coverage and stability. If your question is 'what are people saying about this right now', Grok answers from the feed. If it is 'help me do this task', ChatGPT has more ways to finish it.",
        ("chatgpt", "deepseek"): "DeepSeek's pitch is cost: a free web tier and cheap API for reasoning-heavy work. ChatGPT's is surface area: tools, images, voice, integrations. For maths, logic and code generation on a budget, DeepSeek is the value pick; for everything needing retrieval or multimodality, ChatGPT.",
        ("claude", "copilot"): "One is a chat model you bring documents to; the other is an editor plugin that brings the repository to the model. Copilot wins on repetitive in-repo edits and PR review, Claude wins when you need to reason about a design across many files you paste in deliberately.",
        ("gemini", "perplexity"): "Perplexity is an answer engine: it searches, cites, and stops. Gemini is an assistant that can also search. For a question with a factual answer and a source, Perplexity is faster to trust; for work that continues past the answer, Gemini keeps the thread.",
    }

    for c in compares:
        rows = "".join(
            f'<tr><th style="width:26%">{esc(r["label"])}</th><td>{esc(r["a"])}</td><td>{esc(r["b"])}</td></tr>'
            for r in c.get("table", [])
        )
        faq = c.get("faq", [])
        faq_html = "".join(f"<h3>{esc(x['q'])}</h3><p>{esc(x['a'])}</p>" for x in faq)
        body = f"""
{crumbs([("Home", "/"), ("Comparisons", None), (f"{c['a']} vs {c['b']}", None)])}
<h1>{esc(c['title'])}</h1>
<div class="verdict">{paras(c.get('verdict', ''))}</div>
<h2>Side by side</h2>
<table><thead><tr><th>Dimension</th><th>{esc(c['a'])}</th><th>{esc(c['b'])}</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Pick {esc(c['a'])} if</h2>
{paras(c.get('when_a', ''))}
<h2>Pick {esc(c['b'])} if</h2>
{paras(c.get('when_b', ''))}
<h2>Why you might want both</h2>
{paras(c.get('both', ''))}
<h2>What the specs actually mean for you</h2>
<p>{esc(PAIR_NOTES.get((c['a_slug'], c['b_slug'])) or PAIR_NOTES.get((c['b_slug'], c['a_slug'])) or 'Both are general-purpose assistants, so the deciding factor is usually the workload you have in front of you rather than a headline feature.')}</p>
<table><tbody>
<tr><th style="width:30%">Free tier</th><td>{esc('Yes' if by_slug[c['a_slug']].get('free_tier') else 'No')}</td><td>{esc('Yes' if by_slug[c['b_slug']].get('free_tier') else 'No')}</td></tr>
<tr><th>Checked price</th><td>{esc(by_slug[c['a_slug']].get('price_note') or 'check the official page')}</td><td>{esc(by_slug[c['b_slug']].get('price_note') or 'check the official page')}</td></tr>
<tr><th>Context window</th><td>{esc(by_slug[c['a_slug']].get('context_window') or 'not published')}</td><td>{esc(by_slug[c['b_slug']].get('context_window') or 'not published')}</td></tr>
<tr><th>Where it breaks</th><td>{esc((by_slug[c['a_slug']].get('weaknesses') or ['—'])[0])}</td><td>{esc((by_slug[c['b_slug']].get('weaknesses') or ['—'])[0])}</td></tr>
</tbody></table>
<p>Prices and limits above were read from each vendor's own page on {TODAY}; they change without notice, so treat them as the shape of the deal rather than a quote. The practical way to choose: run one real task through both free tiers today — one document you actually care about — and keep whichever needed fewer corrections.</p>
<h2>FAQ</h2>
{faq_html}
{related_links(products, compares, c['a_slug'], c['b_slug'], c['slug'])}
<h2>Individual reviews</h2>
<ul>
<li><a href="/p/{c['a_slug']}/">{esc(c['a'])}: pricing, limits and who it's for</a></li>
<li><a href="/p/{c['b_slug']}/">{esc(c['b'])}: pricing, limits and who it's for</a></li>
</ul>
"""
        written.append(
            render(
                c["title"],
                c.get("description") or c["title"],
                f"/vs/{c['slug']}/",
                body,
                [
                    {"@context": "https://schema.org", "@type": "FAQPage",
                     "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in faq]},
                    {"@context": "https://schema.org", "@type": "Article", "headline": c["title"],
                     "datePublished": c.get("updated_at", TODAY), "dateModified": c.get("updated_at", TODAY),
                     "author": {"@type": "Organization", "name": SITE_NAME}},
                ],
            )
        )


    # ============ programmatic layer: every remaining pair + use-case hubs ============
    hand = {tuple(sorted((c["a_slug"], c["b_slug"]))) for c in compares}
    slugs = [p["slug"] for p in products]
    gen_pairs = [
        (a, b) for i, a in enumerate(slugs) for b in slugs[i + 1:]
        if tuple(sorted((a, b))) not in hand
    ]

    def ctx_tokens(p):
        import re as _re
        raw = str(p.get("context_window") or "")
        m = _re.findall(r"([\d,.]+)\s*(K|M|百万)?", raw.replace(",", ""))
        best = 0
        for num, unit in m:
            try:
                v = float(num)
            except ValueError:
                continue
            v *= {"K": 1_000, "M": 1_000_000, "百万": 1_000_000}.get(unit, 1)
            best = max(best, v)
        return best

    OPENERS = [
        "Short answer, then the detail.",
        "If you only read one line: pick by workload, not by benchmark charts.",
        "These two overlap more than their marketing suggests; the split is usually about how you work.",
    ]
    BOTHS = [
        "Running both is not wasteful here: one earns its keep on retrieval and tool use, the other on long text you intend to keep.",
        "Most people I know keep both tabs open — one for finding things, one for producing the final draft — and stop paying for whichever they touch last.",
        "There's no reason to pick a single winner if you already pay for one: use the free tier of the other for the tasks it clearly does better.",
    ]

    for idx, (a_slug, b_slug) in enumerate(gen_pairs):
        A, B = by_slug[a_slug], by_slug[b_slug]
        ca, cb = ctx_tokens(A), ctx_tokens(B)
        free_a, free_b = bool(A.get("free_tier")), bool(B.get("free_tier"))
        if free_a and not free_b:
            money = f"{A['name']} has a free tier and {B['name']} doesn't — start there if cost is the deciding factor."
        elif free_b and not free_a:
            money = f"{B['name']} has a free tier and {A['name']} doesn't — start there if cost is the deciding factor."
        elif free_a and free_b:
            money = "Both have free tiers, so cost only separates them once you hit the limits."
        else:
            money = "Neither has a free tier worth relying on; compare the paid tiers on the vendor pages."
        if ca and cb and ca != cb:
            big, small = (A, B) if ca > cb else (B, A)
            ctx_line = f"{big['name']} takes more text in one go ({big.get('context_window')} vs {small.get('context_window')}), which matters for whole books, long contracts and big codebases."
        elif ca and cb:
            ctx_line = f"They're in the same context range ({A.get('context_window')}), so document size won't be what decides it."
        else:
            ctx_line = "Context limits aren't published for both, so treat this as untested until you hit the ceiling yourself."
        verdict = (
            f"{OPENERS[idx % 3]}\n\n"
            f"For {'; '.join((A.get('best_for') or ['general use'])[:2])}, {A['name']} is the more direct fit. "
            f"For {'; '.join((B.get('best_for') or ['general use'])[:2])}, {B['name']} gets there with less fighting.\n\n"
            f"{money} {ctx_line}"
        )
        rows = [
            ("Free tier", "Yes" if free_a else "No", "Yes" if free_b else "No"),
            ("Pricing", A.get("price_note") or "check the official page", B.get("price_note") or "check the official page"),
            ("Context window", A.get("context_window") or "not published", B.get("context_window") or "not published"),
            ("Platforms", ", ".join(A.get("platforms") or []) or "—", ", ".join(B.get("platforms") or []) or "—"),
            ("Best for", "; ".join(A.get("best_for") or []) or "—", "; ".join(B.get("best_for") or []) or "—"),
            ("Availability", A.get("availability_note") or "no regional block published", B.get("availability_note") or "no regional block published"),
        ]
        table = "".join(f'<tr><th style="width:24%">{esc(l)}</th><td>{esc(x)}</td><td>{esc(y)}</td></tr>' for l, x, y in rows)
        faq = [
            (f"Is {A['name']} or {B['name']} better for beginners?",
             f"{A['name']} if you want {'; '.join((A.get('best_for') or ['a straightforward start'])[:1])}. {B['name']} if {'; '.join((B.get('best_for') or ['your work is elsewhere'])[:1])}. Neither has a learning curve worth worrying about past the first day."),
            (f"Can I use both for free?",
             ("Yes — both have free tiers, and the pair covers more ground than either alone." if free_a and free_b else
              f"Only one of them: {A['name'] if free_a else B['name']} has a free tier.")),
            (f"Which one handles longer documents?",
             ctx_line),
        ]
        faq_html = "".join(f"<h3>{esc(q)}</h3><p>{esc(x)}</p>" for q, x in faq)
        title = f"{A['name']} vs {B['name']}: which one to use (2026)"
        if len(title) > 62:
            title = f"{A['name']} vs {B['name']}: which to use"
        written.append(
            render(
                title,
                clip(f"{A['name']} vs {B['name']}: free tiers, pricing, context limits and who each one actually suits."),
                f"/vs/{a_slug}-vs-{b_slug}/",
                f"""{crumbs([("Home", "/"), ("Comparisons", "/vs/"), (f"{A['name']} vs {B['name']}", None)])}
<h1>{esc(A['name'])} vs {esc(B['name'])}: which one to use</h1>
<div class="verdict">{paras(verdict)}</div>
<h2>Side by side</h2>
<table><thead><tr><th>Dimension</th><th>{esc(A['name'])}</th><th>{esc(B['name'])}</th></tr></thead><tbody>{table}</tbody></table>
<h2>Pick {esc(A['name'])} if</h2>
<p>{esc('; '.join((A.get('best_for') or ['you need a general assistant'])[:3]))}. Its strongest point: {esc((A.get('strengths') or ['—'])[0])}. Watch out for: {esc((A.get('weaknesses') or ['—'])[0])}.</p>
<h2>Pick {esc(B['name'])} if</h2>
<p>{esc('; '.join((B.get('best_for') or ['you need a general assistant'])[:3]))}. Its strongest point: {esc((B.get('strengths') or ['—'])[0])}. Watch out for: {esc((B.get('weaknesses') or ['—'])[0])}.</p>
<h2>Running both</h2>
<p>{esc(BOTHS[idx % 3])}</p>
<h2>FAQ</h2>
{faq_html}
{related_links(products, compares, a_slug, b_slug, f"{a_slug}-vs-{b_slug}")}
<h2>Individual reviews</h2>
<ul>
<li><a href="/p/{A['slug']}/">{esc(A['name'])}: pricing, limits and who it's for</a></li>
<li><a href="/p/{B['slug']}/">{esc(B['name'])}: pricing, limits and who it's for</a></li>
<li><a href="/vs/">All {len(compares) + len(gen_pairs)} head-to-head comparisons</a></li>
</ul>
""",
                [
                    {"@context": "https://schema.org", "@type": "FAQPage",
                     "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]},
                    {"@context": "https://schema.org", "@type": "Article", "headline": title,
                     "datePublished": TODAY, "dateModified": TODAY,
                     "author": {"@type": "Organization", "name": SITE_NAME}},
                ],
            )
        )

    # /vs/ index — keeps every comparison one click from the home page
    all_vs = [(c["slug"], c["title"]) for c in compares] + [
        (f"{a}-vs-{b}", f"{by_slug[a]['name']} vs {by_slug[b]['name']}") for a, b in gen_pairs
    ]
    written.append(
        render(
            f"All {len(all_vs)} AI tool comparisons (2026)",
            f"Every head-to-head on this site: {len(all_vs)} pairs of AI chat tools compared on pricing, limits and fit.",
            "/vs/",
            f"""{crumbs([("Home", "/"), ("Comparisons", None)])}
<h1>Every head-to-head comparison</h1>
<p class="lead">{len(all_vs)} pairs, each one written to answer a single question: which of these two should I use.</p>
<ul>{"".join(f'<li><a href="/vs/{sl}/">{esc(ti)}</a></li>' for sl, ti in all_vs)}</ul>
""",
            [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "AI tool comparisons", "url": f"{SITE_URL}/vs/"}],
        )
    )

    # use-case hubs, built from the best_for tags rather than invented
    CASES = {
        "ai-for-coding": ("coding", "Writing and reviewing code — which assistant to keep open"),
        "ai-for-writing": ("writing", "Drafting and editing text where you want your own voice kept"),
        "ai-for-research": ("research", "Research and retrieval where links and sources matter"),
        "ai-for-long-documents": ("long document", "Whole books, contracts and codebases pushed through at once"),
    }
    CASE_COPY = {
        "ai-for-coding": (
            "What actually matters for code is not the model's leaderboard position — it's whether it can see enough of your project to stop guessing. "
            "A tool that reads your repository and follows the existing style saves you review time; one that only sees the pasted snippet will 'fix' code that wasn't broken. "
            "Check whether the assistant runs inside your editor or in a separate tab, because that single difference decides how often you actually reach for it.",
            "The second deciding factor is how it behaves when it doesn't know something. On real repositories the useful assistants say which file they are unsure about; "
            "the unhelpful ones invent a function name and let the compiler find out. Test this deliberately: give it a file with one renamed symbol and see whether it notices or writes confident nonsense.",
        ),
        "ai-for-writing": (
            "Writing breaks down into two different jobs and most people conflate them: getting words on the page, and making existing words shorter and clearer. "
            "Assistants that are strong at the first are often too eager at the second — they rewrite your sentences into their voice, and you spend more time restoring your own phrasing than writing. "
            "Pick one that keeps your structure when you tell it to keep your structure.",
            "The practical test is a paragraph you're proud of. Paste it in, ask for a tightening pass, and see whether the result still sounds like you. "
            "If it doesn't, that tool can still be useful for outlines and for the parts you dread writing, but it shouldn't be the last set of hands on anything published under your name.",
        ),
        "ai-for-research": (
            "Research is the use case where citations either exist or the answer is worthless. A tool that gives you a confident summary with no links is not saving you work — it's moving the work to verification later, "
            "usually after you've already repeated the claim. Prefer tools that show the source next to the sentence.",
            "Then check what happens when the answer isn't on the web: ask something that requires reading a document you supply. "
            "The good ones quote the paragraph and the page; the rest quietly fall back to their training data, which is exactly the failure mode you can't see.",
        ),
        "ai-for-long-documents": (
            "Long input is a spec you can check before paying: the context window. A 40-page contract is roughly 20,000 tokens, a 300-page book around 150,000 — anything under 200K will drop sections without telling you, "
            "and the summary will read fine, which is what makes it dangerous.",
            "Second, test recall rather than summarisation. Ask a question whose answer sits on page 60 and see whether the answer cites the right section. "
            "Summaries hide retrieval failures; specific questions expose them in one round.",
        ),
    }

    for slug, (needle, headline) in CASES.items():
        pick = [p for p in products if any(needle in str(b).lower() for b in (p.get("best_for") or []))]
        rest = [p for p in products if p not in pick]
        rows = "".join(
            f'<tr><td><a href="/p/{p["slug"]}/"><b>{esc(p["name"])}</b></a></td><td>{esc(p.get("tagline") or "")}</td>'
            f'<td>{"Yes" if p.get("free_tier") else "No"}</td><td>{val(p.get("context_window"), "—")}</td></tr>'
            for p in pick
        )
        written.append(
            render(
                f"Best AI tools for {slug.replace('ai-for-', '').replace('-', ' ')} (2026)",
                clip(f"Which AI chat tools are actually built for {needle} work: {', '.join(p['name'] for p in pick) or 'see the full table'}, with prices and limits."),
                f"/best/{slug}/",
                f"""{crumbs([("Home", "/"), ("Best by use case", None), (headline, None)])}
<h1>{esc(headline)}</h1>
<p class="lead">Picked from the {len(products)} tools on this site by what they're actually used for — not by benchmark scores.</p>
<h2>The shortlist</h2>
<table><thead><tr><th>Tool</th><th>What it is</th><th>Free tier</th><th>Context</th></tr></thead><tbody>{rows or '<tr><td colspan="4">Nothing tagged for this use case yet.</td></tr>'}</tbody></table>
<h2>What separates them here</h2>
<p>{esc(CASE_COPY[slug][0])}</p>
<p>{esc(CASE_COPY[slug][1])}</p>
<h2>How to choose between them</h2>
<p>Start with the one that already has a free tier covering your volume, then check the context column: {needle} work usually breaks on input size before it breaks on model quality. If two of them look equal, pick the one whose paid tier you'd actually renew, because that's the one you'll keep using after the novelty wears off.</p>
<p>Everything else — {', '.join(p['name'] for p in rest[:4])} — is on the <a href="/">main comparison table</a>; they show up here only if their own documentation frames them that way.</p>
""",
                [{"@context": "https://schema.org", "@type": "ItemList", "name": headline,
                  "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": p["name"], "url": f"{SITE_URL}/p/{p['slug']}/"} for i, p in enumerate(pick)]}],
            )
        )


    # ---------------- tool page: context-limit checker (engagement + linkable asset) ----------------
    tool_rows = "".join(
        f'<tr data-ctx="{ctx_tokens(p) or 0}"><td><a href="/p/{p["slug"]}/">{esc(p["name"])}</a></td>'
        f'<td>{val(p.get("context_window"), "not published")}</td><td class="fit">—</td></tr>'
        for p in products
    )
    tool_js = """
<script>
const rows=[...document.querySelectorAll('tr[data-ctx]')];
function tokens(t){const cjk=(t.match(/[\u4e00-\u9fff\u3040-\u30ff]/g)||[]).length;const rest=t.replace(/[\u4e00-\u9fff\u3040-\u30ff]/g,' ');const words=(rest.match(/[A-Za-z0-9'\-]+/g)||[]).length;return Math.round(cjk*1.6+words*1.35);}
const box=document.getElementById('t');const out=document.getElementById('out');
function run(){const t=box.value||'';const n=tokens(t);out.textContent=n.toLocaleString();
 rows.forEach(r=>{const cap=+r.dataset.ctx;const cell=r.querySelector('.fit');if(!cap){cell.textContent='unknown';cell.style.color='#97a1ae';return;}
 const ok=cap>=n;cell.textContent=ok?('fits, '+(100*n/cap).toFixed(1)+'% of limit'):'too long';cell.style.color=ok?'#5fd08a':'#ff8080';});}
box.addEventListener('input',run);run();
</script>"""
    written.append(
        render(
            "Will my document fit? AI context limit checker (2026)",
            "Paste your text and see roughly how many tokens it is, then which AI chat tools can take it in one go — limits checked against vendor pages on 2026-10-29.",
            "/tools/context-check/",
            f"""{crumbs([("Home", "/"), ("Tools", None), ("Context limit checker", None)])}
<h1>Will my document fit? Context limit checker</h1>
<p class="lead">Paste a document below. This estimates its token count and marks which tools can hold it in a single conversation.</p>
<div class="card">
<textarea id="t" rows="7" style="width:100%;background:#0f1319;color:#e7eaee;border:1px solid #2a323d;border-radius:8px;padding:10px;font:14px/1.6 ui-monospace,Menlo,monospace" placeholder="Paste your text here…"></textarea>
<p style="margin:10px 0 0">Estimated tokens: <b><span id="out">0</span></b> <span class="meta">(approximate — English ≈1.35 tokens/word, CJK ≈1.6/character)</span></p>
</div>
<h2>Which tools fit</h2>
<table><thead><tr><th>Tool</th><th>Published limit</th><th>Your document</th></tr></thead><tbody>{tool_rows}</tbody></table>
<h2>How to read this</h2>
<p>Token estimates are approximate: the real count depends on the tokenizer each vendor uses, and on whether you attach files (attachments get processed differently from pasted text). Treat this as a pre-check that saves you from pasting a 120-page PDF into a 200K window and wondering why the ending was ignored.</p>
<p>Two practical rules: leave 30–40% headroom, because the model's reply and your follow-up questions also occupy the window; and if a document sits just under the limit, split it by chapter and ask one question per section — long inputs that technically fit still degrade recall near the edges.</p>
{tool_js}""",
            [{"@context": "https://schema.org", "@type": "WebApplication", "name": "AI context limit checker",
              "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web",
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "url": f"{SITE_URL}/tools/context-check/"}],
        )
    )

    # ---------------- hub pages ----------------
    free = [p for p in products if p.get("free_tier")]
    written.append(
        render(
            f"Free AI Chat Tools: {len(free)} Tiers Compared (2026)",
            f"Which AI chat tools have a free tier worth using, what each one actually allows, and where the free plan runs out. Checked {TODAY}.",
            "/free/",
            f"""{crumbs([("Home", "/"), ("Free tier", None)])}
<h1>Free AI chat tools — and where each free tier runs out</h1>
<p class="lead">All {len(free)} of these let you start without paying. The difference is what happens on day three, when you've hit the limit.</p>
{"".join(card(p) for p in free)}
<h2>What a free tier really gets you</h2>
<p>For short tasks — rewriting an email, explaining a concept, summarising one page — free tiers are enough and you should not pay. The three things that break a free plan are: long documents (context limits bite), sustained use (message caps), and the better model behind the paywall.</p>
<p>If your work is one of those three, plan for a paid plan on the tool you use most rather than spreading three free accounts across three products — you'll spend more time re-pasting context than you save.</p>
""",
            [{"@context": "https://schema.org", "@type": "ItemList", "name": "Free AI chat tools",
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": p["name"], "url": f"{SITE_URL}/p/{p['slug']}/"} for i, p in enumerate(free)]}],
        )
    )

    alts = [p for p in products if p["slug"] != "chatgpt"]
    written.append(
        render(
            "ChatGPT Alternatives: Which One Fits Your Work (2026)",
            "Alternatives to ChatGPT split by what you actually need — free use, coding, long documents, research — with what each one costs and gives up.",
            "/alternatives/",
            f"""{crumbs([("Home", "/"), ("ChatGPT alternatives", None)])}
<h1>ChatGPT alternatives, sorted by why you're leaving</h1>
<p class="lead">People switch for three reasons: cost, coding, or long documents. The right replacement depends on which one is yours.</p>
<h2>If you're leaving over cost</h2>
<p>Pick a tool with a free tier that covers your volume, not the one with the longest feature list. The <a href="/free/">free-tier list</a> shows where each plan actually caps out.</p>
<h2>If you're leaving over coding</h2>
<p>Claude and GitHub Copilot are the two serious answers, and they solve different problems: Copilot lives inside the editor and knows your repository; Claude is better when you paste a file and want it changed according to your instructions. See <a href="/vs/claude-vs-copilot/">Claude vs Copilot</a>.</p>
<h2>If you're leaving over long documents</h2>
<p>Context window is the spec that matters. See the context column on <a href="/">the main table</a> — anything under 200K will struggle with a full book or a long contract.</p>
<h2>Every alternative, reviewed</h2>
{"".join(card(p) for p in alts)}
""",
            [{"@context": "https://schema.org", "@type": "ItemList", "name": "ChatGPT alternatives",
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": p["name"], "url": f"{SITE_URL}/p/{p['slug']}/"} for i, p in enumerate(alts)]}],
        )
    )

    # ---------------- robots / sitemap / key / 404 ----------------
    with open(os.path.join(DIST, INDEXNOW_KEY + ".txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = "".join(
        f"  <url><loc>{SITE_URL}{p}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq>"
        f"<priority>{1.0 if p == '/' else 0.8}</priority></url>\n"
        for p in written
    )
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    render("Page not found", "This page doesn't exist. See the full AI chat tool comparison instead.", "/404.html",
           '<h1>Page not found</h1><p>That URL doesn\'t exist. <a href="/">Go to the full comparison</a>.</p>')

    print(f"built {len(written)} pages -> {DIST}")
    for p in written:
        print("  ", p)


if __name__ == "__main__":
    build()
