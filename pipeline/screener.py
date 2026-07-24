"""
Build data/screener.json — one row per bet with an AI score, for the screener page.
Reads data/predictions.json (produced by build.py). Run after build.py.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import history

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "predictions.json"
OUT = ROOT / "data" / "screener.json"

SPORT_LABEL = {
    "soccer": "Football", "basketball": "Basketball", "tennis": "Tennis",
    "icehockey": "Hockey", "mma": "MMA", "americanfootball": "NFL", "baseball": "Baseball",
}


def sport_of(sport_key: str) -> str:
    base = str(sport_key).split("_")[0]
    return SPORT_LABEL.get(base, base.title() or "Other")


def classify(text: str, typ: str) -> str:
    t = text.lower()
    if "btts" in t or "both teams" in t:
        return "BTTS"
    if "over" in t or "under" in t or "total" in t or typ == "totals":
        return "Totals"
    if "-1.5" in t or "+0.5" in t or "-2.5" in t or "handicap" in t or "+1.5" in t:
        return "Handicap"
    if "win" in t or "draw" in t or typ == "h2h":
        return "Match result"
    return "Other"


def outcome_text(outcome: str) -> str:
    """Same wording the recommendation uses, so a Draw doesn't read 'Draw to win'."""
    return "Draw (X)" if outcome == "Draw" else f"{outcome} to win"


def ai_score(conf: int, edge: float, odds: float) -> int:
    """Value-first screener score (1..99).

    This is a VALUE screener, so a genuine positive edge must rank above a
    confident-but-negative-EV favourite. Positive-edge bets are scored by Kelly
    fraction  ev / (odds - 1)  (which demotes longshots); everything with no edge
    sits below them, ordered only by win probability as a tiebreak.
    """
    ev = float(edge) / 100.0
    if ev > 0:
        b = max(float(odds) - 1.0, 0.01)
        kelly = ev / b
        return max(45, min(99, round(50 + kelly * 320 + conf * 0.12)))
    return max(1, min(44, round(conf * 0.40)))


def steam(tip_id: str, market: str, odds_hist: dict) -> str:
    """Real line movement from odds snapshots: 'up' = price shortened (money coming in)."""
    return history.price_move(history.tip_key(tip_id, market), odds_hist)


def row(tip: dict, text: str, price: float, conf: int, edge: float, typ: str, bookmaker: str,
        odds_hist: dict, suffix: str = "") -> dict:
    return {
        "id": f"{tip.get('id','')}{suffix}",
        "sport": sport_of(tip.get("sport_key", "")),
        "icon": tip.get("sport_icon", "🏆"),
        "league": tip.get("league", ""),
        "home": tip.get("home", ""),
        "away": tip.get("away", ""),
        "kickoff": tip.get("kickoff"),
        "market": text,
        "type": classify(text, typ),
        "odds": round(float(price or 0), 2),
        "edge": round(float(edge or 0), 1),
        "confidence": int(conf or 0),
        "score": ai_score(int(conf or 0), float(edge or 0), float(price or 0)),
        "steam": steam(tip.get("id", ""), text, odds_hist),
        "bookmaker": bookmaker or "—",
    }


def main() -> None:
    if not SRC.exists():
        sys.exit(f"✗ {SRC} not found — run build.py first")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    odds_hist = history.load_odds()   # loaded once; used for real line movement
    rows = []
    seen = set()   # dedupe: the recommendation is often also its top value pick

    def add(r: dict) -> None:
        key = (r["home"], r["away"], r["market"], r["odds"])
        if key in seen:
            return
        seen.add(key)
        rows.append(r)

    for tip in data.get("tips", []):
        rec = tip.get("recommendation") or {}
        add(row(tip, rec.get("text", ""), rec.get("price", 0),
                rec.get("confidence", 60), rec.get("edge_pct", 0),
                rec.get("type", ""), rec.get("bookmaker", "—"), odds_hist))
        # extra rows from value picks (h2h outcomes with edge) if present
        for i, vp in enumerate(tip.get("value_picks", [])[:2]):
            add(row(tip, outcome_text(vp.get("outcome", "")), vp.get("best_price", 0),
                    vp.get("confidence", 60), vp.get("edge_pct", 0),
                    "h2h", vp.get("bookmaker", "—"), odds_hist, suffix=f"_v{i}"))

    rows.sort(key=lambda r: -r["score"])
    out = {
        "updated_at": data.get("updated_at"),
        "source": data.get("source"),
        "count": len(rows),
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ screener.json: {len(rows)} rows (from {len(data.get('tips', []))} matches)")


if __name__ == "__main__":
    main()
