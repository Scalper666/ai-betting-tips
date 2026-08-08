"""
Own goal model: time-weighted Poisson attack/defence strengths per team,
fitted from data/football-data.json (two seasons, football-data.org) and — for
leagues that source doesn't cover (MLS) — from our own data/results-archive.json.

This is the first REAL signal in the pipeline: previously "our" probabilities
were just the bookmaker consensus with the margin removed, whose expected ROI
is ≈ −margin by construction. The model's probabilities are blended with the
market's and a tip only becomes an OFFICIAL (archived, graded) pick when the
blend disagrees with the best price by a real value threshold.

Team names in football-data differ from The Odds API's, so lookups go through
the same normalised fuzzy matcher as the Astro side (src/lib/form.js).
"""
from __future__ import annotations
import json, math, re, unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HALF_LIFE_DAYS = 240   # a result half a season+ old counts ~half
SHRINK_K = 6.0         # pseudo-games pulling strengths toward league average
MIN_GAMES = 8          # per team before we trust the model for a fixture
MAX_GOALS = 10         # Poisson grid size

# ---------------------------------------------------------------- name matcher
# (mirror of src/lib/form.js — keep the two in sync)
STOP = {"fc", "cf", "cd", "rcd", "sc", "ac", "afc", "ca", "cfc", "club", "clube",
        "do", "de", "la", "sp", "pr", "mg", "rj", "albion", "town", "county"}
GENERIC = {"city", "united", "real", "deportivo", "sporting", "racing"}

# odds-feed name (normalised) -> exact source spelling. None means REFUSE the
# fixture: the fuzzy matcher found a plausible-looking wrong club (Celta Vigo
# hit "Ceuta" through the edit-distance bridge) and a silent wrong fit is worse
# than no fit. Entries from "racing club" down serve the football-data.co.uk
# import, whose abbreviations the matcher can't bridge (STOP/GENERIC penalties).
ALIAS = {
    "barcelona": "Barça", "atletico madrid": "Atleti",
    "racing club": "Racing Club",            # racing=GENERIC + club=STOP score 0.3
    "estudiantes": "Estudiantes L.P.",
    "gimnasia la plata": "Gimnasia L.P.",
    "belgrano de cordoba": "Belgrano",
    "instituto de cordoba": "Instituto",
    "argentinos juniors": "Argentinos Jrs",
    "basaksehir": "Buyuksehyr",              # co.uk's historic spelling
    "club brugge": "Club Brugge",            # club=STOP left one token tied with Cercle
    "d c united": "DC United",               # d/c both under the 3-char floor
    "los angeles fc": "Los Angeles FC",      # ties with LA Galaxy on los+angeles
    "tokyo verdy": "Verdy",
    "dundee fc": "Dundee",                   # ties with Dundee United
    "wisla krakow": "Wisla",                 # ties with Wieczysta Krakow on krakow
    "cracovia krakow": "Cracovia",
    "celta vigo": None,                      # BLOCK: matched Ceuta (ed-distance 1)
}

# Letters NFD can't decompose — same table as slugify in generate_content.py.
# Without it "Wisła Płock" normalises to "wis a p ock" and no token survives.
_LIG = str.maketrans({"ß": "ss", "ø": "o", "ł": "l", "đ": "d", "þ": "th",
                      "æ": "ae", "œ": "oe", "ð": "d", "ı": "i"})


def _norm(s: str) -> str:
    s = str(s or "").lower().translate(_LIG)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _toks(s: str) -> list[str]:
    return [t for t in _norm(s).split(" ") if len(t) >= 3 and t not in STOP]


def _ed1(a: str, b: str) -> bool:
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    i = j = diff = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1; j += 1; continue
        diff += 1
        if diff > 1:
            return False
        if len(a) > len(b):
            i += 1
        elif len(b) > len(a):
            j += 1
        else:
            i += 1; j += 1
    return diff + (len(a) - i) + (len(b) - j) <= 1


