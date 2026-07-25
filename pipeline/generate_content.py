"""Generate unique page copy via the Claude API -> data/content.json.

One entry per SEO page (match previews, league guides, bet-type guides,
bookmaker/casino verdicts, country intros). The Astro site renders these
sections when present and falls back to its templated copy when absent,
so this step is always safe to skip.

Honesty rules baked into every prompt: no promised winnings, no invented
facts (no injuries/news/lineups — the model only reasons from the odds
data we pass in), responsible-gambling tone.

Caching: an entry is regenerated only when its input hash changes
(match odds moving does NOT re-trigger a match preview; the fixture
itself defines the hash). Run after build.py, before sync_astro.py.

Usage:
    python generate_content.py                # generate whatever is missing
    python generate_content.py --dry-run      # show the plan, no API calls
    python generate_content.py --limit 3      # cap API calls (testing)
    python generate_content.py --only match   # one kind: match|league|tips|bookmaker|casino|country
    python generate_content.py --force        # ignore cache, regenerate all
Requires ANTHROPIC_API_KEY in pipeline/.env (or the environment).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent          # D:\CLOUDE\sharptips
# When the pipeline lives inside the Astro repo, ROOT is the repo itself;
# fall back to the legacy sibling layout for the old standalone checkout.
ASTRO = ROOT if (ROOT / "src" / "data").is_dir() else ROOT.parent / "sharptips-astro"
OUT = ROOT / "data" / "content.json"

MODEL = os.getenv("CONTENT_MODEL", "claude-opus-4-8")
MAX_TOKENS = 3000
WORKERS = 4

BET_TYPES = [
    ("accumulator", "Accumulator Tips"),
    ("btts", "Both Teams To Score (BTTS) Tips"),
    ("over-under", "Over/Under Goals Tips"),
    ("correct-score", "Correct Score Tips"),
    ("double-chance", "Double Chance Tips"),
    ("draw", "Draw Tips"),
]


def slugify(s: str) -> str:
    """Mirror of src/lib/utils.js slugify — keys must match Astro page slugs."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()))


# ---------------------------------------------------------------- schemas
def _obj(props: dict, req: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}


S_TEXT = {"type": "string"}
S_FAQ = {"type": "array", "items": _obj({"q": S_TEXT, "a": S_TEXT}, ["q", "a"])}
SCHEMAS = {
    "match": _obj({
        "intro": S_TEXT,                      # ~120-170 words market-based preview
        "key_factors": {"type": "array", "items": S_TEXT},   # 3-4 bullets
        "verdict": S_TEXT,                    # ~40-60 words wrap-up
        "faq": S_FAQ,                         # 3 search-style Q&As (FAQPage schema)
    }, ["intro", "key_factors", "verdict", "faq"]),
    "league": _obj({
        "intro": S_TEXT,                      # what makes betting on this league distinct
        "betting_guide": S_TEXT,              # practical how-to paragraph
        "faq": S_FAQ,
    }, ["intro", "betting_guide", "faq"]),
    "tips": _obj({
        "intro": S_TEXT,
        "how_it_works": S_TEXT,
        "strategy": S_TEXT,
        "faq": S_FAQ,
    }, ["intro", "how_it_works", "strategy", "faq"]),
    "bookmaker": _obj({
        "verdict": S_TEXT,                    # editorial verdict ~130-170 words
        "who_for": S_TEXT,                    # who this brand suits ~50-70 words
        "faq": S_FAQ,
    }, ["verdict", "who_for", "faq"]),
    "casino": _obj({
        "verdict": S_TEXT,
        "who_for": S_TEXT,
        "faq": S_FAQ,
    }, ["verdict", "who_for", "faq"]),
    "country": _obj({
        "intro": S_TEXT,                      # betting landscape ~110-150 words
        "faq": S_FAQ,
    }, ["intro", "faq"]),
    "page": _obj({                            # evergreen intro + FAQ for thin index pages
        "intro": S_TEXT,
        "faq": S_FAQ,
    }, ["intro", "faq"]),
    "team": _obj({                            # evergreen intro + FAQ for team hub pages
        "intro": S_TEXT,
        "faq": S_FAQ,
    }, ["intro", "faq"]),
    "combo": _obj({                           # bet-type x league matrix pages
        "intro": S_TEXT,
        "faq": S_FAQ,
    }, ["intro", "faq"]),
    "recap": _obj({                           # weekly results recap pages
        "intro": S_TEXT,
        "faq": S_FAQ,
    }, ["intro", "faq"]),
}

