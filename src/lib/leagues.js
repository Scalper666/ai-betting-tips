// Canonical display names per Odds API sport key, mirroring the `label` values
// in pipeline/odds_api.py SPORT_KEYS. Table and scorer pages must NOT derive
// their slug from whatever the live feed happens to contain: a league with no
// priced fixtures today (UEFA competitions out of season) would fall back to
// the football-data name and silently change its URL once markets open.
// Keep this map in sync with SPORT_KEYS whenever a covered league is added.
export const LEAGUE_NAME = {
  soccer_epl: 'Premier League',
  soccer_efl_champ: 'Championship',
  soccer_spain_la_liga: 'La Liga',
  soccer_italy_serie_a: 'Serie A',
  soccer_germany_bundesliga: 'Bundesliga',
  soccer_france_ligue_one: 'Ligue 1',
  soccer_netherlands_eredivisie: 'Eredivisie',
  soccer_portugal_primeira_liga: 'Primeira Liga',
  soccer_brazil_campeonato: 'Brasileirão',
  soccer_uefa_champs_league: 'Champions League',
  soccer_uefa_europa_league: 'Europa League',
};

// Falls back to the data source's own name for leagues not listed above.
export const leagueName = (sportKey, fallback = '') => LEAGUE_NAME[sportKey] ?? fallback;
