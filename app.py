from flask import Flask, render_template, request, redirect, url_for, json, session

import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pandas as pd
from methods import get_players, get_infos_by_player_on_events, get_matches_by_player_on_event, get_results_by_event, get_event_by_id, file_upload_to_database

load_dotenv()

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = os.path.join('csv_files')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = os.getenv("APP_SECRET_KEY")

@app.get('/')
def get_main_data ():
    data = get_players()
    return render_template('index.html', data=data)

@app.get('/<name>')
def events_by_player (name):
    event_infos = get_infos_by_player_on_events(name)
    distinct_years = set(str(event['start'].year) for event in event_infos)
    years = sorted(list(distinct_years))
    return render_template('events_by_player.html', name=name, events=event_infos, years=years)

@app.get('/<name>/<id>')
def matches (name, id):
    data = get_matches_by_player_on_event(name, id)
    return render_template('matches.html', data=data)

@app.get('/event/<id>')
def event_result (id):
    event = get_event_by_id(id)
    results = get_results_by_event(id)
    return render_template('event_result.html', results=results, event=event)

@app.get('/upload')
def index():
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
