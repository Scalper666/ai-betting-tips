"""
Settle archived tips against real match results (The Odds API /scores).

    python results.py            # fetch real scores and grade pending tips
    python results.py --mock     # simulate outcomes (no API key needed, for testing)

Grading (flat 1-unit staking):
    won  -> +(odds - 1)
    lost -> -1
    void -> 0        (push on an exact total, or result unavailable)

Tips older than --expire days that never got a result are voided so they don't
sit "pending" forever and skew the numbers.
"""
from __future__ import annotations
import argparse, random, sys
from datetime import datetime, timezone, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

import history
from odds_api import OddsAPIClient, OddsAPIError


def profit_for(status: str, odds) -> float:
    if status == "won":
        return round(float(odds or 0) - 1, 3)
    if status == "lost":
        return -1.0
    return 0.0


def scores_map(event: dict) -> dict[str, float]:
    out = {}
    for s in event.get("scores") or []:
        try:
            out[s.get("name", "")] = float(s.get("score"))
        except (TypeError, ValueError):
            continue
    return out


def grade(tip: dict, event: dict) -> tuple[str, str] | None:
    """Return (status, score_string) or None if it can't be graded yet."""
    if not event.get("completed"):
        return None
    sm = scores_map(event)
    if len(sm) < 2:
        return None

    home, away = event.get("home_team", ""), event.get("away_team", "")
    hs, as_ = sm.get(home), sm.get(away)
    if hs is None or as_ is None:
        # fall back to whatever two entries exist
        vals = list(sm.values())
        hs, as_ = vals[0], vals[1]
    score_str = f"{int(hs)}-{int(as_)}"

    t = tip.get("type")
    if t == "h2h":
        winner = "Draw" if hs == as_ else (home if hs > as_ else away)
        return ("won" if tip.get("outcome") == winner else "lost"), score_str

    if t == "totals":
        point = tip.get("point")
        side = tip.get("side")
        if point is None or side not in ("Over", "Under"):
            return None
        total = hs + as_
        if total == float(point):
            return "void", score_str
        over_hit = total > float(point)
        won = over_hit if side == "Over" else not over_hit
        return ("won" if won else "lost"), score_str

    return None


def settle_real(h: dict, expire_days: int) -> tuple[int, int]:
    pend = history.pending(h)
    if not pend:
        return 0, 0
    sports = sorted({t.get("sport_key", "") for t in pend if t.get("sport_key")})
    print(f"--> {len(pend)} pending tip(s) across {len(sports)} sport(s)")

    client = OddsAPIClient()
    events: dict[str, dict] = {}
    for sk in sports:
        try:
            for ev in client.get_scores(sk, days_from=3):
                events[ev.get("id", "")] = ev
        except OddsAPIError as e:
            print(f"  ⚠ {sk}: {e}")
        except Exception as e:
            print(f"  ⚠ {sk}: {e}")
    print(f"  fetched {len(events)} finished/live event(s); quota left: {client.quota.get('remaining')}")

    accumulate_results(events)
    return apply_grades(h, pend, events, expire_days)


def accumulate_results(events: dict) -> None:
    """Bank every completed score the /scores calls already returned (the whole
    league round, not just our fixtures) into data/results-archive.json. Costs
    zero extra credits and slowly builds our own form/H2H dataset — the only
    free source that covers MLS."""
    import json
    path = history.ROOT / "data" / "results-archive.json"
    try:
        arch = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        arch = {}
    games = arch.setdefault("games", {})
    added = 0
    for eid, ev in events.items():
        if not eid or not ev.get("completed"):
            continue
        sm = scores_map(ev)
        home, away = ev.get("home_team", ""), ev.get("away_team", "")
        if not home or not away or home not in sm or away not in sm:
            continue
        if eid not in games:
            added += 1
        games[eid] = {
            "sk": ev.get("sport_key", ""),
            "d": str(ev.get("commence_time", ""))[:10],
            "h": home, "a": away,
            "hs": int(sm[home]), "as": int(sm[away]),
        }
    arch["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(arch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  results archive: +{added} new, {len(games)} total")


def apply_grades(h: dict, pend: list[dict], events: dict, expire_days: int) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    graded = expired = 0
    for tip in pend:
        ev = events.get(tip.get("event_id", ""))
        res = grade(tip, ev) if ev else None
        if res:
            status, score = res
            tip["status"] = status
            tip["score"] = score
            tip["profit"] = profit_for(status, tip.get("odds"))
            tip["settled_at"] = now.isoformat()
            graded += 1
            continue
        # expire stale tips so they don't stay pending forever
        ko = tip.get("kickoff")
        if ko:
            try:
                kt = datetime.fromisoformat(str(ko).replace("Z", "+00:00"))
                if now - kt > timedelta(days=expire_days):
                    tip["status"] = "void"
                    tip["profit"] = 0.0
                    tip["settled_at"] = now.isoformat()
                    tip["score"] = None
                    expired += 1
            except ValueError:
                pass
    history.save(h)
    return graded, expired


def settle_mock(h: dict) -> tuple[int, int]:
    """Simulate outcomes so the tracking pipeline can be tested without an API key."""
    pend = history.pending(h)
    now = datetime.now(timezone.utc)
    rnd = random.Random(1234)
    graded = 0
    for tip in pend:
        # Realistic simulation: hit-rate = implied probability of the price we took,
        # nudged by our edge. That yields an ROI in the same ballpark as the edge
        # (a few %), instead of the fantasy numbers a confidence-based coin-flip gives.
        odds = float(tip.get("odds") or 2.0)
        edge = float(tip.get("edge_pct") or 0) / 100.0
        p_win = max(0.02, min(0.95, (1.0 / odds) * (1.0 + edge)))
        won = rnd.random() < p_win
        status = "won" if won else "lost"
        tip["status"] = status
        tip["profit"] = profit_for(status, tip.get("odds"))
        tip["settled_at"] = now.isoformat()
        tip["score"] = "simulated"
        graded += 1
    history.save(h)
    return graded, 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="simulate results (no API call)")
    p.add_argument("--expire", type=int, default=5, help="void pending tips older than N days")
    # tolerate flags aimed at build.py (update.bat forwards the same arguments)
    args, _ = p.parse_known_args()

    h = history.load()
    if not h.get("tips"):
        sys.exit("✗ history.json is empty — run build.py first")

    if args.mock:
        print("--> Simulating results (no API call)")
        graded, expired = settle_mock(h)
    else:
        try:
            graded, expired = settle_real(h, args.expire)
        except OddsAPIError as e:
            sys.exit(f"✗ {e}")

    clv_n = history.apply_clv(h)
    if clv_n:
        history.save(h)
        print(f"  CLV annotated on {clv_n} settled tip(s)")

    tips = list(h.get("tips", {}).values())
    counts = {}
    for t in tips:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    print(f"✓ Settled {graded} tip(s)" + (f", voided {expired} stale" if expired else ""))
    print(f"  History: {counts}")


if __name__ == "__main__":
    main()