FAQ_RULES = """
- faq: exactly 3 concise Q&A pairs phrased the way real bettors search (natural questions).
  Answers 2-3 sentences, honest, self-contained, no cross-references to "above". Evergreen wording:
  never cite counts, dates or prices that change daily."""

# Thin index pages that get an evergreen AI intro + FAQ (key -> what the page is)
PAGES = [
    ("predictions", "the football predictions hub listing every current tip with odds and confidence"),
    ("screener", "the AI value screener — a sortable table of every bet scored by value edge and win probability"),
    ("bonuses", "the betting bonuses comparison page listing welcome offers with their real wagering terms"),
    ("betting-apps", "the betting apps roundup rating bookmakers' mobile apps"),
    ("tipsters", "the model performance page: honest by-market track records (match result, totals, draw value) of our own prediction model — no tipster personas — with a fully settled public log"),
]

SYSTEM = """You are the senior editor of AI Betting Tips (ai-betting-tips.com), an English-language
sports-betting information site. You write clear, useful, search-friendly copy.

Hard rules — never break these:
- Never promise, guarantee or imply certain winnings. Betting involves risk; outcomes are uncertain.
- Ground every claim ONLY in the data given in the prompt (odds, implied probabilities, ratings,
  bonus terms). NEVER invent facts: no injuries, form streaks, transfers, news, head-to-head history,
  stadium details or lineups — you do not have that information.
- When discussing chances, reason from the odds/implied probability ("the market prices X at about
  N%"), not from claimed inside knowledge.
- Neutral-to-positive professional tone; no hype words like "guaranteed", "sure bet", "can't lose",
  "easy money". No emoji.
- Audience is 18+ bettors; write responsibly (moderation, bankroll care where natural — one light
  touch, not a lecture).
- Plain text only in every field: no markdown, no headings, no HTML.
- Write naturally varied prose. Avoid boilerplate openers like "When it comes to" or "In the world of".
"""


# ---------------------------------------------------------------- prompt builders
def p_match(t: dict) -> str:
    rec = t.get("recommendation") or {}
    h2h = t.get("best_h2h") or {}
    odds_lines = "\n".join(f"  {name}: {i['price']} ({i['bookmaker']})" for name, i in h2h.items())
    picks = "\n".join(
        f"  {v.get('outcome')}: best price {v.get('best_price')} , fair prob {round((v.get('fair_prob') or 0)*100)}%, edge {v.get('edge_pct')}%"
        for v in (t.get("value_picks") or [])[:3]
    ) or "  (none above threshold)"
    return f"""Write a pre-match betting preview for this fixture, based strictly on the market data below.

Fixture: {t.get('home')} vs {t.get('away')}
Competition: {t.get('league')}
Kick-off (UTC): {t.get('kickoff')}
Best available match-result odds:
{odds_lines}
Our model's recommended bet: {rec.get('text')} @ {rec.get('price')} ({rec.get('bookmaker')}), market-implied confidence {rec.get('confidence')}%, value edge {rec.get('edge_pct')}%
Value picks vs market consensus:
{picks}

Sections:
- intro: 120-170 words. Frame the fixture through the odds: who the market makes favourite and how strongly, what the prices imply in probability terms, and where our recommended bet fits. Mention both team names and the competition naturally (good for search).
- key_factors: 3-4 short bullet sentences, each derived from the data above (price gaps, implied probabilities, value edges, draw pricing). No invented facts.
- verdict: 40-60 words summarising the recommended bet and its risk level honestly.
- faq: exactly 3 Q&As bettors would search about betting on this exact fixture (e.g. who is
  favourite, what the draw is priced at, is there value) — answered ONLY from the data above.
  Answers 1-3 sentences, honest. Never invent team news."""


