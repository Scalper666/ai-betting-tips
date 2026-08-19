// Path builders for the localized data sections. getStaticPaths runs isolated
// from page frontmatter, so anything shared between the EN and [lang] routes
// has to live in lib/.
import fdData from '../data/football-data.json';
import seasonsData from '../data/seasons.json';
import { slugify } from './utils.js';
import { leagueName } from './leagues.js';

// /table/{slug} — leagues whose snapshot has at least one played match
export function tablePaths() {
  // A page exists as soon as the league HAS a standings shape, even when every
  // row still reads 0 played. Gating on played>0 made these pages flicker: the
  // new season reset the top leagues' counters and /table/premier-league and
  // peers 404'd overnight after sitting in the index (GSC caught it). The view
  // renders an honest "season hasn't started" state and links last season's
  // final table instead.
  return Object.entries(fdData.leagues ?? {})
    .filter(([, lg]) => (lg.standings ?? []).length > 0)
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
