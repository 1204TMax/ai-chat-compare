#!/usr/bin/env python3
"""Pre-publish checks for the English edition.

Checks (all observable by a crawler):
1. unique <title>, 20-65 chars  2. unique meta description, 70-165 chars
3. canonical self-referencing, exactly one <h1>, lang="en"
4. body ≥ 250 words once tags/scripts are stripped
5. JSON-LD parses  6. ≥ 3 internal links (no orphan pages)
"""

import json
import os
import re
import sys
from collections import Counter

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
SITE = "https://compare.chattcy.top"
MIN_WORDS = 250


def words(html):
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", body))


def main():
    pages, titles, descs, problems = [], [], [], []
    for root, _, files in os.walk(DIST):
        for f in files:
            if f == "index.html":
                pages.append(os.path.join(root, f))
    print(f"{'page':40s} {'words':>6s} {'h1':>3s} {'links':>5s} {'title':>6s}")
    for path in sorted(pages):
        html = open(path, encoding="utf-8").read()
        rel = "/" + os.path.relpath(os.path.dirname(path), DIST).replace(".", "").strip("/") + "/"
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        desc = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
        canon = re.search(r'<link rel="canonical" href="(.*?)">', html)
        h1 = len(re.findall(r"<h1[\s>]", html))
        links = len(set(re.findall(r'href="(/[^"#]*)"', html)))
        w = words(html)
        t = title.group(1) if title else ""
        d = desc.group(1) if desc else ""
        titles.append(t)
        descs.append(d)
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                json.loads(m)
            except Exception as exc:
                problems.append(f"{rel}: JSON-LD invalid: {exc}")
        if not t:
            problems.append(f"{rel}: missing title")
        elif not 20 <= len(t) <= 65:
            problems.append(f"{rel}: title length {len(t)}")
        if not d:
            problems.append(f"{rel}: missing description")
        elif not 70 <= len(d) <= 165:
            problems.append(f"{rel}: description length {len(d)}")
        if not canon or not canon.group(1).startswith(SITE):
            problems.append(f"{rel}: canonical wrong ({canon.group(1) if canon else 'missing'})")
        if h1 != 1:
            problems.append(f"{rel}: h1 count {h1}")
        if 'lang="en"' not in html:
            problems.append(f"{rel}: lang is not en")
        if w < MIN_WORDS:
            problems.append(f"{rel}: only {w} words")
        if links < 3:
            problems.append(f"{rel}: only {links} internal links")
        # 内链必须真有落地页：换内容后最容易出现 404 链接
        for href in set(re.findall(r'href="(/[^"#]*)"', html)):
            target = os.path.join(DIST, href.strip("/"), "index.html") if href != "/" else os.path.join(DIST, "index.html")
            if not os.path.exists(target):
                problems.append(f"{rel}: broken internal link {href}")
        print(f"{rel:40s} {w:6d} {h1:3d} {links:5d} {len(t):6d}")

    for label, seq in (("title", titles), ("description", descs)):
        dup = [x for x, c in Counter(seq).items() if c > 1 and x]
        if dup:
            problems.append(f"duplicate {label}: {dup[:3]}")
    print(f"\n{len(pages)} pages, {len(set(titles))} unique titles, {len(set(descs))} unique descriptions")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
