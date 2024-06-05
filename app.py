from flask import Flask, render_template, request, redirect, url_for, json, session

import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pandas as pd
from methods import *

load_dotenv()

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = os.path.join('csv_files')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = os.getenv("APP_SECRET_KEY")

@app.get('/')
def index ():
    return render_template('index.html')

@app.get('/players')
def players ():
    newest = get_list('PLAYERS')
    all_time = get_list('PLAYERS_ALL_TIME')
    return render_template('players.html', all_time_data=all_time, newest_data=newest)

@app.get('/events')
def events ():
    data = get_list('EVENTS')
    return render_template('events.html', data=data)

@app.get('/ratings')
def ratings ():
    periods = get_rating_list_periods()
    return render_template('ratings.html', periods=periods)

@app.post("/ratings")
def test():
    select = request.form.get('ratings')
    data = get_rating_list(select)
    periods = get_rating_list_periods()
    return render_template('ratings.html', data=data, periods=periods)

@app.get('/<name>')
def player (name):
    player_info = get_player_by_name(name)
    years = get_event_years_by_player(name)
    ratings_data = get_ratings_by_player(name)
    periods = [row['period'].strftime('%Y-%m') for row in ratings_data]
    ratings = [row['rating'] for row in ratings_data]
    return render_template('player.html', name=name, infos=player_info, ratings=ratings, periods=periods, years=years)

@app.get('/event/<name>/<year>')
def events_by_player (name, year):
    event_infos = get_infos_by_player_on_events(name, year)
    return render_template('events_by_player.html', name=name, year=year, events=event_infos)

@app.get('/<name>/<id>')
def matches (name, id):
    data = get_matches_by_player_on_event(name, id)
    return render_template('matches.html', data=data)

@app.get('/event/<id>')
def event_result (id):
    event = get_event_by_id(id)
    matches = get_matches_by_event(id)
    players = get_players_on_event_with_rating(id)
    infos = calculate_player_statistics(matches, players)
    #results = get_results_by_event(id)
    return render_template('event_result.html', results=infos, event=event)

@app.get('/upload')
def upload():
    return render_template('upload.html')

@app.post('/upload')
def upload_file():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if uploaded_file.filename != '':
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_upload_to_database(session)
    return render_template('uploaded.html')

@app.get('/show_data')
def show():
    data_file_path = session.get('uploaded_data_file_path', None)
    uploaded_df = pd.read_csv(data_file_path, encoding='unicode_escape')
    uploaded_df_html = uploaded_df.to_html()
    return render_template('show_data.html', data_var=uploaded_df_html)

if __name__ == '__main__':
    app.run(debug=True)