def p_league(name: str, short: str, teams: list[str], n: int) -> str:
    return f"""Write evergreen copy for the "{name}" football predictions page of our site.

Data: we currently list {n} upcoming {name} fixtures, featuring teams such as {', '.join(teams[:6])}.

Sections:
- intro: 120-160 words on betting on {name}: what kind of competition it is at a general level and what our predictions page offers (daily tips with odds comparison, value detection, honest settled results). Mention "{name} predictions" and "{name} betting tips" naturally once each.
- betting_guide: 100-140 words of practical guidance for betting on this league responsibly: comparing odds across bookmakers, understanding implied probability, sticking to a bankroll plan. General best practice only — no invented league statistics.{FAQ_RULES}"""


def p_tips(slug: str, name: str) -> str:
    return f"""Write an evergreen guide for our "{name}" page (URL slug: /tips/{slug}).

Sections:
- intro: 90-130 words: what this bet type is and who it suits.
- how_it_works: 110-150 words: mechanics of the bet with one simple worked example using odds (invent only the arithmetic example, clearly hypothetical, e.g. "say a team is priced at 2.00").
- strategy: 110-150 words: sensible approach to this bet type — value thinking, common mistakes, bankroll discipline. No promises of profit.{FAQ_RULES}"""


def p_bookmaker(bk: dict) -> str:
    sc = bk.get("scores") or {}
    b = bk.get("bonus") or {}
    return f"""Write the editorial verdict for our review of the bookmaker "{bk.get('name')}".

Data:
- Overall rating: {bk.get('rating')}/5
- Category scores (out of 10): {json.dumps(sc)}
- Welcome offer: {b.get('headline')} (wagering {b.get('wagering')}, min odds {b.get('min_odds')})
- Available in: {', '.join((bk.get('countries') or [])).upper()}
- Founded: {bk.get('founded', 'n/a')}; licence: {bk.get('licence', 'n/a')}

Sections:
- verdict: 130-170 words weighing the strong and weak category scores honestly (praise the high ones, note the lower ones), and put the welcome offer in context including its wagering terms.
- who_for: 50-70 words on which kind of bettor this bookmaker suits best, based on the scores.{FAQ_RULES}"""


def p_casino(c: dict) -> str:
    sc = c.get("scores") or {}
    b = c.get("bonus") or {}
    return f"""Write the editorial verdict for our review of the online casino "{c.get('name')}".

Data:
- Overall rating: {c.get('rating')}/5
- Category scores (out of 10): {json.dumps(sc)}
- Welcome offer: {b.get('headline')} (wagering {b.get('wagering')}x)
- Game providers: {', '.join((c.get('providers') or [])[:6])}
- Available in: {', '.join((c.get('countries') or [])).upper()}

Sections:
- verdict: 130-170 words, honest about strong and weak scores; explain the wagering requirement's practical meaning.
- who_for: 50-70 words on which players this casino suits.{FAQ_RULES}"""


def p_country(c: dict) -> str:
    return f"""Write the intro for our "Betting sites in {c.get('name')}" page.

Data:
- Country: {c.get('name')}
- Regulator: {c.get('regulator', 'n/a')}
- Currency: {c.get('currency', 'n/a')}
- Popular payment methods: {', '.join(c.get('popular_payments') or [])}

Sections:
- intro: 110-150 words about choosing a licensed bookmaker in {c.get('name')}: role of the regulator named above, why licensing matters, what our rankings weigh (odds, payout speed, app quality, safety). Do not make specific legal claims beyond "check local rules" — laws change.{FAQ_RULES}"""


def p_page(key: str, what: str) -> str:
    return f"""Write evergreen copy for {what} (site section /{key}/).

Sections:
- intro: 100-140 words explaining what this page offers a bettor and how to get the most out of it.
  Mention that every published tip is archived and settled openly (our core trust promise) where natural.
{FAQ_RULES}"""


