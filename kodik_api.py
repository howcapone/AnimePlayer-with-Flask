import requests
from flask import jsonify


class KodikAPI:
    def __init__(self):
        self.token = "45c53578f11ecfb74e31267b634cc6a8"
        self.base_url = "https://kodikapi.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'AnimeViewer/2.0'
        })

    def _make_request(self, endpoint, params=None):
        try:
            params = params or {}
            params['token'] = self.token
            response = self.session.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error: {str(e)}")
            return None

    def _process_item(self, item):
        """Полная обработка элемента с проверкой всех обязательных полей"""
        if not item:
            return None

        # Проверяем наличие обязательных полей
        anime_id = item.get('id')
        if not anime_id:
            return None

        material_data = item.get('material_data', {})

        # Получаем изображение
        image = (
                material_data.get('poster_url') or
                material_data.get('anime_poster_url') or
                item.get('screenshots', [None])[0] or
                '/static/img/placeholder.jpg'
        )

        # Проверяем наличие хотя бы одного эпизода
        episodes_count = item.get('episodes_count', 0)
        if episodes_count < 1:
            return None

        return {
            'id': anime_id,
            'title': material_data.get('title') or item.get('title', 'Без названия'),
            'shikimori_id': material_data.get('shikimori_id'),
            'image': image,
            'episodes_count': episodes_count,
            'year': item.get('year'),
            'type': item.get('type', 'anime')
        }

    def search_anime(self, query):
        params = {
            'title': query,
            'types': 'anime,anime-serial',
            'with_material_data': 'true',
            'with_episodes': 'true',
            'limit': 50
        }

        data = self._make_request('search', params)
        if not data or not data.get('results'):
            return []

        return [self._process_item(item) for item in data['results'] if self._process_item(item)]

    def get_popular(self):
        params = {
            'types': 'anime,anime-serial',
            'with_material_data': 'true',
            'with_episodes': 'true',
            'limit': 50,
            'sort': 'updated_at'
        }

        data = self._make_request('list', params)
        if not data or not data.get('results'):
            return []

        return [self._process_item(item) for item in data['results'] if self._process_item(item)]

    def get_episode(self, anime_id, episode):
        """Получение серии с проверкой работоспособности ссылки"""
        params = {
            'id': anime_id,
            'with_episodes': 'true',
            'with_material_data': 'true',
            'limit': 1
        }

        data = self._make_request('list', params)
        if not data or not data.get('results'):
            return None

        anime = data['results'][0]

        # Проверяем наличие эпизодов
        if anime.get('episodes_count', 0) < 1:
            return None

        # Получаем все доступные переводы
        translations = anime.get('translations', {})
        if not translations:
            return None

        # Выбираем первый доступный перевод
        translation_id = list(translations.keys())[0]
        translation = translations[translation_id]

        # Формируем ссылку по новому формату
        video_url = (
            f"https://kodik.info/serial/{anime_id}/"
            f"{translation.get('id')}/"
            f"{translation.get('hash') or 'default'}/"
            f"{episode}/720p"
        )

        material_data = anime.get('material_data', {})
        return {
            'url': video_url,
            'total': anime.get('episodes_count', 1),
            'title': material_data.get('title') or anime.get('title', 'Без названия'),
            'image': material_data.get('poster_url') or anime.get('screenshots', [None])[0]
        }

    def debug_api(self):
        try:
            test_data = self._make_request('list', {'limit': 1})
            if test_data and test_data.get('results'):
                return {
                    'status': 'working',
                    'example_item': test_data['results'][0]
                }
            return {'status': 'no_data'}
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def check_video_available(self, anime_id, episode=1):
        """Проверка доступности видео"""
        params = {
            'id': anime_id,
            'with_episodes': 'true',
            'limit': 1
        }

        try:
            response = self.session.head(
                f"https://kodik.info/serial/{anime_id}",
                allow_redirects=True,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False