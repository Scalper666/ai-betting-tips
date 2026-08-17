import predictions from '../data/predictions.json';
import oddsHistory from '../data/odds_history.json';
import { slugify } from './utils.js';
import { buildLeagueNames } from './leaguePages.js';

// ── Shared path/data builder for the per-league dropping-odds pages.
//    Lives here because getStaticPaths is frontmatter-isolated: both the
//    [slug] route and anything linking to it must derive the same set.
//    Pages are ETERNAL (feed ∪ history ∪ registry, same union as league
//    pages): the old 3-move threshold made URLs appear and vanish between
//    builds, which GSC read as intermittent 404s. A quiet league now keeps
//    its page with an honest "no movement" state instead.

export function droppingByLeague() {
  const byLeague = {};
  for (const t of (predictions.tips ?? [])) {
    const rec = t.recommendation ?? {};
    const series = oddsHistory[`${t.id}|${rec.text ?? ''}`] ?? [];
    if (series.length < 2) continue;
    const first = Number(series[0]?.price), last = Number(series[series.length - 1]?.price);
    if (!(first > 1) || !(last > 1) || first === last) continue;
    (byLeague[t.league] ??= []).push({
      t, market: rec.text, first, last,
      move: Math.round(((last - first) / first) * 1000) / 10,
      points: series.length,
    });
  }
  const out = {};
  for (const [league, rows] of Object.entries(byLeague)) {
    rows.sort((a, b) => Math.abs(b.move) - Math.abs(a.move));
    out[league] = rows;
  }
  return out;
}

export function buildDroppingPaths() {
  const moved = droppingByLeague();
  return [...buildLeagueNames()].map(([slug, league]) => ({
    params: { slug },
    props: { league, rows: moved[league] ?? [] },
  }));
}

export const hasDroppingPage = (league) => buildLeagueNames().has(slugify(league));
