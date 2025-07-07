from flask import Flask, render_template, request, redirect, url_for, session
from shikimori_api import ShikimoriAPI
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Генерация случайного секретного ключа
app.config['DEBUG'] = True

shikimori = ShikimoriAPI(app)


@app.route('/')
def home():
    if not session.get('shikimori_token'):
        return redirect(url_for('auth'))
    return redirect(url_for('catalog'))


@app.route('/auth')
def auth():
    return redirect(shikimori.get_auth_url())


@app.route('/auth/callback')
def auth_callback():
    error = request.args.get('error')
    if error:
        logger.error(f"Auth error: {error}")
        return render_template('error.html',
                               message="Ошибка авторизации",
                               back_url=url_for('home'),
                               debug_info={
                                   'error': error,
                                   'suggestion': 'Попробуйте авторизоваться снова'
                               })

    code = request.args.get('code')
    if not code:
        logger.error("No authorization code received")
        return render_template('error.html',
                               message="Не получен код авторизации",
                               back_url=url_for('home'))

    token_data = shikimori.get_token(code)
    if not token_data:
        logger.error("Failed to get token")
        return render_template('error.html',
                               message="Не удалось получить токен",
                               back_url=url_for('home'),
                               debug_info={
                                   'suggestion': 'Сервер Shikimori может быть недоступен. Попробуйте позже'
                               })

    session['shikimori_token'] = token_data['access_token']
    session['shikimori_refresh_token'] = token_data.get('refresh_token')
    logger.info("Successfully authenticated")
    return redirect(url_for('catalog'))


@app.route('/catalog')
def catalog():
    if not session.get('shikimori_token'):
        return redirect(url_for('auth'))

    try:
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)

        anime_list = shikimori.get_anime_list(search=search_query, page=page)

        if not isinstance(anime_list, list):
            raise ValueError("Некорректный формат данных от API")

        return render_template(
            'catalog.html',
            anime_list=anime_list,
            search_query=search_query,
            current_page=page
        )
    except Exception as e:
        logger.error(f"Catalog error: {str(e)}")
        return render_template(
            'error.html',
            message="Ошибка загрузки каталога",
            back_url=url_for('catalog'),
            debug_info={
                'error': str(e),
                'suggestion': 'Попробуйте обновить страницу или зайти позже'
            }
        )


@app.route('/anime/<int:anime_id>')
def anime_details(anime_id):
    if not session.get('shikimori_token'):
        return redirect(url_for('auth'))

    try:
        anime = shikimori.get_anime(anime_id)
        if not anime:
            raise ValueError("Аниме не найдено")

        return render_template(
            'anime.html',
            anime=anime
        )
    except Exception as e:
        logger.error(f"Anime details error: {str(e)}")
        return render_template(
            'error.html',
            message="Ошибка загрузки информации об аниме",
            back_url=url_for('catalog'),
            debug_info={
                'error': str(e),
                'suggestion': 'Попробуйте выбрать другое аниме'
            }
        )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)