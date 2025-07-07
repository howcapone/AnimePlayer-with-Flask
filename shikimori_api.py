import requests
from urllib.parse import urlencode
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShikimoriAPI:
    def __init__(self, app=None):
        self.client_id = 'pg6I9J8InwM1e75AS4dGG9LjILOzjGbeXv12Micx0KA'
        self.client_secret = '6WZ_YPUsyg5JxLIFj1bZ5EAOF9uH1Y5g4_KiRnHPOFA'
        self.base_url = 'https://shikimori.one'
        self.api_url = f"{self.base_url}/api"
        self.redirect_uri = 'http://localhost:5001/auth/callback'
        self.timeout = 15
        self.session = self._create_session()

    def _create_session(self):
        """Создаем сессию с повторными попытками"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update({
            'User-Agent': 'AnimeViewer/2.0',
            'Accept': 'application/json'
        })

        return session

    def get_auth_url(self):
        """Генерация URL для авторизации"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'user_rates'
        }
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    def get_token(self, code):
        """Получение токена доступа"""
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        try:
            response = self.session.post(
                f"{self.base_url}/oauth/token",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Token request failed: {str(e)}")
            return None

    def get_anime_list(self, search=None, page=1, limit=50):
        """Получение списка аниме"""
        params = {
            'page': page,
            'limit': limit,
            'order': 'popularity',
            'kind': 'tv'
        }

        if search:
            params['search'] = search

        try:
            response = self.session.get(
                f"{self.api_url}/animes",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._process_anime_list(response.json())
        except Exception as e:
            logger.error(f"Anime list request failed: {str(e)}")
            return []

    def get_anime(self, anime_id):
        """Получение информации об аниме"""
        try:
            response = self.session.get(
                f"{self.api_url}/animes/{anime_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return self._process_anime(response.json())
        except Exception as e:
            logger.error(f"Anime request failed: {str(e)}")
            return None

    def _process_anime_list(self, anime_list):
        """Обработка списка аниме"""
        return [self._process_anime(a) for a in anime_list if a]

    def _process_anime(self, anime):
        """Обработка одного аниме"""
        image_url = f"{self.base_url}{anime['image']['original']}" if anime.get('image') else None

        return {
            'id': anime.get('id'),
            'title': anime.get('russian') or anime.get('name'),
            'original_title': anime.get('name'),
            'image': image_url,
            'description': anime.get('description') or "Описание отсутствует",
            'episodes': anime.get('episodes', 0),
            'episodes_aired': anime.get('episodes_aired', 0),
            'kind': anime.get('kind'),
            'status': anime.get('status'),
            'year': anime.get('aired_on', '')[:4] if anime.get('aired_on') else None,
            'score': anime.get('score'),
            'genres': [g['russian'] for g in anime.get('genres', [])],
            'shikimori_url': f"{self.base_url}{anime.get('url')}" if anime.get('url') else None
        }