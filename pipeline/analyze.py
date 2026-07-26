"""
Odds analysis — best lines across bookmakers, fair odds (margin-removed),
value detection by edge over fair probability.
"""
from __future__ import annotations
import statistics
from typing import Iterable


def implied_prob(decimal_odds: float) -> float:
    """Decimal odds → implied probability (with bookie margin baked in)."""
    return 1.0 / decimal_odds if decimal_odds > 0 else 0.0


def best_h2h_odds(event: dict) -> dict[str, dict]:
    """
    For a single event, find the highest decimal odds per outcome across all bookmakers.

    Returns { outcome_name -> {"price": float, "bookmaker": str} }
    Outcome names match what the API returns (home team name, away team name, "Draw").
    """
    best: dict[str, dict] = {}
    for bm in event.get("bookmakers", []):
        for market in bm.get("markets", []):
            if market.get("key") != "h2h":
                continue
            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                price = float(outcome["price"])
                if name not in best or price > best[name]["price"]:
                    best[name] = {"price": price, "bookmaker": bm.get("title", "—")}
    return best


def best_totals(event: dict) -> dict[str, dict]:
    """
    Best Over/Under per (point, side).

    Returns { "Over_2.5" -> {"price", "bookmaker", "point", "side"}, ... }
    """
    best: dict[str, dict] = {}
    for bm in event.get("bookmakers", []):
        for market in bm.get("markets", []):
            if market.get("key") != "totals":
                continue
            for o in market.get("outcomes", []):
                point = o.get("point")
                side = o.get("name")  # "Over" or "Under"
                if point is None or side is None:
                    continue
                key = f"{side}_{point}"
                price = float(o["price"])
                if key not in best or price > best[key]["price"]:
                    best[key] = {
                        "price": price,
                        "bookmaker": bm.get("title", "—"),
                        "point": point,
                        "side": side,
                    }
    return best


def fair_h2h_probs(event: dict) -> dict[str, float] | None:
    """
    Compute fair probability per outcome by averaging implied probabilities
    across all bookmakers, then normalizing to 1.0 (removing overround).
    Works well when ≥5 bookmakers are quoting.
    """
    bucket: dict[str, list[float]] = {}
    for bm in event.get("bookmakers", []):
        for market in bm.get("markets", []):
            if market.get("key") != "h2h":
                continue
            # Collect probs only if this bm has all outcomes; skip incomplete bms
            outcomes = market.get("outcomes", [])
            if not outcomes:
                continue
            for o in outcomes:
                bucket.setdefault(o["name"], []).append(implied_prob(float(o["price"])))
    if not bucket:
        return None
    avg = {k: statistics.mean(v) for k, v in bucket.items() if v}
    total = sum(avg.values())
    if total <= 0:
        return None
    return {k: v / total for k, v in avg.items()}


def find_value_picks(
    event: dict,
    edge_threshold: float = 0.03,
    max_odds: float = 6.0,
    min_prob: float = 0.06,
    fair: dict[str, float] | None = None,
) -> list[dict]:
    """
    For each h2h outcome, compare the best market price vs the consensus fair price.

    Two guards keep this honest instead of surfacing longshot noise:
      * max_odds — ignore big underdogs, where one generous book creates a huge
        fake edge% that is really just an outlier/soft price, not value.
      * ranking by Kelly fraction  ev / (price - 1)  instead of raw edge% —
        Kelly weights value by how likely the bet is to land, so a small edge on
        a 1.8 favourite outranks a large edge on a 6.0 shot (as it should).

    Returns picks sorted best-first (highest Kelly fraction).
    """
    fair = fair or fair_h2h_probs(event)
    if not fair:
        return []
    best = best_h2h_odds(event)
    picks = []
    for name, info in best.items():
        p_fair = fair.get(name)
        price = float(info["price"])
        if p_fair is None or p_fair < min_prob:
            continue
        if price <= 1.0 or price > max_odds:   # skip longshot outliers
            continue
        ev = price * p_fair - 1.0               # expected profit per 1u stake
        if ev < edge_threshold:
            continue
        kelly = ev / (price - 1.0)              # optimal stake fraction; demotes longshots
        picks.append({
            "outcome": name,
            "best_price": round(price, 2),
            "bookmaker": info["bookmaker"],
            "fair_prob": round(p_fair, 4),
            "implied_prob": round(implied_prob(price), 4),
            "edge_pct": round(ev * 100, 2),      # expected ROI %
            "kelly": round(kelly, 4),
            "confidence": min(98, int(round(p_fair * 100))),
        })
    picks.sort(key=lambda x: -x["kelly"])
    return picks