TEAM_MIN_APPEARANCES = 3   # AI text once a team has this many archived/current fixtures

def p_team(name: str, leagues: list[str], n_tips: int, settled: int, won: int, profit: float, markets: list[str]) -> str:
    return f"""Write evergreen copy for our "{name} betting tips" team page.

Data (our own archive only):
- Team: {name}, seen in: {', '.join(leagues)}
- Our archived record on {name} fixtures so far: {n_tips} tips published, {settled} settled ({won} won), cumulative profit {profit:+.2f} units at flat stakes
- Markets we have tipped on their fixtures: {', '.join(markets) or 'match result, totals'}

Sections:
- intro: 100-140 words on following {name} through our value lens: how the page works (every {name}
  fixture we cover gets a data-driven tip, archived before kick-off and settled against the final
  score), and how to read our tips on their matches (implied probability, value edges). STRICTLY no
  invented club facts: no history, players, managers, stadiums, form or fan culture — you only know
  the betting data above. Do not cite the exact record numbers (they change daily).
{FAQ_RULES}"""


MATRIX = [
    ("match-result", "Match Result Tips", "1X2 winner picks"),
    ("over-under", "Over/Under Goals Tips", "totals picks"),
    ("draw", "Draw Tips", "value draw picks"),
]
COMBO_MIN_ITEMS = 2   # mirror of the Astro page threshold
RECAP_MIN_SETTLED = 3   # AI review once a finished week has this many graded bets


def p_recap(label: str, week: int, year: int, st: dict, markets: list[str], leagues: list[str],
            best: str, worst: str) -> str:
    return f"""Write copy for the weekly results recap page "Week {week}, {year}" ({label}) of our own
prediction model. The week is finished and settled; these final figures are frozen, so unlike live
pages you MAY cite them exactly.

Final record: {st['tips']} tips published, {st['settled']} settled, {st['won']} won, {st['lost']} lost,
{st['voided']} void. Profit at flat 1-unit stakes: {st['profit']:+.2f}u. ROI per graded bet: {st['roi']:+.1f}%.
By market: {'; '.join(markets)}.
By league: {'; '.join(leagues)}.
Best result: {best}. Worst result: {worst}.

Return JSON:
- intro: 110-150 words reviewing the week from these figures only: overall record, which market or
  league carried the week and which dragged it, and one honest observation. If the sample is small
  (under 20 graded bets), say plainly that a week proves little either way — no trend claims.{FAQ_RULES}
  Exception for this page: the frozen final figures above may be cited in answers."""

def p_combo(type_name: str, short: str, league: str, n: int, settled: int, won: int, profit: float) -> str:
    return f"""Write evergreen copy for our "{league} {type_name}" page ({short} for the {league}).

Data (our own archive only): {n} tips on this market in this league so far, {settled} settled ({won} won), cumulative profit {profit:+.2f} units at flat stakes.

Sections:
- intro: 100-140 words on this specific market in this specific league through our value lens: what the
  market is, how our model finds value in it (implied probability vs best price), and that every tip is
  archived pre-match and settled openly. STRICTLY no invented league statistics, trends or team facts.
  Do not cite the exact record numbers (they change daily).
{FAQ_RULES}"""


