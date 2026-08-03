"""
The Odds API client — thin wrapper around api.the-odds-api.com/v4
Docs: https://the-odds-api.com/liveapi/guides/v4/
"""
import os
import ssl
import sys
import time
from typing import Any
import requests
from requests.adapters import HTTPAdapter

ODDS_API_BASE = "https://api.the-odds-api.com/v4"


class _SSLContextAdapter(HTTPAdapter):
    """requests adapter that forces a specific SSLContext."""
    def __init__(self, ssl_context=None, **kw):
        self._ssl_context = ssl_context
        super().__init__(**kw)

    def init_poolmanager(self, *args, **kw):
        if self._ssl_context is not None:
            kw["ssl_context"] = self._ssl_context
        return super().init_poolmanager(*args, **kw)


def _build_session() -> requests.Session:
    """A requests session that trusts the OS certificate store on Windows.

    Windows machines running TLS-inspecting antivirus/proxies inject a root CA
    that lives in the Windows store (not in certifi) and may violate strict
    RFC 5280 (e.g. Basic Constraints not marked critical), which OpenSSL 3.x
    rejects. We load the Windows trust store and relax only the strict flag, so
    the chain is still verified against trusted roots. On non-Windows (CI, prod)
    this is a no-op and requests keeps its default certifi bundle.
    """
    s = requests.Session()
    if sys.platform == "win32":
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
            s.mount("https://", _SSLContextAdapter(ssl_context=ctx))
        except Exception:
            pass  # fall back to requests' default trust
    return s

# Sports we care about → (Russian label, sport icon, league short tag)
# Keys discoverable via GET /sports — list may change as seasons end.
SPORT_KEYS: dict[str, dict[str, str]] = {
    # Football
    "soccer_uefa_champs_league": {"label": "Champions League", "icon": "⚽", "short": "UCL"},
    "soccer_uefa_europa_league": {"label": "Europa League", "icon": "⚽", "short": "UEL"},
    "soccer_epl":                {"label": "Premier League", "icon": "⚽", "short": "EPL"},
    "soccer_spain_la_liga":      {"label": "La Liga",         "icon": "⚽", "short": "LL"},
    "soccer_italy_serie_a":      {"label": "Serie A",         "icon": "⚽", "short": "SA"},
    "soccer_germany_bundesliga": {"label": "Bundesliga",      "icon": "⚽", "short": "BL"},
    "soccer_france_ligue_one":   {"label": "Ligue 1",         "icon": "⚽", "short": "L1"},
    "soccer_russia_premier_league": {"label": "Russian PL",   "icon": "⚽", "short": "RPL"},
    "soccer_uefa_europa_conference_league": {"label": "Conference League", "icon": "⚽", "short": "UECL"},
    "soccer_netherlands_eredivisie": {"label": "Eredivisie",  "icon": "⚽", "short": "ERE"},
    "soccer_portugal_primeira_liga": {"label": "Primeira Liga", "icon": "⚽", "short": "PPL"},
    "soccer_efl_champ":             {"label": "Championship",  "icon": "⚽", "short": "CHA"},
    "soccer_turkey_super_league":   {"label": "Süper Lig",     "icon": "⚽", "short": "TUR"},
    "soccer_belgium_first_div":     {"label": "Belgian Pro League", "icon": "⚽", "short": "BEL"},
    "soccer_brazil_campeonato":     {"label": "Brasileirão",   "icon": "⚽", "short": "BRA"},
    "soccer_usa_mls":               {"label": "MLS",           "icon": "⚽", "short": "MLS"},
    "soccer_spl":                   {"label": "Scottish Premiership", "icon": "⚽", "short": "SPL"},
    "soccer_argentina_primera_division": {"label": "Liga Profesional", "icon": "⚽", "short": "ARG"},
    "soccer_mexico_ligamx":         {"label": "Liga MX",       "icon": "⚽", "short": "MX"},
    "soccer_denmark_superliga":     {"label": "Danish Superliga", "icon": "⚽", "short": "DEN"},
    "soccer_sweden_allsvenskan":    {"label": "Allsvenskan",   "icon": "⚽", "short": "SWE"},
    "soccer_uefa_champs_league_qualification": {"label": "UCL Qualification", "icon": "⚽", "short": "UCLQ"},
    "soccer_austria_bundesliga":    {"label": "Austrian Bundesliga", "icon": "⚽", "short": "AUT"},
    "soccer_switzerland_superleague": {"label": "Swiss Super League", "icon": "⚽", "short": "SUI"},
    "soccer_greece_super_league":   {"label": "Greek Super League",  "icon": "⚽", "short": "GRE"},
    "soccer_poland_ekstraklasa":    {"label": "Ekstraklasa",         "icon": "⚽", "short": "POL"},
    "soccer_norway_eliteserien":    {"label": "Eliteserien",         "icon": "⚽", "short": "NOR"},
    "soccer_japan_j_league":        {"label": "J1 League",           "icon": "⚽", "short": "JPN"},
    "soccer_korea_kleague1":        {"label": "K League 1",          "icon": "⚽", "short": "KOR"},
    "soccer_germany_bundesliga2":   {"label": "2. Bundesliga",       "icon": "⚽", "short": "BL2"},
    "soccer_spain_segunda_division": {"label": "La Liga 2",          "icon": "⚽", "short": "LL2"},
    "soccer_england_league1":       {"label": "League One",          "icon": "⚽", "short": "EL1"},
    # Basketball
    "basketball_nba":            {"label": "NBA",             "icon": "🏀", "short": "NBA"},
    "basketball_euroleague":     {"label": "EuroLeague",      "icon": "🏀", "short": "EL"},
    # Hockey
    "icehockey_nhl":             {"label": "NHL",             "icon": "🏒", "short": "NHL"},
    # Tennis (sport_keys for tennis rotate per tournament — check /sports)
    "tennis_atp_french_open":    {"label": "Roland Garros (ATP)", "icon": "🎾", "short": "ATP"},
    "tennis_wta_french_open":    {"label": "Roland Garros (WTA)", "icon": "🎾", "short": "WTA"},
    # MMA
    "mma_mixed_martial_arts":    {"label": "UFC / MMA",       "icon": "🥊", "short": "UFC"},
    # American football
    "americanfootball_nfl":      {"label": "NFL",             "icon": "🏈", "short": "NFL"},
    # Baseball
    "baseball_mlb":              {"label": "MLB",             "icon": "⚾", "short": "MLB"},
}


