"""
Fetch standings + finished results from football-data.org (free tier).

    python football_data.py          # writes data/football-data.json

Free tier: 10 requests/minute, ~12 competitions. We map The Odds API sport
keys to football-data competition codes and fetch, per covered league:
    * the current standings table
    * every finished match of the current season (form + head-to-head)
Leagues without a mapping (e.g. MLS) are skipped — the Astro side falls back
to our own results archive for those.

Needs FOOTBALL_DATA_TOKEN in pipeline/.env (or the CI secret). Exits 0 when
the token is missing so the pipeline never fails over an optional source.
"""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from odds_api import _build_session

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "football-data.json"
API = "https://api.football-data.org/v4"

# The Odds API sport_key -> football-data.org competition code
COMP = {
    "soccer_epl": "PL",
    "soccer_efl_champ": "ELC",
    "soccer_spain_la_liga": "PD",
    "soccer_italy_serie_a": "SA",
    "soccer_germany_bundesliga": "BL1",
    "soccer_france_ligue_one": "FL1",
    "soccer_netherlands_eredivisie": "DED",
    "soccer_portugal_primeira_liga": "PPL",
    "soccer_brazil_campeonato": "BSA",
    "soccer_uefa_champs_league": "CL",
}

PAUSE = 6.5  # seconds between calls: stays under the 10 req/min free limit


def main() -> int:
    token = os.getenv("FOOTBALL_DATA_TOKEN")
    if not token:
        print("⚠ FOOTBALL_DATA_TOKEN not set — skipping football-data fetch")
        return 0

    sports = [s.strip() for s in os.getenv("ODDS_API_SPORTS", "").split(",") if s.strip()]
    targets = [(sk, COMP[sk]) for sk in sports if sk in COMP]
    if not targets:
        print("⚠ no configured league maps to a football-data competition")
        return 0

    ses = _build_session()
    ses.headers["X-Auth-Token"] = token

    def get(path: str):
        r = ses.get(f"{API}{path}", timeout=25)
        if r.status_code == 429:
            time.sleep(30)
            r = ses.get(f"{API}{path}", timeout=25)
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()

    try:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}
    leagues = prev.get("leagues", {})

    for sk, code in targets:
        try:
            st = get(f"/competitions/{code}/standings")
            table = next((s for s in st.get("standings", []) if s.get("type") == "TOTAL"), {})
            rows = [{
                "pos": r.get("position"),
                "team": (r.get("team") or {}).get("shortName") or (r.get("team") or {}).get("name"),
                "p": r.get("playedGames"), "w": r.get("won"), "d": r.get("draw"), "l": r.get("lost"),
                "gd": r.get("goalDifference"), "pts": r.get("points"),
            } for r in table.get("table", [])]

            def matches_of(query: str) -> list[dict]:
                out = []
                for m in get(f"/competitions/{code}/matches?{query}").get("matches", []):
                    ft = (m.get("score") or {}).get("fullTime") or {}
                    if ft.get("home") is None or ft.get("away") is None:
                        continue
                    out.append({
                        "d": str(m.get("utcDate", ""))[:10],
                        "h": (m.get("homeTeam") or {}).get("shortName") or (m.get("homeTeam") or {}).get("name"),
                        "a": (m.get("awayTeam") or {}).get("shortName") or (m.get("awayTeam") or {}).get("name"),
                        "hs": ft["home"], "as": ft["away"],
                    })
                return out

            results = matches_of("status=FINISHED")
            # previous season too (free tier allows it): H2H depth, and early-season
            # form before the new campaign has any rounds played
            season = (st.get("season") or {}).get("startDate", "")[:4]
            if season.isdigit():
                try:
                    results = matches_of(f"status=FINISHED&season={int(season) - 1}") + results
                except Exception as e:
                    print(f"  ⚠ {code} season {int(season) - 1}: {str(e)[:60]}")
            leagues[sk] = {
                "code": code,
                "name": st.get("competition", {}).get("name", code),
                "season": (st.get("season") or {}).get("startDate", "")[:4],
                "standings": rows,
                "results": results,
            }
            print(f"  ✓ {code}: {len(rows)} table rows, {len(results)} finished matches")
        except Exception as e:
            print(f"  ⚠ {code}: {type(e).__name__} {str(e)[:90]} — keeping previous data")

    OUT.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "leagues": leagues,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ football-data.json: {len(leagues)} league(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
