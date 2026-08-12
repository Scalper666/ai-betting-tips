import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import registry from '../data/match-registry.json';
import { leagueName } from './leagues.js';
import { slugify } from './utils.js';

// ── League page path set: feed ∪ settlement archive ∪ match registry.
//    Extracted from the EN and [lang] routes, which had drifted into two
//    copies of the same loop — and both missed the registry, so a league
//    that rotated out of the feed with no official picks (Swiss Super
//    League) lost its page. Never redirect a dormant league instead: a
//    static _redirects line would shadow the real page when the league
//    wakes up, because Pages checks redirects before static assets.
export function buildLeagueNames() {
  const tips = predictions.tips ?? [];
  const names = new Map(tips.map((t) => [slugify(t.league), t.league]));
  for (const h of Object.values(historyData.tips ?? {})) {
    if (h.score === 'simulated' || String(h.event_id ?? '').startsWith('mock') || !h.league) continue;
    if (!names.has(slugify(h.league))) names.set(slugify(h.league), h.league);
  }
  for (const m of Object.values(registry.matches ?? {})) {
    const lg = m.league || leagueName(m.sk, '');
    if (lg && !names.has(slugify(lg))) names.set(slugify(lg), lg);
  }
  return names;
}
