"""Permanent registry of every match page the site has ever built.

The site's own design note says match pages are eternal, but the path set was
feed ∪ settlement-archive — and the settlement archive only holds OFFICIAL
picks. Every fixture that carried just a "model lean" lost its page the moment
it left the feed, which is exactly the 404 pattern Search Console reported
(49 dead match URLs and growing with every matchday).

This registry is append-only and committed with the data snapshot: once a
fixture has had a page, it stays here and the page keeps building forever.
Scores are filled in from the results archive when they become known, so a
resurrected page can show the final result rather than a permanent "awaiting".

Called from build.py after each fetch; safe to run standalone:
    python pipeline/match_registry.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_content import slugify  # the one slug implementation

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "match-registry.json"


def _load() -> dict:
    try:
        return json.loads(REG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"updated_at": None, "matches": {}}


def update() -> tuple[int, int]:
    """Upsert current feed fixtures and archived results. Returns (new, total)."""
    doc = _load()
    m = doc.setdefault("matches", {})
    new = 0

    # live feed: names, league, kickoff
    try:
        preds = json.loads((ROOT / "data" / "predictions.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        preds = {}
    for t in preds.get("tips", []):
        if not t.get("home") or not t.get("away"):
            continue
        slug = slugify(f"{t['home']}-vs-{t['away']}")
        row = m.get(slug)
        if row is None:
            new += 1
            m[slug] = {"h": t["home"], "a": t["away"], "league": t.get("league", ""),
                       "sk": t.get("sport_key", ""), "ko": t.get("kickoff"),
                       "hs": None, "as": None}
        else:
            # a repeat fixture re-uses the slug: keep the page pointed at the
            # newest meeting, same rule the live view applies
            row.update({"league": t.get("league", row.get("league", "")),
                        "sk": t.get("sport_key", row.get("sk", "")),
                        "ko": t.get("kickoff") or row.get("ko")})

    # results archive: fill scores, resurrect fixtures the feed dropped
    try:
        arch = json.loads((ROOT / "data" / "results-archive.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        arch = {}
    for g in (arch.get("games") or {}).values():
        if not g.get("h") or not g.get("a"):
            continue
        slug = slugify(f"{g['h']}-vs-{g['a']}")
        row = m.get(slug)
        if row is None:
            new += 1
            m[slug] = {"h": g["h"], "a": g["a"], "league": "", "sk": g.get("sk", ""),
                       "ko": g.get("d"), "hs": g.get("hs"), "as": g.get("as")}
        elif row.get("hs") is None and str(row.get("ko", ""))[:10] == str(g.get("d", ""))[:10]:
            # same fixture, same day -> that meeting's final score
            row["hs"], row["as"] = g.get("hs"), g.get("as")

    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    REG.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return new, len(m)


if __name__ == "__main__":
    n, total = update()
    print(f"✓ match-registry: +{n} new, {total} total")
