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
    ("tipsters", "the tipster leaderboard with honest, settled win rates and ROI for every tipster"),
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

    # thin index pages
    for key, what in PAGES:
        work.append({"key": f"page:{key}", "kind": "page", "prompt": p_page(key, what), "hash_src": key + "|v1"})

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