class OddsAPIError(Exception):
    pass


class OddsAPIClient:
    def __init__(self, api_key: str | None = None, region: str = "eu", timeout: int = 20):
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise OddsAPIError(
                "ODDS_API_KEY required. Get a free key at https://the-odds-api.com/ "
                "then put it in pipeline/.env"
            )
        self.region = region
        self.timeout = timeout
        self.session = _build_session()
        self.quota: dict[str, str | None] = {"used": None, "remaining": None}

    def _get(self, path: str, params: dict[str, Any] | None = None, retries: int = 2) -> Any:
        """GET with retry + exponential backoff on rate limits and transient network errors."""
        params = {**(params or {}), "apiKey": self.api_key}
        url = f"{ODDS_API_BASE}{path}"
        last_err: Exception | None = None

        for attempt in range(retries + 1):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as e:
                last_err = e
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise OddsAPIError(f"Network error after {retries + 1} attempts: {e}") from e

            # Track quota (headers are present on every response)
            self.quota["used"] = r.headers.get("x-requests-used")
            self.quota["remaining"] = r.headers.get("x-requests-remaining")

            if r.status_code == 401:
                raise OddsAPIError("Invalid API key (401). Check ODDS_API_KEY in pipeline/.env")
            if r.status_code == 422:
                raise OddsAPIError(f"Bad request 422: {r.text}")
            if r.status_code == 429:
                if attempt < retries:
                    time.sleep(2 ** attempt)   # back off, then retry
                    continue
                raise OddsAPIError("Rate-limited (429). Slow down or upgrade tier.")
            if r.status_code >= 500:
                last_err = OddsAPIError(f"Server error {r.status_code}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise last_err

            r.raise_for_status()
            return r.json()

        raise OddsAPIError(f"Request failed: {last_err}")

    def list_sports(self, all_sports: bool = False) -> list[dict]:
        """List sports the API has odds for. Pass all=True to include out-of-season."""
        return self._get("/sports", {"all": "true" if all_sports else "false"})

    def get_odds(self, sport_key: str, markets: str = "h2h,totals,spreads") -> list[dict]:
        """
        Get odds for a sport.

        markets: comma-separated of h2h (1X2/ML), totals (over/under), spreads (handicaps)
        Returns list of events with bookmakers + markets + outcomes.
        Each event also costs 1 request (per market combination) — keep an eye on quota.
        """
        return self._get(
            f"/sports/{sport_key}/odds",
            {
                "regions": self.region,
                "markets": markets,
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            },
        )

    def get_scores(self, sport_key: str, days_from: int = 1) -> list[dict]:
        """Live + recent scores for a sport. daysFrom 0..3 (0=live only)."""
        return self._get(
            f"/sports/{sport_key}/scores",
            {"daysFrom": days_from, "dateFormat": "iso"},
        )

    def fetch_many(self, sport_keys: list[str], markets: str = "h2h,totals", delay: float = 0.2):
        """Fetch odds for many sports with small delay between calls."""
        out = {}
        for key in sport_keys:
            try:
                out[key] = self.get_odds(key, markets=markets)
            except OddsAPIError as e:
                print(f"  ⚠ {key}: {e}")
                out[key] = []
            except requests.RequestException as e:
                print(f"  ⚠ {key}: network error {e}")
                out[key] = []
            time.sleep(delay)
        return out
