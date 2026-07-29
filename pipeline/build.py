"""
Main build script — fetches odds, analyzes, writes data/predictions.json.

Usage:
    python build.py                  # fetch live data and write JSON
    python build.py --mock           # generate sample data without hitting the API
    python build.py --sports soccer_epl,basketball_nba   # restrict to specific sports
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Force UTF-8 on Windows consoles where stdout defaults to cp1251
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv is optional

from odds_api import OddsAPIClient, SPORT_KEYS, OddsAPIError
from analyze import summarize_event, stats
import history


ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "predictions.json"


def fetch_live(sport_filter: list[str] | None = None) -> dict:
    """Hit The Odds API for every configured sport and build the prediction set."""
    client = OddsAPIClient(region=os.getenv("ODDS_API_REGION", "eu"))
    keys = list(SPORT_KEYS.keys())
    if sport_filter:
        keys = [k for k in keys if k in sport_filter]
    print(f"--> Fetching odds for {len(keys)} sports (region={client.region})...")

    raw = client.fetch_many(keys, markets="h2h,totals")
    print(f"  quota: used={client.quota['used']} remaining={client.quota['remaining']}")

    from model import GoalModel
    gm = GoalModel()
    print(f"  goal model: {len(gm.leagues)} league(s) fitted")

    tips = []
    official_n = 0
    for sport_key, events in raw.items():
        meta = SPORT_KEYS[sport_key]
        for ev in events:
            probs = gm.probs(sport_key, ev.get("home_team", ""), ev.get("away_team", ""))
            tip = summarize_event(ev, meta, model_probs=probs)
            if tip:
                tips.append(tip)
                official_n += 1 if tip["recommendation"].get("official") else 0
    print(f"  official picks: {official_n} of {len(tips)} fixtures (rest are page leans)")

    # Sort: live/closest first by confidence desc, then by kickoff
    tips.sort(key=lambda t: (
        t.get("kickoff") or "9999",
        -t["recommendation"]["confidence"],
    ))

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "the-odds-api.com",
        "quota_remaining": client.quota["remaining"],
        "stats": stats(tips),
        "tips": tips,
    }


def fetch_mock() -> dict:
    """Generate plausible demo data without hitting the API."""
    now = datetime.now(timezone.utc)
    sample_matches = [
        ("soccer_uefa_champs_league", "⚽", "Champions League", "UCL",
         [("Real Madrid", "Manchester City"), ("Bayern Munich", "PSG"),
          ("Arsenal", "Liverpool"), ("Barcelona", "Atletico Madrid")]),
        ("soccer_epl", "⚽", "Premier League", "EPL",
         [("Chelsea", "Tottenham"), ("Man United", "Newcastle"), ("Aston Villa", "West Ham")]),
        ("soccer_italy_serie_a", "⚽", "Serie A", "SA",
         [("Inter", "Juventus"), ("Napoli", "Milan"), ("Roma", "Lazio")]),
        ("basketball_nba", "🏀", "NBA", "NBA",
         [("LA Lakers", "Boston Celtics"), ("Denver", "Phoenix"),
          ("Milwaukee", "Miami"), ("Warriors", "Mavericks")]),
        ("tennis_atp_french_open", "🎾", "Roland Garros (ATP)", "ATP",
         [("C. Alcaraz", "J. Sinner"), ("D. Medvedev", "A. Zverev"),
          ("N. Djokovic", "H. Rune")]),
        ("icehockey_nhl", "🏒", "NHL", "NHL",
         [("Edmonton", "Vegas"), ("Boston", "NY Rangers")]),
        ("mma_mixed_martial_arts", "🥊", "UFC / MMA", "UFC",
         [("Adesanya", "Pereira")]),
    ]

    tips = []
    h_off = 1
    random.seed(42)
    for sport_key, icon, league, short, matches in sample_matches:
        for home, away in matches:
            kickoff = (now + timedelta(hours=h_off)).isoformat()
            h_off += random.randint(2, 8)
            best_h2h = {
                home: {"price": round(random.uniform(1.50, 3.50), 2),
                       "bookmaker": random.choice(["1xBet", "Pinnacle", "bet365"])},
                away: {"price": round(random.uniform(1.50, 3.50), 2),
                       "bookmaker": random.choice(["Fonbet", "Marathon", "Stake"])},
            }
            if "soccer" in sport_key:
                best_h2h["Draw"] = {"price": round(random.uniform(2.80, 4.00), 2),
                                    "bookmaker": "1xBet"}
            edge = round(random.uniform(2.0, 11.0), 1)
            conf = random.randint(58, 90)
            pred_pool = ["Over 2.5 + BTTS", "Home -1.5", "Both teams to score",
                         "Over 22.5 games", "Home total over 1.5", "Away win + Over 2.5"]
            tips.append({
                "id": f"mock_{len(tips)}",
                "sport_key": sport_key,
                "sport_icon": icon,
                "league": league,
                "league_short": short,
                "kickoff": kickoff,
                "home": home,
                "away": away,
                "best_h2h": best_h2h,
                "recommendation": {
                    "text": random.choice(pred_pool),
                    "price": round(random.uniform(1.65, 3.20), 2),
                    "bookmaker": random.choice(["1xBet", "Pinnacle", "bet365", "Fonbet"]),
                    "confidence": conf,
                    "edge_pct": edge,
                    "type": "h2h" if random.random() > 0.3 else "totals",
                },
                "value_picks": [],
            })

    return {
        "updated_at": now.isoformat(),
        "source": "mock-data",
        "quota_remaining": None,
        "stats": stats(tips),
        "tips": tips,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true",
                   help="Generate sample data without hitting the API")
    p.add_argument("--sports", type=str, default="",
                   help="Comma-separated sport keys to fetch (default: all)")
    p.add_argument("--out", type=Path, default=OUT_PATH,
                   help="Output JSON path (default: data/predictions.json)")
    args = p.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    if args.mock:
        print("--> Using mock data (no API call)")
        result = fetch_mock()
    else:
        # --sports wins; otherwise fall back to ODDS_API_SPORTS in .env; else all sports
        raw = args.sports or os.getenv("ODDS_API_SPORTS", "")
        sport_filter = [s.strip() for s in raw.split(",") if s.strip()] or None
        try:
            result = fetch_live(sport_filter)
        except OddsAPIError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(2)

    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Wrote {len(result['tips'])} tips to {args.out}")
    print(f"  Stats: {result['stats']}")

    # Archive every published tip so results.py can grade it once the match ends,
    # and snapshot prices so the screener can show real line movement.
    try:
        new, total = history.add_from_predictions(result)
        series = history.record_odds(result)
        print(f"  Archived: {new} new, {total} total in history.json · {series} odds series")
    except Exception as e:  # never let archiving break the build
        print(f"  ⚠ history archive failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
