import requests


class ApiClient:
    def __init__(self, week=1, use_old=False, headers=None, timeout=10):
        self.week = week
        self.league_id = '1266106052584165376' if use_old else '1389725835237269504'
        self.base_url = 'https://api.sleeper.app/v1/league/'+ self.league_id
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)
        self.timeout = timeout

    def getPlayers(self, **kwargs):
        playerUrl = 'https://api.sleeper.app/v1/players/nfl?active=true'

        response = self.session.get(playerUrl, params=None, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def _url(self, endpoint):
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, params=None, **kwargs):
        response = self.session.get(self._url(endpoint), params=params, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()
