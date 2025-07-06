from flask import Flask, render_template, request, redirect, url_for, jsonify
from kodik_api import KodikAPI

app = Flask(__name__)
app.secret_key = 'super-secret-key-2'
app.config['DEBUG'] = True

api = KodikAPI()


@app.route('/')
def home():
    return redirect(url_for('catalog'))


@app.route('/player')
def player():
    try:
        anime_id = request.args.get('anime_id')
        episode = request.args.get('episode', default=1, type=int)

        if not anime_id:
            return redirect(url_for('catalog'))

        # Сначала проверяем доступность аниме
        if not api.check_video_available(anime_id, episode):
            return render_template(
                'error.html',
                message="Это аниме временно недоступно",
                back_url=url_for('catalog'),
                debug_info={
                    'anime_id': anime_id,
                    'episode': episode,
                    'api_status': api.debug_api()
                }
            ), 404

        video_data = api.get_episode(anime_id, episode)
        if not video_data:
            return render_template(
                'error.html',
                message="Не удалось загрузить видео",
                back_url=url_for('catalog'),
                debug_info={
                    'anime_id': anime_id,
                    'episode': episode,
                    'api_status': api.debug_api()
                }
            ), 404

        return render_template(
            'player.html',
            anime={
                'title': video_data['title'],
                'image': video_data['image']
            },
            anime_id=anime_id,
            current_episode=episode,
            video_url=video_data['url'],
            total_episodes=video_data['total']
        )
    except Exception as e:
        app.logger.error(f"Player error: {str(e)}")
        return render_template(
            'error.html',
            message="Ошибка загрузки плеера",
            back_url=url_for('catalog'),
            debug_info={'error': str(e)}
        ), 500


@app.route('/catalog')
def catalog():
    try:
        search_query = request.args.get('search', '').strip()

        if search_query:
            anime_list = api.search_anime(search_query)
        else:
            anime_list = api.get_popular()

        # Фильтруем None и аниме без ID
        anime_list = [a for a in anime_list if a and a.get('id')]

        if not anime_list:
            return render_template(
                'error.html',
                message="Ничего не найдено" if search_query else "Нет доступных аниме",
                back_url=url_for('catalog'),
                debug_info={
                    'search_query': search_query,
                    'api_status': api.debug_api(),
                    'test_data': api._make_request('list', {'limit': 3})
                }
            ), 404

        # Добавим отладочную информацию
        debug_first_item = None
        if anime_list and len(anime_list) > 0:
            debug_first_item = {
                'id': anime_list[0].get('id'),
                'title': anime_list[0].get('title'),
                'episodes': anime_list[0].get('episodes_count')
            }

        return render_template(
            'catalog.html',
            anime_list=anime_list,
            search_query=search_query,
            debug_first_item=debug_first_item
        )
    except Exception as e:
        app.logger.error(f"Catalog error: {str(e)}")
        return render_template(
            'error.html',
            message="Ошибка загрузки каталога",
            back_url=url_for('catalog'),
            debug_info={'error': str(e)}
        ), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)