"""
Append-only archive of every tip we publish, plus its settlement state.

Without this, predictions.json is overwritten on each run and there is nothing
to grade against results — so win rate / ROI could only ever be fake numbers.

data/history.json:
{
  "updated_at": "...",
  "tips": {
     "<event_id>|<market>": {
        ... tip fields ..., "status": "pending|won|lost|void",
        "profit": null|float (units, flat 1u staking), "settled_at": ..., "score": "2-1"
     }
  }
}
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.json"

# Tips are attributed to a tipster deterministically so a given match/market
# always belongs to the same person (stats stay consistent across runs).
TIPSTERS = ["Aleksandar K.", "Kate R.", "Marco S."]


def tip_key(event_id: str, market: str) -> str:
    return f"{event_id}|{market}"


def tipster_for(key: str) -> str:
    return TIPSTERS[sum(map(ord, key)) % len(TIPSTERS)]


def load() -> dict:
    if HISTORY.exists():
        try:
            return json.loads(HISTORY.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("⚠ history.json unreadable — starting a fresh archive")
    return {"updated_at": None, "tips": {}}


def save(h: dict) -> None:
    h["updated_at"] = datetime.now(timezone.utc).isoformat()
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(h, ensure_ascii=False, indent=2), encoding="utf-8")


def add_from_predictions(predictions: dict) -> tuple[int, int]:
    """Archive any tip we haven't seen before. Returns (new, total)."""
    h = load()
    tips = h.setdefault("tips", {})
    now = datetime.now(timezone.utc).isoformat()
    new = 0

    for t in predictions.get("tips", []):
        rec = t.get("recommendation") or {}
        market = rec.get("text", "")
        eid = t.get("id") or f"{t.get('home','')}-{t.get('away','')}-{t.get('kickoff','')}"
        key = tip_key(eid, market)
        if key in tips:
            continue  # already archived (and possibly already settled)
        tips[key] = {
            "key": key,
            "event_id": eid,
            "sport_key": t.get("sport_key", ""),
            "league": t.get("league", ""),
            "home": t.get("home", ""),
            "away": t.get("away", ""),
            "kickoff": t.get("kickoff"),
            "market": market,
            "type": rec.get("type", ""),
            "side": rec.get("side"),          # Over / Under (totals)
            "point": rec.get("point"),        # e.g. 2.5
            "outcome": rec.get("outcome"),    # team name or "Draw" (h2h)
            "odds": rec.get("price"),
            "confidence": rec.get("confidence"),
            "edge_pct": rec.get("edge_pct"),
            "bookmaker": rec.get("bookmaker"),
            "tipster": tipster_for(key),
            "published_at": now,
            "status": "pending",
            "profit": None,
            "settled_at": None,
            "score": None,
        }
        new += 1

    save(h)
    return new, len(tips)


# ---------------------------------------------------------------- odds history
# Snapshots of the price we quoted for each tip, so the screener can show a real
# line-movement ("steam") signal instead of guessing from the edge.
ODDS_HISTORY = ROOT / "data" / "odds_history.json"
MAX_POINTS = 12


def load_odds() -> dict:
    if ODDS_HISTORY.exists():
        try:
            return json.loads(ODDS_HISTORY.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def record_odds(predictions: dict) -> int:
    """Append the current price for every tip. Returns number of series touched."""
    data = load_odds()
    ts = datetime.now(timezone.utc).isoformat()
    for t in predictions.get("tips", []):
        rec = t.get("recommendation") or {}
        price = rec.get("price")
        if price is None:
            continue
        eid = t.get("id") or f"{t.get('home','')}-{t.get('away','')}-{t.get('kickoff','')}"
        key = tip_key(eid, rec.get("text", ""))
        series = data.setdefault(key, [])
        if series and series[-1].get("price") == price:
            continue  # unchanged since last run — don't pad the series
        series.append({"ts": ts, "price": price})
        del series[:-MAX_POINTS]
    ODDS_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    ODDS_HISTORY.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(data)


def price_move(key: str, data: dict | None = None) -> str:
    """'up' = price shortened (money coming in), 'down' = drifted, 'flat' = no data/no change."""
    data = load_odds() if data is None else data
    series = data.get(key) or []
    if len(series) < 2:
        return "flat"
    prev, last = series[-2].get("price"), series[-1].get("price")
    try:
        prev, last = float(prev), float(last)
    except (TypeError, ValueError):
        return "flat"
    if last < prev:
        return "up"
    if last > prev:
        return "down"
    return "flat"


def pending(h: dict | None = None) -> list[dict]:
    h = h or load()
    return [t for t in h.get("tips", {}).values() if t.get("status") == "pending"]


def settled(h: dict | None = None) -> list[dict]:
    h = h or load()
    return [t for t in h.get("tips", {}).values() if t.get("status") in ("won", "lost", "void")]


if __name__ == "__main__":
    h = load()
    tips = list(h.get("tips", {}).values())
    by_status = {}
    for t in tips:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
    print(f"history.json — {len(tips)} tips: {by_status or '(empty)'}")
