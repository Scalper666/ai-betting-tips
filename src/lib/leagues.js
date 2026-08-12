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
  soccer_uefa_champs_league_qualification: 'UCL Qualification',
  soccer_uefa_europa_conference_league: 'Conference League',
  soccer_turkey_super_league: 'Süper Lig',
  soccer_belgium_first_div: 'Belgian Pro League',
  soccer_usa_mls: 'MLS',
  soccer_spl: 'Scottish Premiership',
  soccer_argentina_primera_division: 'Liga Profesional',
  soccer_mexico_ligamx: 'Liga MX',
  soccer_denmark_superliga: 'Danish Superliga',
  soccer_sweden_allsvenskan: 'Allsvenskan',
  soccer_austria_bundesliga: 'Austrian Bundesliga',
  soccer_switzerland_superleague: 'Swiss Super League',
  soccer_greece_super_league: 'Greek Super League',
  soccer_poland_ekstraklasa: 'Ekstraklasa',
  soccer_norway_eliteserien: 'Eliteserien',
  soccer_japan_j_league: 'J1 League',
  soccer_korea_kleague1: 'K League 1',
  soccer_germany_bundesliga2: '2. Bundesliga',
  soccer_spain_segunda_division: 'La Liga 2',
  soccer_england_league1: 'League One',
};

// Falls back to the data source's own name for leagues not listed above.
export const leagueName = (sportKey, fallback = '') => LEAGUE_NAME[sportKey] ?? fallback;
