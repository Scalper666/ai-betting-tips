import predictions from '../data/predictions.json';
import oddsHistory from '../data/odds_history.json';
import { slugify } from './utils.js';

// ── Shared path/data builder for the per-league dropping-odds pages.
//    Lives here because getStaticPaths is frontmatter-isolated: both the
//    [slug] route and anything linking to it must derive the same set.
//    A league only gets a page at 3+ tracked moved prices — a "biggest
//    movers" page with one row is a doorway, not a page.
const MIN_MOVES = 3;

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
    if (rows.length < MIN_MOVES) continue;
    rows.sort((a, b) => Math.abs(b.move) - Math.abs(a.move));
    out[league] = rows;
  }
  return out;
}

export function buildDroppingPaths() {
  return Object.entries(droppingByLeague()).map(([league, rows]) => ({
    params: { slug: slugify(league) },
    props: { league, rows },
  }));
}

export const hasDroppingPage = (league) =>
  Object.prototype.hasOwnProperty.call(droppingByLeague(), league);
