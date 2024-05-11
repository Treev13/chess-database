from flask import Flask, render_template, request, redirect, url_for, json, session

import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from methods import get_matches_by_player_on_event, file_upload_to_database, get_results_by_event, get_event_by_id, get_infos_by_player_on_events
from queries import PLAYERS, MATCHES_BY_PLAYER_AND_EVENT

load_dotenv()

ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = os.path.join('csv_files')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = 'This is your secret key to utilize session in Flask'

connection = psycopg2.connect(database=os.getenv("DATABASE"),
                              user=os.getenv("USER"),
                              password=os.getenv("PASSWORD"),
                              host=os.getenv("HOST"),
                              port=os.getenv("PORT"))

@app.get('/')
def get_players ():
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(PLAYERS) 
            data = cursor.fetchall()
    return render_template('index.html', data=data)

@app.get('/<name>')
def events_by_player (name):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            event_infos = get_infos_by_player_on_events(name, cursor)

    return render_template('events_by_player.html', events=event_infos)

@app.get('/event/<id>')
def event_result (id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            event = get_event_by_id(id, cursor)
            results = get_results_by_event(id, cursor)
    return render_template('event_result.html', results=results, event=event)

@app.get('/<name>/<id>')
def matches (name, id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            data = get_matches_by_player_on_event(name, id, cursor)
    return render_template('matches.html', data=data)

@app.get('/upload')
def index():
    return render_template('upload.html')

@app.post('/upload')
def upload_file():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)

    session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if uploaded_file.filename != '':
        #checked_file = check_csv_file(uploaded_file)
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_upload_to_database(connection, session)
    return render_template('uploaded.html')

@app.get('/show_data')
def show():
    # Uploaded File Path
    data_file_path = session.get('uploaded_data_file_path', None)
    # read csv
    uploaded_df = pd.read_csv(data_file_path, encoding='unicode_escape')
    # Converting to html Table
    uploaded_df_html = uploaded_df.to_html()
    return render_template('show_data.html', data_var=uploaded_df_html)

if __name__ == '__main__':
    app.run(debug=True)
