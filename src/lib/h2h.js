import fd from '../data/football-data.json';
import archive from '../data/results-archive.json';
import { leagueName } from './leagues.js';

// ── Head-to-head page data: every pair of teams that met at least twice in
//    our results dataset (football-data seasons + own archive). Slug is the
//    alphabetical pair, so both orders resolve to one page.

const slug = (s) => String(s ?? '').toLowerCase().normalize('NFD')
  .replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

export const pairSlug = (a, b) => {
  const [x, y] = [slug(a), slug(b)].sort();
  return `${x}-vs-${y}`;
};

// league sources: football-data leagues + archive-only leagues (e.g. MLS)
function sources() {
  const out = [];
  for (const [sk, lg] of Object.entries(fd.leagues ?? {})) {
    if ((lg.results ?? []).length) out.push({ sk, name: leagueName(sk, lg.name), results: lg.results });
  }
  const bySk = {};
  for (const g of Object.values(archive.games ?? {})) {
    if ((fd.leagues ?? {})[g.sk]) continue;             // fd already covers it
    (bySk[g.sk] ??= []).push({ d: g.d, h: g.h, a: g.a, hs: g.hs, as: g.as });
  }
  for (const [sk, results] of Object.entries(bySk)) {
    if (results.length >= 10) {
      const fallback = sk.replace('soccer_', '').replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
      out.push({ sk, name: leagueName(sk, fallback), results });
    }
  }
  return out;
}

// all H2H pages: { slug, teamA, teamB, league, sk, meetings[], stats }
export function buildH2hPairs(minMeetings = 2) {
  const pairs = new Map();
  for (const src of sources()) {
    for (const r of src.results) {
      if (!r.h || !r.a) continue;
      const key = pairSlug(r.h, r.a);
      let p = pairs.get(key);
      if (!p) {
        const [teamA, teamB] = [r.h, r.a].sort((x, y) => slug(x) < slug(y) ? -1 : 1);
        p = { slug: key, teamA, teamB, league: src.name, sk: src.sk, meetings: [] };
        pairs.set(key, p);
      }
      p.meetings.push({ d: r.d, home: r.h, away: r.a, hs: r.hs, as: r.as });
    }
  }

  const out = [];
  for (const p of pairs.values()) {
    if (p.meetings.length < minMeetings) continue;
    p.meetings.sort((a, b) => String(b.d).localeCompare(String(a.d)));
    let aW = 0, bW = 0, draws = 0, aG = 0, bG = 0, over25 = 0, btts = 0;
    for (const m of p.meetings) {
      const aHome = m.home === p.teamA;
      const ga = aHome ? m.hs : m.as, gb = aHome ? m.as : m.hs;
      aG += ga; bG += gb;
      if (ga > gb) aW++; else if (gb > ga) bW++; else draws++;
      if (m.hs + m.as > 2.5) over25++;
      if (m.hs > 0 && m.as > 0) btts++;
    }
    p.stats = {
      n: p.meetings.length, aW, bW, draws, aG, bG,
      over25, btts,
      avgGoals: Math.round(((aG + bG) / p.meetings.length) * 100) / 100,
    };
    out.push(p);
  }
  return out;
}

// ── Which languages each h2h league ships in.
//    Cloudflare Pages refuses deployments over 20,000 files, and h2h is our
//    largest family (~1700 pairs): all of it in 9 languages was 27k files and
//    failed the deploy. Localizing every pair into every language was never
//    right anyway — a Spanish reader searches La Liga and Champions League
//    head-to-heads, not Danish ones. Each language gets its own leagues plus
//    the two everyone follows (Premier League, Champions League).
//    Everything else links to the English page through lhref.
const UNIVERSAL = ['Premier League', 'Champions League'];
// 2026-09-19: no localized h2h pages any more (see MATCH_LANGS in src/i18n).
// The per-league map stays documented for when authority allows widening again:
//   es: [...UNIVERSAL, 'La Liga', 'Serie A'], pt: [...UNIVERSAL, 'Brasileirão',
//   'Primeira Liga'], de: [...UNIVERSAL, 'Bundesliga', 'Eredivisie'], fr: [...UNIVERSAL, 'Ligue 1', 'Serie A']
export const H2H_LEAGUES = {};

/** Languages a given league's h2h pages exist in (for hreflang). */
export const h2hLangsFor = (league) =>
  ['en', ...Object.keys(H2H_LEAGUES).filter((l) => H2H_LEAGUES[l].includes(league))];

/** Does /{lang}/h2h/... exist for this league? */
export const hasH2hIn = (lang, league) =>
  lang === 'en' || (H2H_LEAGUES[lang] ?? []).includes(league);
