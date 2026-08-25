import time
from collections import deque

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
    """Current fantasy week from Sleeper's NFL state, or None when out of season.

    Sleeper's week field counts preseason weeks too, so it's only trusted
    during the regular season and playoffs; callers decide the out-of-season
    fallback (e.g. last week with local data).
    """
    if state.get('season_type') not in ('regular', 'post'):
        return None
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
        self._call_times = deque()

    MAX_CALLS_PER_SECOND = 10

    def _rate_limit(self):
        now = time.monotonic()
        while self._call_times and now - self._call_times[0] > 1:
            self._call_times.popleft()
        if len(self._call_times) >= self.MAX_CALLS_PER_SECOND:
            sleep_time = 1 - (now - self._call_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            now = time.monotonic()
            while self._call_times and now - self._call_times[0] > 1:
                self._call_times.popleft()
        self._call_times.append(now)

    def getPlayers(self, **kwargs):
        playerUrl = f'{BASE_URL}/players/nfl?active=true'

        self._rate_limit()
        response = self.session.get(playerUrl, params=None, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def getDraftPicks(self, draft_id, **kwargs):
        draftPicksUrl = f'https://api.sleeper.app/v1/draft/{draft_id}/picks'

        self._rate_limit()
        response = self.session.get(draftPicksUrl, params=None, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def getWeeklyPlayerPerformance(self, player_id, week, season, **kwargs):
        if week is None or season is None:
            print('Need season and week')
            return
        performanceUrl = f'https://api.sleeper.app/stats/nfl/player/{player_id}?season_type=regular&season={season}&week={week}'

        self._rate_limit()
        response = self.session.get(performanceUrl, params=None, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def _url(self, endpoint):
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, params=None, **kwargs):
        self._rate_limit()
        response = self.session.get(self._url(endpoint), params=params, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()
