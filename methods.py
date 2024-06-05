from datetime import timedelta, datetime
from queries import *
from fide_calculator import fide_calculator
from database import connection
from psycopg2.extras import RealDictCursor, RealDictRow
from dateutil.relativedelta import relativedelta

def get_list(list_name):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(eval(list_name)) 
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_rating_list(period):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(RATINGS, (period,)) 
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_player_by_name(name):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(PLAYER_BY_NAME, (name,)) 
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data[0]

def get_ratings_by_player(name):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(RATINGS_BY_PLAYER, (name,)) 
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_matches_by_player_on_event(name, id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(MATCHES_BY_PLAYER_ON_EVENT, (name, name, id)) 
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    formatted_matches = format_matches(name, data)
    return add_infos_to_matches(id, formatted_matches)

def get_infos_by_player_on_events(name, year):
    infos = []
    events = get_events_by_player(name, year)
    for event in events:
        matches_on_event = get_matches_by_player_on_event(name, event['id'])
        stats_on_event = calculate_stats(matches_on_event)
        infos.append({'id': event['id'],
                        'start': event['start'],
                        'name': event['name'],
                        'site': event['site'],
                        'points': stats_on_event['points'],
                        'matches': stats_on_event['matches']})
    return infos

def check_latest_rating_list(match_date, periods):
    minimum = timedelta.max
    final_date = periods[0]['period']
    for period in periods:
        if (match_date - period['period']) < minimum and (match_date - period['period']) >= timedelta(0):
            minimum = match_date - period['period']
            final_date = period['period']
    return final_date

def get_rating_list_periods():
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(DISTINCT_PERIODS)
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_rating (period, fide_id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(INFO_FROM_RATINGS, (period, fide_id)) 
            rating = cursor.fetchone()
            connection.commit()
        cursor.close()
    return rating if rating is not None else RealDictRow({'rating': 2000, 'fed': 'no'})

def add_infos_to_matches(id, data):
    final_data = dict()
    final_data['matches'] = []
    event = get_event_by_id(id)
    periods = get_rating_list_periods()
    period = check_latest_rating_list(event['start_date'], periods)
    final_data['event_id'] = event['event_id']
    final_data['event_name'] = event['event_name']
    final_data['p_name'] = data[0]['w_name']
    final_data['p_year'] = data[0]['w_year']
    final_data['p_month'] = data[0]['w_month']
    player_id = data[0]['w_fide_id']
    final_data['p_rating'] = (get_rating(period, player_id))['rating']
    final_data['p_nat'] = (get_rating(period, player_id))['fed']
    for row in data:
        match = dict()
        match['date'] = row['date']
        match['round'] = row['round']
        match['color'] = row['color']
        match['o_name'] = row['b_name']
        data_from_ratings_for_black = (get_rating(period, row['b_fide_id']))
        match['o_rating'] = data_from_ratings_for_black['rating']
        match['o_nat'] = data_from_ratings_for_black['fed']
        match['o_year'] = row['b_year']
        match['o_month'] = row['b_month']
        match['result'] = row['result']
        match['rat_change'] = (calculate_fide(final_data['p_rating'], match['o_rating'], row['result']))
        final_data['matches'].append(match)
    return final_data

def format_matches(name, data):
    mod_data = []
    for row in data:
        if row['w_name'] != name:
            row['w_fide_id'], row['b_fide_id'] = row['b_fide_id'], row['w_fide_id']
            row['w_name'], row['b_name'] = row['b_name'], row['w_name']
            row['w_year'], row['b_year'] = row['b_year'], row['w_year']
            row['w_month'], row['b_month'] = row['b_month'], row['w_month']
            
            if row['result'] == '1-0':
                row['result'] = '0-1'
            elif row['result'] == '0-1':
                row['result'] = '1-0'
            row['color'] = ('b')
        else: row['color'] = ('w')
        
        mod_data.append(row)
    return mod_data

def calculate_stats(event_by_player):
    points = 0
    for match in event_by_player['matches']:
        if match['result'] == '1-0': points += 1
        elif match['result'] == '½-½': points += 0.5
    return {'points': points, 'matches': len(event_by_player['matches'])}

def get_results_by_event(id):
    periods = get_rating_list_periods()
    event = get_event_by_id(id)
    period = check_latest_rating_list(event['start_date'], periods)
    result = calculate_result(id)
    for row in result:
        data_from_ratings = get_rating(period, row['fide_id'])
        row['rating'] = data_from_ratings['rating']
        row['nat'] = data_from_ratings['fed']
    return result

def calculate_result(id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(RESULT_BY_EVENT, (id, id))
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data
    
def calculate_fide(p_rat, o_rat, result):
    diff = (p_rat - o_rat)
    if p_rat == 2000 or o_rat == 2000:
        return 0, 0
    else: expected = fide_calculator(diff)
    if result == '1-0': real = 1
    elif result == '0-1': real = 0
    else: real = 0.5
    return round(((real - expected) * 10), 2), round(((real - expected) * 10), 2)*-1
    
def get_events_by_player(name, year):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(EVENTS_BY_PLAYER, (name, name, year))
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_event_years_by_player(name):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(EVENT_YEARS_BY_PLAYER, (name, name))
            data = cursor.fetchall()
            connection.commit()
        cursor.close()
    return data

def get_event_by_id(id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(EVENT_BY_ID, (id,)) 
            event = cursor.fetchone()
            connection.commit()
        cursor.close()
    return event

def get_matches_by_event(event):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(MATCHES_BY_EVENT, (event,)) 
            matches = cursor.fetchall()
            connection.commit()
        cursor.close()
    return matches

def file_upload_to_database(session):
    with connection:
        with connection.cursor() as cursor:
            
            with open(session['uploaded_data_file_path'], 'r') as f:
                cursor.copy_expert(sql=IMPORT_CSV, file=f)
                
                connection.commit()
            add_event(cursor)
            load_matches(cursor)
            connection.commit()
        cursor.close()

def add_event(cursor):
    cursor.execute(INSERT_EVENT)

def load_matches(cursor):
    cursor.execute(ADD_MATCHES)

def get_players_on_event_with_rating(id):
    periods = get_rating_list_periods()
    event = get_event_by_id(id)
    period = check_latest_rating_list(event['start_date'], periods)
    players = get_players_on_event(id)
    players_with_rating = {}
    for player in players:
        info = get_rating(period, player['id'])
        birthdate = player['born']
        start = event['start_date']
        year = relativedelta(start, birthdate).years
        month = relativedelta(start, birthdate).months
        players_with_rating[player['id']] = (player['name'], info['rating'], info['fed'], year, month)
    return players_with_rating


def get_players_on_event(id):
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(PLAYERS_ON_EVENT, (id, id)) 
            players = cursor.fetchall()
            connection.commit()
        cursor.close()
    return players


def calculate_player_statistics(matches, players):
    player_stats = {}
    for player_id, (name, rating, fed, year, month) in players.items():
        player_stats[str(player_id)] = {
            'name': name,
            'rating': rating,
            'fed': fed,
            'year': year,
            'month': month,
            'matches': 0,
            'points': 0,
            'change': 0
        }

    for match in matches:
        white = match['white']
        black = match['black']
        result = match['result']
        white_rating = players[white][1]
        black_rating = players[black][1]

        white_points, black_points = _calculate_points(result)
        white_change, black_change = calculate_fide(white_rating, black_rating, result)

        player_stats[str(white)]["matches"] += 1
        player_stats[str(white)]["points"] += white_points
        player_stats[str(white)]["change"] += white_change

        player_stats[str(black)]["matches"] += 1
        player_stats[str(black)]["points"] += black_points
        player_stats[str(black)]["change"] += black_change

    return player_stats

def _calculate_points(result):
    if result == '1-0':
        return 1, 0
    elif result == '0-1':
        return 0, 1
    elif result == '½-½':
        return 0.5, 0.5
    else:
        return 0, 0