# ---------------------------------------------------------------- worklist
def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_worklist() -> list[dict]:
    work = []
    preds = load_json(ROOT / "data" / "predictions.json")
    tips = preds.get("tips", [])

    # matches — one preview per fixture page
    for t in tips:
        slug = slugify(f"{t.get('home')}-vs-{t.get('away')}")
        work.append({
            "key": f"match:{slug}",
            "kind": "match",
            "prompt": p_match(t),
            # hash on fixture identity, not odds — prices move hourly, the preview shouldn't
            "hash_src": f"{t.get('home')}|{t.get('away')}|{t.get('league')}|{(t.get('kickoff') or '')[:10]}",
        })

    # leagues
    by_league: dict[str, list[dict]] = {}
    for t in tips:
        by_league.setdefault(t.get("league") or "", []).append(t)
    for name, ts in by_league.items():
        if not name:
            continue
        teams = [x for t in ts for x in (t.get("home"), t.get("away")) if x]
        work.append({
            "key": f"league:{slugify(name)}",
            "kind": "league",
            "prompt": p_league(name, ts[0].get("league_short", ""), teams, len(ts)),
            "hash_src": name + "|v2",   # v2: faq added
        })

    # bet types (evergreen)
    for slug, name in BET_TYPES:
        work.append({"key": f"tips:{slug}", "kind": "tips", "prompt": p_tips(slug, name), "hash_src": slug + "|v2"})

    # bookmakers / casinos / countries — read from the Astro data (hand-maintained)
    for bk in (load_json(ASTRO / "src" / "data" / "bookmakers.json").get("bookmakers") or []):
        work.append({"key": f"bookmaker:{bk['slug']}", "kind": "bookmaker", "prompt": p_bookmaker(bk),
                     "hash_src": json.dumps(bk, sort_keys=True) + "|v2"})
    for c in (load_json(ASTRO / "src" / "data" / "casinos.json").get("casinos") or []):
        work.append({"key": f"casino:{c['slug']}", "kind": "casino", "prompt": p_casino(c),
                     "hash_src": json.dumps(c, sort_keys=True) + "|v2"})
    for c in (load_json(ASTRO / "src" / "data" / "countries.json").get("countries") or []):
        work.append({"key": f"country:{c['slug']}", "kind": "country", "prompt": p_country(c),
                     "hash_src": json.dumps({k: c.get(k) for k in ("name", "regulator", "currency")}, sort_keys=True) + "|v2"})

    # bet-type x league matrix pages
    hist_all = [v for v in load_json(ROOT / "data" / "history.json").get("tips", {}).values()
                if v.get("score") != "simulated" and not str(v.get("event_id", "")).startswith("mock")]
    def _combo_match(kind_key, rec_type, outcome):
        if kind_key == "over-under":
            return rec_type == "totals"
        if kind_key == "draw":
            return rec_type == "h2h" and outcome == "Draw"
        return rec_type == "h2h" and outcome != "Draw"
    combo_leagues = sorted({x.get("league") for x in hist_all if x.get("league")}
                           | {t.get("league") for t in tips if t.get("league")})
    for ckey, cname, cshort in MATRIX:
        for lg in combo_leagues:
            live_n = sum(1 for t in tips if t.get("league") == lg and
                         _combo_match(ckey, (t.get("recommendation") or {}).get("type"),
                                      (t.get("recommendation") or {}).get("outcome")))
            past = [h for h in hist_all if h.get("league") == lg and
                    _combo_match(ckey, h.get("type"), h.get("outcome"))]
            if live_n + len(past) < COMBO_MIN_ITEMS:
                continue
            st = [h for h in past if h.get("status") in ("won", "lost", "void")]
            work.append({
                "key": f"combo:{ckey}:{slugify(lg)}",
                "kind": "combo",
                "prompt": p_combo(cname, cshort, lg, live_n + len(past), len(st),
                                  sum(1 for h in st if h["status"] == "won"),
                                  sum(float(h.get("profit") or 0) for h in st)),
                "hash_src": f"combo|{ckey}|{lg}|v1",
            })

    # weekly recap pages — AI review once a week is finished and settled enough.
    # Hash on the final stats: late settlements retrigger a fresh (cheap) rewrite,
    # then the copy freezes for good.
    from datetime import date, timedelta
    by_monday: dict[str, list[dict]] = {}
    for h in hist_all:
        d = str(h.get("kickoff") or "")[:10]
        try:
            dd = date.fromisoformat(d)
        except ValueError:
            continue
        by_monday.setdefault((dd - timedelta(days=dd.isoweekday() - 1)).isoformat(), []).append(h)
    today = datetime.now(timezone.utc).date()
    for mon_s, ws in sorted(by_monday.items()):
        monday = date.fromisoformat(mon_s)
        if monday + timedelta(days=6) >= today:      # only finished weeks
            continue
        st_list = [h for h in ws if h.get("status") in ("won", "lost", "void")]
        graded = [h for h in st_list if h.get("status") != "void"]
        if len(st_list) < RECAP_MIN_SETTLED or not graded:
            continue
        iso_y, iso_w, _ = monday.isocalendar()
        stats = {
            "tips": len(ws), "settled": len(st_list),
            "won": sum(1 for h in graded if h["status"] == "won"),
            "lost": sum(1 for h in graded if h["status"] == "lost"),
            "voided": len(st_list) - len(graded),
            "profit": sum(float(h.get("profit") or 0) for h in st_list),
        }
        stats["roi"] = stats["profit"] / len(graded) * 100
        def _grp(key):
            g: dict[str, list[dict]] = {}
            for h in st_list:
                g.setdefault(str(h.get(key) or "—"), []).append(h)
            names = {"h2h": "match result (1X2)", "totals": "over/under totals"}
            return [f"{names.get(k, k)}: {sum(1 for x in v if x['status'] == 'won')}W-"
                    f"{sum(1 for x in v if x['status'] == 'lost')}L, "
                    f"{sum(float(x.get('profit') or 0) for x in v):+.2f}u"
                    for k, v in sorted(g.items())]
        def _pick(h):
            return f"{h.get('home')} v {h.get('away')} ({h.get('market')}, odds {h.get('odds')}, final {h.get('score')})"
        by_profit = sorted(graded, key=lambda h: float(h.get("profit") or 0))
        label = f"{monday.strftime('%d %b')} – {(monday + timedelta(days=6)).strftime('%d %b %Y')}"
        work.append({
            "key": f"recap:{iso_y}-w{iso_w:02d}",
            "kind": "recap",
            "prompt": p_recap(label, iso_w, iso_y, stats, _grp("type"), _grp("league"),
                              _pick(by_profit[-1]), _pick(by_profit[0])),
            "hash_src": f"recap|{iso_y}-w{iso_w:02d}|{stats['settled']}|{stats['won']}|{stats['profit']:.2f}",
        })

    # team hub pages — AI text once a team is seen often enough
    hist = load_json(ROOT / "data" / "history.json").get("tips", {})
    team_agg: dict[str, dict] = {}
    def _feed(name, league, market, status, profit):
        if not name:
            return
        a = team_agg.setdefault(name, {"n": 0, "settled": 0, "won": 0, "profit": 0.0,
                                       "leagues": set(), "markets": set()})
        a["n"] += 1
        a["leagues"].add(league or "")
        if market:
            a["markets"].add("totals" if ("Over" in market or "Under" in market) else "match result")
        if status in ("won", "lost", "void"):
            a["settled"] += 1
            a["profit"] += float(profit or 0)
            if status == "won":
                a["won"] += 1
    for v in hist.values():
        if v.get("score") == "simulated" or str(v.get("event_id", "")).startswith("mock"):
            continue
        for side in ("home", "away"):
            _feed(v.get(side), v.get("league"), v.get("market"), v.get("status"), v.get("profit"))
    for t in tips:
        for side in ("home", "away"):
            _feed(t.get(side), t.get("league"), (t.get("recommendation") or {}).get("text"), None, 0)
    for name, a in team_agg.items():
        if a["n"] < TEAM_MIN_APPEARANCES:
            continue
        work.append({
            "key": f"team:{slugify(name)}",
            "kind": "team",
            "prompt": p_team(name, sorted(a["leagues"] - {""}), a["n"], a["settled"], a["won"],
                             a["profit"], sorted(a["markets"])),
            "hash_src": f"team|{name}|v1",   # written once; stats change daily but the copy is evergreen
        })

    # thin index pages
    for key, what in PAGES:
        work.append({"key": f"page:{key}", "kind": "page", "prompt": p_page(key, what), "hash_src": f"{key}|{what}|v2"})

    # dedupe by key (e.g. rematch fixtures share a home-vs-away slug/page)
    seen: set[str] = set()
    work = [w for w in work if not (w["key"] in seen or seen.add(w["key"]))]
    return work


