import requests

BASE_URL = 'https://api.sleeper.app/v1'


def _get(url, timeout=10):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_nfl_state(timeout=10):
    return _get(f'{BASE_URL}/state/nfl', timeout=timeout)


def get_user_info(username_or_id, timeout=10):
    return _get(f'{BASE_URL}/user/{username_or_id}', timeout=timeout)


def get_user_leagues(user_id, season, timeout=10):
    return _get(f'{BASE_URL}/user/{user_id}/leagues/nfl/{season}', timeout=timeout)


def get_league_info(league_id, timeout=10):
    return _get(f'{BASE_URL}/league/{league_id}', timeout=timeout)


def infer_week(state):
    # Sleeper's week field counts preseason weeks too; only trust it in-season
    if state.get('season_type') not in ('regular', 'post'):
        return 1
    try:
        return max(int(state.get('week') or 1), 1)
    except (TypeError, ValueError):
        return 1


class ApiClient:
    def __init__(self, league_id, week=1, headers=None, timeout=10):
        self.week = week
        self.league_id = league_id
        self.base_url = f'{BASE_URL}/league/{self.league_id}'
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        self.timeout = timeout

    def getPlayers(self, **kwargs):
        playerUrl = f'{BASE_URL}/players/nfl?active=true'

        response = self.session.get(playerUrl, params=None, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def _url(self, endpoint):
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, params=None, **kwargs):
        response = self.session.get(self._url(endpoint), params=params, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()
