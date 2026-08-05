// Path builders for the localized data sections. getStaticPaths runs isolated
// from page frontmatter, so anything shared between the EN and [lang] routes
// has to live in lib/.
import fdData from '../data/football-data.json';
import seasonsData from '../data/seasons.json';
import { slugify } from './utils.js';
import { leagueName } from './leagues.js';

// /table/{slug} — leagues whose snapshot has at least one played match
export function tablePaths() {
  return Object.entries(fdData.leagues ?? {})
    .filter(([, lg]) => (lg.standings ?? []).some((r) => (r.p ?? 0) > 0))
    .map(([sk, lg]) => ({ sk, slug: slugify(leagueName(sk, lg.name)) }));
}

// /results/{slug} — leagues with finished matches on record
export function resultsPaths() {
  return Object.entries(fdData.leagues ?? {})
    .filter(([, lg]) => (lg.results ?? []).length > 0)
    .map(([sk, lg]) => ({ sk, slug: slugify(leagueName(sk, lg.name)) }));
}

// /seasons/{slug}
export function seasonPaths() {
  return (seasonsData.seasons ?? []).map((s) => ({ slug: s.slug }));
}
