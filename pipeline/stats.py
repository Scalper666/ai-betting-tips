"""
Compute REAL performance stats from settled tips in history.json.

    python stats.py     ->  data/stats.json

Everything here is derived from graded bets only — nothing is hand-written.
Flat 1-unit staking: ROI = profit / units staked. Voids don't count as stakes.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import history

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "stats.json"


def summarise(tips: list[dict]) -> dict:
    won = sum(1 for t in tips if t["status"] == "won")
    lost = sum(1 for t in tips if t["status"] == "lost")
    void = sum(1 for t in tips if t["status"] == "void")
    staked = won + lost                       # voids are returned, not staked
    profit = round(sum(float(t.get("profit") or 0) for t in tips), 2)
    return {
        "settled": won + lost + void,
        "won": won, "lost": lost, "void": void,
        "win_rate": round(won / staked * 100, 1) if staked else 0.0,
        "profit": profit,
        "roi": round(profit / staked * 100, 1) if staked else 0.0,
    }


def main() -> None:
    h = history.load()
    all_tips = list(h.get("tips", {}).values())
    if not all_tips:
        sys.exit("✗ history.json is empty — run build.py (and results.py) first")

    graded = [t for t in all_tips if t["status"] in ("won", "lost", "void")]
    pending = [t for t in all_tips if t["status"] == "pending"]

    overall = summarise(graded)
    overall["pending"] = len(pending)
    overall["tips_total"] = len(all_tips)

    # NOTE: this file used to compute a per-"tipster" table from invented names
    # (Aleksandar K. / Kate R. / Marco S.) that history.py hash-assigned to
    # bets. The site's whole editorial stance is "no fictional experts" — the
    # honest by-market tracks in ModelTracks.astro replaced the personas on
    # every page, so the fabricated grouping is gone from the data too.

    # per league
    by_league: dict[str, list[dict]] = {}
    for t in graded:
        by_league.setdefault(t.get("league") or "—", []).append(t)
    leagues = []
    for name, tips in by_league.items():
        s = summarise(tips)
        s["name"] = name
        leagues.append(s)
    leagues.sort(key=lambda x: -x["settled"])

    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "overall": overall,
        "leagues": leagues[:12],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ stats.json — {overall['settled']} settled, {overall['pending']} pending")
    print(f"  Overall: {overall['win_rate']}% win, ROI {overall['roi']:+}%, profit {overall['profit']:+}u")
    for lg in leagues[:6]:
        print(f"  {lg['name']:<24} {lg['settled']:>3} bets | {lg['win_rate']:>5}% | ROI {lg['roi']:+}%")


if __name__ == "__main__":
    main()
