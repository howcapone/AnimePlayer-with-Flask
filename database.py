import sqlite3

def get_episodes():
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM episodes")
    episodes = cursor.fetchall()
    conn.close()
    return episodes

def get_episode(episode_id):
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM episodes WHERE id = ?", (episode_id,))
    episode = cursor.fetchone()
    conn.close()
    return episode