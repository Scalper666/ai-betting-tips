// ── Internal-link guards.
// Several page families are built conditionally: a table page needs played
// matches, an H2H hub needs a results dataset, a combo page needs enough
// items, a team page needs the club to appear in the feed or archive. Linking
// unconditionally produced 100+ internal 404s, which burn crawl budget on a
// site this size. These sets mirror the getStaticPaths of each family, so a
// link can be checked before it is rendered.
import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import fdData from '../data/football-data.json';
import { slugify } from './utils.js';
import { leagueName } from './leagues.js';
import { buildH2hPairs } from './h2h.js';
import { teamDirectory } from './teams.js';
import { MATRIX } from './betTypes.js';
import { buildLeagueNames } from './leaguePages.js';

const realTip = (h) => !(h.score === 'simulated' || String(h.event_id ?? '').startsWith('mock'));

// /league/{slug} — feed ∪ settlement archive (see pages/league/[slug].astro)
const leagueSlugs = new Set();
for (const t of predictions.tips ?? []) leagueSlugs.add(slugify(t.league));
for (const h of Object.values(historyData.tips ?? {})) {
  if (realTip(h) && h.league) leagueSlugs.add(slugify(h.league));
}

// /table/{slug} and /top-scorers/{slug}
const tableSlugs = new Set();
const scorerSlugs = new Set();
for (const [sk, lg] of Object.entries(fdData.leagues ?? {})) {
  const slug = slugify(leagueName(sk, lg.name));
  if ((lg.standings ?? []).some((r) => (r.p ?? 0) > 0)) tableSlugs.add(slug);
  if ((lg.scorers ?? []).length > 0) scorerSlugs.add(slug);
}

// /results/{slug}
const resultsSlugs = new Set();
for (const [sk, lg] of Object.entries(fdData.leagues ?? {})) {
  if ((lg.results ?? []).length > 0) resultsSlugs.add(slugify(leagueName(sk, lg.name)));
}

// /h2h/league/{slug}
const h2hSlugs = new Set(buildH2hPairs().map((p) => slugify(p.league)));

// /teams/{league} and /team/{slug}
const { teams, byLeague } = teamDirectory();
const teamsHubSlugs = new Set(Object.keys(byLeague).map((l) => slugify(l)));
const teamSlugs = new Set(teams.keys());

// /tips/{type}/{league} — mirrors pages/tips/[type]/[league].astro: the
// eternal matrix builds every covered league × every market
const comboSlugs = new Set();
{
  for (const m of MATRIX) {
    for (const slug of buildLeagueNames().keys()) comboSlugs.add(`${m.type}/${slug}`);
  }
}

export const hasLeaguePage = (league) => leagueSlugs.has(slugify(league));
export const hasTablePage = (league) => tableSlugs.has(slugify(league));
export const hasScorersPage = (league) => scorerSlugs.has(slugify(league));
export const hasH2hHub = (league) => h2hSlugs.has(slugify(league));
export const hasTeamsHub = (league) => teamsHubSlugs.has(slugify(league));
export const hasTeamPage = (team) => teamSlugs.has(slugify(team));
export const hasComboPage = (type, league) => comboSlugs.has(`${type}/${slugify(league)}`);
export const hasResultsPage = (league) => resultsSlugs.has(slugify(league));
