// Team directory shared by /teams and /teams/{league}. getStaticPaths runs in
// isolation from a page's frontmatter, so this has to live in lib/ — see the
// Astro gotcha noted in the project docs.
import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import { slugify } from './utils.js';

// Every club we have ever tipped on, grouped by the league it appears in.
export function teamDirectory() {
  const teams = new Map();   // slug -> { name, leagues:Set, n }
  const touch = (name, league) => {
    if (!name) return;
    const slug = slugify(name);
    if (!teams.has(slug)) teams.set(slug, { name, leagues: new Set(), n: 0 });
    const t = teams.get(slug);
    t.n += 1;
    if (league) t.leagues.add(league);
  };
  for (const h of Object.values(historyData.tips ?? {})) {
    if (h.score === 'simulated' || String(h.event_id ?? '').startsWith('mock')) continue;
    touch(h.home, h.league); touch(h.away, h.league);
  }
  for (const t of predictions.tips ?? []) {
    touch(t.home, t.league); touch(t.away, t.league);
  }

  const byLeague = {};
  for (const [slug, t] of teams) {
    const lg = [...t.leagues][0] ?? 'Other';
    (byLeague[lg] ??= []).push({ slug, ...t });
  }
  for (const lg in byLeague) byLeague[lg].sort((a, b) => a.name.localeCompare(b.name));

  return { teams, byLeague, leagueNames: Object.keys(byLeague).sort() };
}
