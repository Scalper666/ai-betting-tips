"""Import historical results from football-data.co.uk into the goal model.

football-data.org's free tier stops at 12 competitions, which left the Poisson
model blind on two thirds of the odds feed — including its two biggest leagues,
MLS and the Argentine Primera. football-data.co.uk publishes free CSVs of final
scores for exactly those: single all-season files for the "extra" leagues and
per-season files for the European ones.

Output: data/results-import.json, one bucket per Odds-API sport_key, rows in
the same {d,h,a,hs,as} shape model.py already ingests. Team names are the
CSV's own — model.py resolves odds-feed names onto them with its fuzzy matcher,
the same way it does for football-data.org.

The files update on the site roughly weekly. The importer is meant to run in CI
before build.py; any download failure just leaves the previously committed JSON
in place, so a third-party outage can never break a build.

Usage:  python pipeline/import_fdcouk.py
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "results-import.json"

MAX_AGE_DAYS = 730          # HALF_LIFE_DAYS=240 makes anything older near-noise
BASE_EXTRA = "https://www.football-data.co.uk/new"
BASE_MAIN = "https://www.football-data.co.uk/mmz4281"


def _season_codes(today: date) -> list[str]:
    """Current + previous European season codes ('2627', '2526'). The new
    season's file appears within days of the first fixture; before that the
    404 is tolerated and last season alone carries the fit."""
    y = today.year if today.month >= 7 else today.year - 1
    code = lambda yy: f"{yy % 100:02d}{(yy + 1) % 100:02d}"
    return [code(y), code(y - 1)]


S = _season_codes(date.today())

# sport_key -> list of CSV URLs. Extra files hold every season in one file;
# main files are per-season. K League and UEFA qualifiers have no source here.
SOURCES: dict[str, list[str]] = {
    "soccer_argentina_primera_division": [f"{BASE_EXTRA}/ARG.csv"],
    "soccer_usa_mls":                    [f"{BASE_EXTRA}/USA.csv"],
    "soccer_mexico_ligamx":              [f"{BASE_EXTRA}/MEX.csv"],
    "soccer_japan_j_league":             [f"{BASE_EXTRA}/JPN.csv"],
    "soccer_sweden_allsvenskan":         [f"{BASE_EXTRA}/SWE.csv"],
    "soccer_norway_eliteserien":         [f"{BASE_EXTRA}/NOR.csv"],
    "soccer_poland_ekstraklasa":         [f"{BASE_EXTRA}/POL.csv"],
    "soccer_austria_bundesliga":         [f"{BASE_EXTRA}/AUT.csv"],
    # Switzerland: football-data.co.uk covers it in neither file family
    "soccer_denmark_superliga":          [f"{BASE_EXTRA}/DNK.csv"],
    "soccer_england_league1":            [f"{BASE_MAIN}/{s}/E2.csv" for s in S],
    "soccer_spain_segunda_division":     [f"{BASE_MAIN}/{s}/SP2.csv" for s in S],
    "soccer_germany_bundesliga2":        [f"{BASE_MAIN}/{s}/D2.csv" for s in S],
    "soccer_belgium_first_div":          [f"{BASE_MAIN}/{s}/B1.csv" for s in S],
    "soccer_turkey_super_league":        [f"{BASE_MAIN}/{s}/T1.csv" for s in S],
    "soccer_greece_super_league":        [f"{BASE_MAIN}/{s}/G1.csv" for s in S],
    "soccer_spl":                        [f"{BASE_MAIN}/{s}/SC0.csv" for s in S],
}


def fetch(url: str) -> str | None:
    """curl rather than urllib: the local machine sits behind a TLS-intercepting
    AV whose CA python's ssl rejects, while curl's bundle accepts it — and CI
    has curl anyway. -f turns 404 (season file not published yet) into rc!=0."""
    r = subprocess.run(
        ["curl", "-sSf", "--retry", "2", "--max-time", "60", url],
        capture_output=True,
    )
    if r.returncode != 0:
        return None
    # files are windows-1252 with stray bytes; latin-1 never throws
    return r.stdout.decode("utf-8", errors="replace") if b"\xc3" in r.stdout[:2000] \
        else r.stdout.decode("latin-1", errors="replace")


def _parse_date(s: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_rows(text: str) -> list[dict]:
    """Both schemas: extra files use Home/Away/HG/AG, main files use
    HomeTeam/AwayTeam/FTHG/FTAG. Rows without a final score are fixtures."""
    out = []
    cutoff = date.today().toordinal() - MAX_AGE_DAYS
    for row in csv.DictReader(io.StringIO(text)):
        h = (row.get("Home") or row.get("HomeTeam") or "").strip()
        a = (row.get("Away") or row.get("AwayTeam") or "").strip()
        hs = (row.get("HG") or row.get("FTHG") or "").strip()
        as_ = (row.get("AG") or row.get("FTAG") or "").strip()
        d = _parse_date(row.get("Date") or "")
        if not h or not a or not d or d.toordinal() < cutoff:
            continue
        try:
            out.append({"d": d.isoformat(), "h": h, "a": a,
                        "hs": int(float(hs)), "as": int(float(as_))})
        except ValueError:
            continue   # unplayed / abandoned
    return out


def main() -> int:
    leagues: dict[str, dict] = {}
    failures = []
    for sk, urls in SOURCES.items():
        rows, seen = [], set()
        got_any = False
        for url in urls:
            text = fetch(url)
            if text is None:
                failures.append(url.rsplit("/", 2)[-1])
                continue
            got_any = True
            for r in parse_rows(text):
                key = (r["d"], r["h"], r["a"])
                if key not in seen:
                    seen.add(key)
                    rows.append(r)
        if got_any and rows:
            rows.sort(key=lambda r: r["d"])
            leagues[sk] = {"results": rows}
            print(f"  {sk:<38} {len(rows):>5} матчей  ({rows[0]['d']} … {rows[-1]['d']})")
        else:
            print(f"  {sk:<38}  — не удалось")

    if not leagues:
        print("✗ ни одна лига не скачалась — файл не трогаю", file=sys.stderr)
        return 1

    OUT.write_text(json.dumps(
        {"updated_at": datetime.now(timezone.utc).isoformat(),
         "source": "football-data.co.uk",
         "leagues": leagues},
        ensure_ascii=False), encoding="utf-8")
    note = f" (пропущено: {', '.join(failures)})" if failures else ""
    print(f"✓ results-import.json: {len(leagues)} лиг, "
          f"{sum(len(v['results']) for v in leagues.values())} матчей{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
