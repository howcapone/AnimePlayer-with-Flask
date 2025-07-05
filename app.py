from flask import Flask, render_template, redirect, url_for
from database import get_episodes, get_episode

app = Flask(__name__)

@app.route('/')
def home():
    episode = get_episode(1)
    return render_template('index.html', video_file=episode[0])

@app.route("/choice")
def choice():
    episodes = get_episodes()
    return render_template('choice.html', episodes=episodes)

@app.route("/watch/<int:episode_id>")
def watch(episode_id):
    episode_path = get_episode(episode_id)[0]
    return render_template("index.html", video_file=episode_path)

if  __name__ == "__main__":
    app.run(debug=True)