# ---------------------------------------------------------------- client
def make_client():
    import anthropic
    from anthropic import DefaultHttpxClient
    kw = {}
    if sys.platform == "win32":
        # The user's antivirus TLS-inspection breaks the certifi bundle; trust the
        # Windows store instead (verification stays on). Same fix as odds_api.py.
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
            kw["http_client"] = DefaultHttpxClient(verify=ctx)
        except Exception:
            pass
    return anthropic.Anthropic(**kw)


def generate_one(client, item: dict) -> dict:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        output_config={"format": {"type": "json_schema", "schema": SCHEMAS[item["kind"]]}},
        messages=[{"role": "user", "content": item["prompt"]}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model refused")
    text = next(b.text for b in resp.content if b.type == "text")
    data = json.loads(text)
    return {
        **data,
        "_kind": item["kind"],
        "_model": resp.model,
        "_hash": hashlib.sha256(item["hash_src"].encode()).hexdigest()[:16],
        "_generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "_usage": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens},
    }


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", choices=list(SCHEMAS))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    store = load_json(OUT)
    entries: dict = store.get("entries", {})
    work = build_worklist()
    if args.only:
        work = [w for w in work if w["kind"] == args.only]

    # Prune only match entries that exist NEITHER in the current feed NOR in the
    # settlement archive. Archived matches keep their pages forever (SEO archive),
    # so their previews must survive too. Mock-phase entries never get pages.
    live_keys = {w["key"] for w in build_worklist()}
    hist = load_json(ROOT / "data" / "history.json").get("tips", {})
    archived_keys = {
        f"match:{slugify(str(v.get('home')) + '-vs-' + str(v.get('away')))}"
        for v in (hist.values() if isinstance(hist, dict) else [])
        if v.get("score") != "simulated" and not str(v.get("event_id", "")).startswith("mock")
    }
    keep = live_keys | archived_keys
    stale = [k for k in entries if k.startswith("match:") and k not in keep]
    for k in stale:
        del entries[k]

    todo = []
    for w in work:
        h = hashlib.sha256(w["hash_src"].encode()).hexdigest()[:16]
        cur = entries.get(w["key"])
        if not args.force and cur and cur.get("_hash") == h:
            continue
        todo.append(w)
    if args.limit:
        todo = todo[:args.limit]

    kinds = {}
    for w in todo:
        kinds[w["kind"]] = kinds.get(w["kind"], 0) + 1
    print(f"content: {len(entries)} cached, {len(todo)} to generate {kinds if kinds else ''}"
          + (f", {len(stale)} stale pruned" if stale else ""))

    if args.dry_run or not todo:
        if stale or args.dry_run is False:
            OUT.write_text(json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                       "entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠ ANTHROPIC_API_KEY not set (pipeline/.env) — skipping content generation")
        return 0   # never fail the pipeline over missing copy

    client = make_client()
    lock = threading.Lock()
    done = fail = 0
    tok_in = tok_out = 0

    def run(w):
        nonlocal done, fail, tok_in, tok_out
        try:
            entry = generate_one(client, w)
            with lock:
                entries[w["key"]] = entry
                done += 1
                tok_in += entry["_usage"]["in"]
                tok_out += entry["_usage"]["out"]
                # crash-safe: persist as we go
                OUT.write_text(json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                           "entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  ✓ {w['key']} ({done}/{len(todo)})")
        except Exception as e:
            with lock:
                fail += 1
                print(f"  ✗ {w['key']}: {type(e).__name__} {str(e)[:90]}")

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(as_completed(ex.submit(run, w) for w in todo))

    cost = tok_in / 1e6 * 5 + tok_out / 1e6 * 25   # opus 4.8 $5/$25 per MTok
    print(f"✓ content.json: {done} generated, {fail} failed, {len(entries)} total"
          f" · tokens {tok_in}+{tok_out} ≈ ${cost:.2f}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
