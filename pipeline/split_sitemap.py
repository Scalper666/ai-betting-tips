"""Split the generated sitemap into themed files.

Astro emits one sitemap-0.xml with every URL in it. That works, but Search
Console reports coverage per submitted sitemap — so a single file tells you
"390 of 4830 discovered" and nothing about WHICH pages are stuck. Splitting by
page type turns the sitemaps report into a diagnostic: matches vs h2h vs guides,
each with its own discovered/indexed count.

Runs after `astro build`, rewrites sitemap-index.xml to point at the themed
files, and leaves sitemap-0.xml in place so the previously submitted URL keeps
working.

Usage:  python pipeline/split_sitemap.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = "https://ai-betting-tips.com"

# Order matters: first match wins. Localized paths are grouped by language
# rather than by type, so hreflang clusters can be checked as a whole.
GROUPS = [
    ("i18n-es",     lambda p: p.startswith("/es/")),
    ("i18n-pt",     lambda p: p.startswith("/pt/")),
    ("i18n-de",     lambda p: p.startswith("/de/")),
    ("i18n-fr",     lambda p: p.startswith("/fr/")),
    ("matches",     lambda p: p.startswith("/predictions/") and not p.startswith("/predictions/daily")),
    ("h2h",         lambda p: p.startswith("/h2h/")),
    ("teams",       lambda p: p.startswith("/team/") or p.startswith("/teams")),
    ("leagues",     lambda p: any(p.startswith(x) for x in
                        ("/league/", "/table", "/results", "/top-scorers", "/seasons", "/tips/"))),
    ("operators",   lambda p: any(p.startswith(x) for x in
                        ("/bookmakers", "/casinos", "/countries", "/bonuses", "/betting-apps"))),
    ("content",     lambda p: any(p.startswith(x) for x in
                        ("/guides", "/glossary", "/research", "/news", "/tools", "/model"))),
    ("core",        lambda p: True),   # home, screener, legal, daily archives, everything else
]

URL_RE = re.compile(r"<url>.*?</url>", re.S)
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")


def main() -> int:
    src = DIST / "sitemap-0.xml"
    if not src.exists():
        print("✗ dist/sitemap-0.xml not found — run the build first", file=sys.stderr)
        return 1

    xml = src.read_text(encoding="utf-8")
    entries = URL_RE.findall(xml)
    if not entries:
        print("✗ no <url> entries found", file=sys.stderr)
        return 1

    buckets: dict[str, list[str]] = {name: [] for name, _ in GROUPS}
    for entry in entries:
        m = LOC_RE.search(entry)
        path = m.group(1).replace(SITE, "") or "/" if m else "/"
        for name, test in GROUPS:
            if test(path):
                buckets[name].append(entry)
                break

    header = ('<?xml version="1.0" encoding="UTF-8"?>'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    written = []
    for name, items in buckets.items():
        if not items:
            continue
        out = DIST / f"sitemap-{name}.xml"
        out.write_text(header + "".join(items) + "</urlset>", encoding="utf-8")
        written.append((name, len(items)))

    # rewrite the index: themed files plus the original flat file, so the
    # already-submitted sitemap-0.xml keeps resolving
    lastmod = ""
    m = re.search(r"<lastmod>([^<]+)</lastmod>", (DIST / "sitemap-index.xml").read_text(encoding="utf-8"))
    if m:
        lastmod = f"<lastmod>{m.group(1)}</lastmod>"
    # The index lists ONLY the themed files. sitemap-0.xml stays on disk so the
    # originally submitted URL keeps resolving, but listing it here too would
    # double-count every URL in Search Console (5,220 reported for 4,830 pages).
    parts = "".join(
        f"<sitemap><loc>{SITE}/sitemap-{name}.xml</loc>{lastmod}</sitemap>" for name, _ in written
    )
    (DIST / "sitemap-index.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + parts +
        "</sitemapindex>",
        encoding="utf-8",
    )

    total = sum(n for _, n in written)
    for name, n in sorted(written, key=lambda x: -x[1]):
        print(f"  sitemap-{name}.xml: {n}")
    print(f"✓ {len(written)} themed sitemaps, {total} urls (index rewritten)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
