import fd from '../data/football-data.json';
import archive from '../data/results-archive.json';

// ── Team form / H2H / standings, merged from two sources:
//    * football-data.org snapshot (data/football-data.json) — deep season
//      results + tables for the leagues its free tier covers;
//    * our own results archive (data/results-archive.json) — every completed
//      score The Odds API settlement calls return; the only source for MLS.
//    football-data team names differ from The Odds API's ("Barça" vs
//    "Barcelona"), so lookups go through a normalised fuzzy matcher.

const LEAGUES = fd.leagues ?? {};
const ARCHIVE = Object.values(archive.games ?? {});

const STOP = new Set(['fc', 'cf', 'cd', 'rcd', 'sc', 'ac', 'afc', 'ca', 'cfc', 'club', 'clube',
  'do', 'de', 'la', 'sp', 'pr', 'mg', 'rj', 'albion', 'town', 'county']);
// tokens too common to identify a club on their own ("Coventry City" ≠ "Man City")
const GENERIC = new Set(['city', 'united', 'real', 'deportivo', 'sporting', 'racing']);

// hand-checked bridges the fuzzy matcher can't infer (norm(odds name) -> fd name)
const ALIAS = {
  'barcelona': 'Barça',
  'atletico madrid': 'Atleti',
  'internacional': 'Internacional',
};

export const norm = (s) => String(s ?? '').toLowerCase().normalize('NFD')
  .replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
const toks = (s) => norm(s).split(' ').filter((t) => t.length >= 3 && !STOP.has(t));

function ed1(a, b) { // true when edit distance ≤ 1
  if (a === b) return true;
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0, j = 0, diff = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { i++; j++; continue; }
    if (++diff > 1) return false;
    if (a.length > b.length) i++;
    else if (b.length > a.length) j++;
    else { i++; j++; }
  }
  return diff + (a.length - i) + (b.length - j) <= 1;
}

function score(a, b) {
  let s = 0;
  for (const x of a) for (const y of b) {
    const lo = Math.min(x.length, y.length), hi = Math.max(x.length, y.length);
    if (x === y) s += GENERIC.has(x) ? 0.3 : 1;
    // prefix pair: "atleti"~"atletico"; short abbreviations ("man"~"manchester")
    // count too, but only against a clearly longer token
    else if ((x.startsWith(y) || y.startsWith(x)) && (lo >= 4 || (lo >= 3 && hi >= 6))) s += 0.7;
    else if (x.length >= 5 && y.length >= 5 && ed1(x, y)) s += 0.6;
  }
  return s;
}

const fdNamesOf = (lg) => [...new Set([
  ...(lg.standings ?? []).map((r) => r.team),
  ...(lg.results ?? []).flatMap((r) => [r.h, r.a]),
])].filter(Boolean);

const cache = new Map();

// Odds-API team name -> football-data team name (null when no confident match)
export function resolveTeam(sportKey, oddsName) {
  const lg = LEAGUES[sportKey];
  if (!lg || !oddsName) return null;
  const key = sportKey + '|' + oddsName;
  if (cache.has(key)) return cache.get(key);

  let found = ALIAS[norm(oddsName)] ?? null;
  if (!found) {
    const nt = toks(oddsName);
    let best = null, bestS = 0, second = 0;
    for (const f of fdNamesOf(lg)) {
      const s = score(nt, toks(f));
      if (s > bestS) { second = bestS; bestS = s; best = f; }
      else if (s > second) second = s;
    }
    found = bestS >= 0.6 && bestS > second ? best : null; // demand a unique winner
  }
  cache.set(key, found);
  return found;
}

const wdl = (my, their) => (my > their ? 'W' : my < their ? 'L' : 'D');

// last N completed games for a team, newest first:
//   {d, opp, ha: 'H'|'A', score: '2-1' (team-first), res: 'W'|'D'|'L'}
export function teamForm(sportKey, oddsName, n = 5) {
  const lg = LEAGUES[sportKey];
  if (lg) {
    const name = resolveTeam(sportKey, oddsName);
    if (!name) return [];
    return (lg.results ?? [])
      .filter((r) => r.h === name || r.a === name)
      .sort((a, b) => String(b.d).localeCompare(String(a.d)))
      .slice(0, n)
      .map((r) => {
        const home = r.h === name;
        const my = home ? r.hs : r.as, their = home ? r.as : r.hs;
        return { d: r.d, opp: home ? r.a : r.h, ha: home ? 'H' : 'A', score: `${my}-${their}`, res: wdl(my, their) };
      });
  }
  // fallback: our own archive (names already match The Odds API)
  return ARCHIVE
    .filter((g) => g.sk === sportKey && (g.h === oddsName || g.a === oddsName))
    .sort((a, b) => String(b.d).localeCompare(String(a.d)))
    .slice(0, n)
    .map((g) => {
      const home = g.h === oddsName;
      const my = home ? g.hs : g.as, their = home ? g.as : g.hs;
      return { d: g.d, opp: home ? g.a : g.h, ha: home ? 'H' : 'A', score: `${my}-${their}`, res: wdl(my, their) };
    });
}

// past meetings, newest first: {d, home, away, score: '2-1', res} — res is the
// result from the PAGE home team's perspective
export function h2hBetween(sportKey, oddsHome, oddsAway, n = 10) {
  const lg = LEAGUES[sportKey];
  let games, nameH, nameA;
  if (lg) {
    nameH = resolveTeam(sportKey, oddsHome);
    nameA = resolveTeam(sportKey, oddsAway);
    if (!nameH || !nameA) return [];
    games = (lg.results ?? []).filter((r) =>
      (r.h === nameH && r.a === nameA) || (r.h === nameA && r.a === nameH));
  } else {
    nameH = oddsHome; nameA = oddsAway;
    games = ARCHIVE.filter((g) => g.sk === sportKey &&
      ((g.h === nameH && g.a === nameA) || (g.h === nameA && g.a === nameH)));
  }
  return games
    .sort((a, b) => String(b.d).localeCompare(String(a.d)))
    .slice(0, n)
    .map((r) => {
      const myGoals = r.h === nameH ? r.hs : r.as, theirGoals = r.h === nameH ? r.as : r.hs;
      return { d: r.d, home: r.h, away: r.a, score: `${r.hs}-${r.as}`, res: wdl(myGoals, theirGoals) };
    });
}

// real club crest URL (football-data.org CDN), or null → caller falls back to
// the lettered colour badge (e.g. all of MLS)
export function teamCrest(sportKey, oddsName) {
  const lg = LEAGUES[sportKey];
  if (!lg?.crests) return null;
  const name = resolveTeam(sportKey, oddsName);
  return (name && lg.crests[name]) || null;
}

// current league table, or null while the season hasn't started (all zeros)
export function leagueTable(sportKey) {
  const lg = LEAGUES[sportKey];
  const rows = lg?.standings ?? [];
  if (!rows.length || !rows.some((r) => (r.p ?? 0) > 0)) return null;
  return { name: lg.name, rows };
}