def pick_recommended_total(event: dict) -> dict | None:
    """
    From totals markets, pick the over/under line closest to the median line
    and recommend the side with better-than-fair odds.
    Simple heuristic for when h2h has no clear value pick.
    """
    totals = best_totals(event)
    if not totals:
        return None

    # Group by point
    by_point: dict[float, dict] = {}
    for k, info in totals.items():
        p = info["point"]
        by_point.setdefault(p, {})[info["side"]] = info

    # Pick the most quoted line (closest to bookies' consensus)
    if not by_point:
        return None
    target_point = sorted(by_point.keys(), key=lambda x: -len(by_point[x]))[0]
    sides = by_point[target_point]

    # Compare implied probs: side with lower implied has better value at that line
    over = sides.get("Over")
    under = sides.get("Under")
    if not over or not under:
        return None

    # Fair probability (assuming symmetric overround)
    over_imp = implied_prob(over["price"])
    under_imp = implied_prob(under["price"])
    total = over_imp + under_imp
    fair_over = over_imp / total if total > 0 else 0
    fair_under = 1 - fair_over

    # Recommend whichever side has lower margin (slightly mispriced)
    ev_over = over["price"] * fair_over - 1
    ev_under = under["price"] * fair_under - 1
    if ev_over >= ev_under:
        return {
            "market": f"Over {target_point} goals",
            "best_price": round(over["price"], 2),
            "bookmaker": over["bookmaker"],
            "confidence": int(round(fair_over * 100)),
            "edge_pct": round(ev_over * 100, 2),
            "side": "Over", "point": target_point,
        }
    return {
        "market": f"Under {target_point} goals",
        "best_price": round(under["price"], 2),
        "bookmaker": under["bookmaker"],
        "confidence": int(round(fair_under * 100)),
        "edge_pct": round(ev_under * 100, 2),
        "side": "Under", "point": target_point,
    }


def summarize_event(event: dict, meta: dict) -> dict | None:
    """
    Convert a raw odds-event into a 'tip card' object for the website.
    Returns None when the event has insufficient odds data.
    """
    if not event.get("bookmakers"):
        return None

    home = event.get("home_team", "")
    away = event.get("away_team", "")
    if not home or not away:
        return None

    best_h2h = best_h2h_odds(event)
    if not best_h2h:
        return None

    fair = fair_h2h_probs(event)
    value_picks = find_value_picks(event, fair=fair)
    totals_pick = pick_recommended_total(event)

    # Recommendation priority: (1) best value h2h by Kelly, (2) totals value,
    # (3) plain favourite — so every match still gets a sensible tip on the
    # most likely outcome rather than a longshot.
    # The MAIN tip is stricter than the screener list: it becomes a real
    # archived bet, so no lottery tickets — moderate odds and a real chance
    # of landing, or we fall through to totals / the favourite.
    REC_MAX_ODDS = 4.0
    REC_MIN_PROB = 0.35
    rec_candidates = [p for p in value_picks
                      if p["best_price"] <= REC_MAX_ODDS and p["fair_prob"] >= REC_MIN_PROB]
    if rec_candidates:
        top = rec_candidates[0]
        recommendation = {
            "text": _h2h_text(top["outcome"], home, away),
            "price": top["best_price"],
            "bookmaker": top["bookmaker"],
            "confidence": top["confidence"],
            "edge_pct": top["edge_pct"],
            "type": "h2h",
            # structured fields so results.py can settle the bet automatically
            "outcome": top["outcome"],
        }
    elif totals_pick:
        recommendation = {
            "text": totals_pick["market"],
            "price": totals_pick["best_price"],
            "bookmaker": totals_pick["bookmaker"],
            "confidence": totals_pick["confidence"],
            "edge_pct": totals_pick["edge_pct"],
            "type": "totals",
            "side": totals_pick["side"],
            "point": totals_pick["point"],
        }
    elif fair:
        # Favourite fallback: highest fair-probability outcome at its best price.
        fav = max(fair, key=fair.get)
        info = best_h2h.get(fav)
        if not info:
            return None
        p = fair[fav]
        price = float(info["price"])
        recommendation = {
            "text": _h2h_text(fav, home, away),
            "price": round(price, 2),
            "bookmaker": info["bookmaker"],
            "confidence": min(98, int(round(p * 100))),
            "edge_pct": round((price * p - 1.0) * 100, 2),
            "type": "h2h",
            "outcome": fav,
        }
    else:
        return None

    return {
        "id": event.get("id"),
        "sport_key": event.get("sport_key"),
        "sport_icon": meta.get("icon", "🏆"),
        "league": meta.get("label", event.get("sport_title", "—")),
        "league_short": meta.get("short", ""),
        "kickoff": event.get("commence_time"),
        "home": home,
        "away": away,
        "best_h2h": {
            name: {"price": round(info["price"], 2), "bookmaker": info["bookmaker"]}
            for name, info in best_h2h.items()
        },
        "recommendation": recommendation,
        "value_picks": value_picks[:3],  # top-3 value bets
    }


def _h2h_text(outcome: str, home: str, away: str) -> str:
    """Convert API outcome name into a short Russian prediction text."""
    if outcome == "Draw":
        return "Draw (X)"
    if outcome == home:
        return f"{home} to win"
    if outcome == away:
        return f"{away} to win"
    return outcome


def stats(tips: Iterable[dict]) -> dict:
    """Aggregate stats over a list of tips for the dashboard summary."""
    tips = list(tips)
    by_sport: dict[str, int] = {}
    for t in tips:
        by_sport[t["sport_icon"]] = by_sport.get(t["sport_icon"], 0) + 1
    high_conf = sum(1 for t in tips if t["recommendation"]["confidence"] >= 75)
    avg_edge = statistics.mean([t["recommendation"]["edge_pct"] for t in tips]) if tips else 0
    return {
        "total": len(tips),
        "by_sport": by_sport,
        "high_confidence": high_conf,
        "avg_edge_pct": round(avg_edge, 2),
    }