def _score(A: list[str], B: list[str]) -> float:
    s = 0.0
    for x in A:
        for y in B:
            lo, hi = min(len(x), len(y)), max(len(x), len(y))
            if x == y:
                s += 0.3 if x in GENERIC else 1.0
            elif (x.startswith(y) or y.startswith(x)) and (lo >= 4 or (lo >= 3 and hi >= 6)):
                s += 0.7
            elif len(x) >= 5 and len(y) >= 5 and _ed1(x, y):
                s += 0.6
    return s


# ---------------------------------------------------------------- league fit
class _League:
    def __init__(self, results: list[dict]):
        today = date.today()
        wsum = wh = wa = 0.0
        acc: dict[str, dict] = {}   # team -> att_num/att_den/def_num/def_den/games

        def bump(team, att_sample, def_sample, w):
            a = acc.setdefault(team, {"an": 0.0, "aw": 0.0, "dn": 0.0, "dw": 0.0, "n": 0})
            a["an"] += w * att_sample; a["aw"] += w
            a["dn"] += w * def_sample; a["dw"] += w
            a["n"] += 1

        games = []
        for r in results:
            try:
                d = date.fromisoformat(str(r["d"]))
            except (KeyError, ValueError):
                continue
            w = 0.5 ** (max(0, (today - d).days) / HALF_LIFE_DAYS)
            games.append((r, w))
            wsum += w; wh += w * r["hs"]; wa += w * r["as"]

        self.mu_h = wh / wsum if wsum else 1.4
        self.mu_a = wa / wsum if wsum else 1.1
        for r, w in games:
            bump(r["h"], r["hs"] / max(self.mu_h, .2), r["as"] / max(self.mu_a, .2), w)
            bump(r["a"], r["as"] / max(self.mu_a, .2), r["hs"] / max(self.mu_h, .2), w)

        self.att, self.dfn, self.games = {}, {}, {}
        for t, a in acc.items():
            self.att[t] = (a["an"] + SHRINK_K) / (a["aw"] + SHRINK_K)
            self.dfn[t] = (a["dn"] + SHRINK_K) / (a["dw"] + SHRINK_K)
            self.games[t] = a["n"]

    def lambdas(self, home: str, away: str) -> tuple[float, float]:
        lh = self.mu_h * self.att.get(home, 1) * self.dfn.get(away, 1)
        la = self.mu_a * self.att.get(away, 1) * self.dfn.get(home, 1)
        return max(.15, min(5.5, lh)), max(.15, min(5.5, la))


def _pois_vec(lam: float) -> list[float]:
    return [math.exp(-lam) * lam ** k / math.factorial(k) for k in range(MAX_GOALS + 1)]


def outcome_probs(lh: float, la: float) -> dict:
    ph, pa = _pois_vec(lh), _pois_vec(la)
    home = draw = away = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            p = ph[i] * pa[j]
            if i > j:
                home += p
            elif i == j:
                draw += p
            else:
                away += p
    tot = home + draw + away
    return {"home": home / tot, "draw": draw / tot, "away": away / tot}


def scoreline_probs(lh: float, la: float, top: int = 6) -> list[dict]:
    """Most likely exact scorelines. The Poisson grid is already computed for
    1X2 and totals; exposing it costs nothing and answers the "correct score"
    question directly instead of leaving it to guesswork."""
    ph, pa = _pois_vec(lh), _pois_vec(la)
    grid = []
    tot = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            pr = ph[i] * pa[j]
            tot += pr
            grid.append((i, j, pr))
    grid.sort(key=lambda x: -x[2])
    return [{"score": f"{i}-{j}", "p": round(pr / tot, 4)} for i, j, pr in grid[:top]]


def btts_prob(lh: float, la: float) -> float:
    """P(both teams score) = 1 - P(home blanks) - P(away blanks) + P(both blank)."""
    ph, pa = _pois_vec(lh), _pois_vec(la)
    return 1.0 - ph[0] - pa[0] + ph[0] * pa[0]


