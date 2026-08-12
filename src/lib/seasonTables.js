import fd from '../data/football-data.json';
import imported from '../data/results-import.json';
import { leagueName } from './leagues.js';
import { slugify } from './utils.js';

// ── Final league tables for the last COMPLETED season, computed from raw
//    results (3-1-0 points). Shared by the [slug]/[season] route and every
//    page that links to it (getStaticPaths isolation).
//
//    Season windows: cross-year leagues run 1 Jul – 30 Jun; calendar leagues
//    (listed explicitly — a heuristic here would misfile someone every year)
//    run 1 Jan – 31 Dec. Liga MX is deliberately absent: its Apertura and
//    Clausura are two separate championships, and one merged table would be
//    fiction. Administrative points deductions are NOT applied — the page
//    says so out loud.
const CALENDAR = new Set([
  'soccer_usa_mls', 'soccer_brazil_campeonato', 'soccer_argentina_primera_division',
  'soccer_sweden_allsvenskan', 'soccer_norway_eliteserien', 'soccer_japan_j_league',
  'soccer_korea_kleague1',
]);
const SKIP = new Set(['soccer_mexico_ligamx']);
const MIN_MATCHES = 100;

function computeTable(results) {
  const acc = {};
  for (const r of results) {
    const h = (acc[r.h] ??= { team: r.h, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 });
    const a = (acc[r.a] ??= { team: r.a, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 });
    h.p++; a.p++;
    h.gf += r.hs; h.ga += r.as; a.gf += r.as; a.ga += r.hs;
    if (r.hs > r.as) { h.w++; a.l++; h.pts += 3; }
    else if (r.hs < r.as) { a.w++; h.l++; a.pts += 3; }
    else { h.d++; a.d++; h.pts++; a.pts++; }
  }
  return Object.values(acc).sort(
    (x, y) => y.pts - x.pts || (y.gf - y.ga) - (x.gf - x.ga) || y.gf - x.gf || x.team.localeCompare(y.team)
  );
}

export function buildSeasonTables() {
  // last completed windows as of the 2026-27 European season
  const out = [];
  const sources = {};
  for (const [sk, lg] of Object.entries(imported.leagues ?? {})) sources[sk] = lg.results ?? [];
  for (const [sk, lg] of Object.entries(fd.leagues ?? {})) {
    if ((lg.results ?? []).length) sources[sk] = lg.results;   // org data wins
  }

  for (const [sk, results] of Object.entries(sources)) {
    if (SKIP.has(sk)) continue;
    const calendar = CALENDAR.has(sk);
    const [from, to, season] = calendar
      ? ['2025-01-01', '2025-12-31', '2025']
      : ['2025-07-01', '2026-06-30', '2025-26'];
    const windowed = results.filter((r) => r.d >= from && r.d <= to);
    if (windowed.length < MIN_MATCHES) continue;
    const name = leagueName(sk, sk);
    out.push({
      sportKey: sk,
      league: name,
      slug: slugify(name),
      season,
      matches: windowed.length,
      table: computeTable(windowed),
      lastMatch: windowed[windowed.length - 1]?.d ?? from,
    });
  }
  return out.sort((a, b) => a.league.localeCompare(b.league));
}

export function buildSeasonTablePaths() {
  return buildSeasonTables().map((s) => ({
    params: { slug: s.slug, season: s.season },
    props: s,
  }));
}