def totals_probs(lh: float, la: float, point: float) -> dict:
    ph, pa = _pois_vec(lh), _pois_vec(la)
    over = push = under = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            p = ph[i] * pa[j]
            s = i + j
            if s > point:
                over += p
            elif s == point:
                push += p
            else:
                under += p
    tot = over + push + under
    return {"over": over / tot, "push": push / tot, "under": under / tot}


# ---------------------------------------------------------------- public API
class GoalModel:
    def __init__(self):
        self.leagues: dict[str, _League] = {}
        self._match_cache: dict[tuple[str, str], str | None] = {}
        self._names: dict[str, list[str]] = {}

        try:
            fd = json.loads((ROOT / "data" / "football-data.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            fd = {}
        for sk, lg in (fd.get("leagues") or {}).items():
            res = lg.get("results") or []
            if len(res) >= 60:
                self.leagues[sk] = _League(res)
                names = {r["team"] for r in lg.get("standings", [])}
                for r in res:
                    names.add(r["h"]); names.add(r["a"])
                self._names[sk] = sorted(n for n in names if n)

        # football-data.co.uk import (pipeline/import_fdcouk.py) covers the
        # leagues the free football-data.org tier can't — MLS, Argentina, the
        # second divisions. Same row shape, same fuzzy name resolution;
        # football-data.org keeps priority where both exist.
        try:
            imp = json.loads((ROOT / "data" / "results-import.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            imp = {}
        for sk, lg in (imp.get("leagues") or {}).items():
            res = lg.get("results") or []
            if sk not in self.leagues and len(res) >= 60:
                self.leagues[sk] = _League(res)
                names = set()
                for r in res:
                    names.add(r["h"]); names.add(r["a"])
                self._names[sk] = sorted(n for n in names if n)

        # our own archive fills the gaps (MLS): names already match The Odds API
        try:
            arch = json.loads((ROOT / "data" / "results-archive.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            arch = {}
        by_sk: dict[str, list[dict]] = {}
        for g in (arch.get("games") or {}).values():
            if g.get("sk") and g.get("sk") not in self.leagues:
                by_sk.setdefault(g["sk"], []).append(g)
        for sk, res in by_sk.items():
            if len(res) >= 40:
                self.leagues[sk] = _League(res)
                self._names[sk] = None   # identity names — no matching needed

    def _resolve(self, sk: str, odds_name: str) -> str | None:
        names = self._names.get(sk)
        if names is None:               # archive-backed league: names are identical
            return odds_name
        key = (sk, odds_name)
        if key in self._match_cache:
            return self._match_cache[key]
        nk = _norm(odds_name)
        if nk in ALIAS:                 # explicit verdict, including None = refuse
            self._match_cache[key] = ALIAS[nk]
            return ALIAS[nk]
        found = None
        if not found:
            nt = _toks(odds_name)
            best, bs, sec = None, 0.0, 0.0
            for f in names:
                s = _score(nt, _toks(f))
                if s > bs:
                    sec, bs, best = bs, s, f
                elif s > sec:
                    sec = s
            found = best if bs >= 0.6 and bs > sec else None
        self._match_cache[key] = found
        return found

    def probs(self, sport_key: str, home: str, away: str) -> dict | None:
        """1X2 + goal expectation for a fixture, or None when we don't have a
        trustworthy fit for both teams. Caller blends with market probs."""
        lg = self.leagues.get(sport_key)
        if not lg:
            return None
        th, ta = self._resolve(sport_key, home), self._resolve(sport_key, away)
        if not th or not ta:
            return None
        if lg.games.get(th, 0) < MIN_GAMES or lg.games.get(ta, 0) < MIN_GAMES:
            return None
        lh, la = lg.lambdas(th, ta)
        out = outcome_probs(lh, la)
        return {
            "p_home": round(out["home"], 4),
            "p_draw": round(out["draw"], 4),
            "p_away": round(out["away"], 4),
            "lambda_home": round(lh, 3),
            "lambda_away": round(la, 3),
            "games": min(lg.games[th], lg.games[ta]),
            "scorelines": scoreline_probs(lh, la),
            "p_btts": round(btts_prob(lh, la), 4),
        }
