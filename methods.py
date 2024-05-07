from datetime import timedelta
from queries import INSERT_EVENT, ADD_MATCHES, IMPORT_CSV, EVENTS_BY_PLAYER, EVENT_BY_ID, RESULT_BY_EVENT
from fide_calculator import fide_calculator

def check_latest_rating_list(match_date, periods):
    
    minimum = timedelta.max
    final_date = periods[0]
    for day in periods:
        if (match_date - day) < minimum and (match_date - day) >= timedelta(0):
            minimum = match_date - day
            final_date = day

    return final_date

def get_rating_list_periods(cursor):
    cursor.execute('''
                SELECT DISTINCT period as period
                FROM ratings
                ''')
    data = cursor.fetchall()
    dates = []
    for row in data:
        dates.append(row['period'])
    return dates

def get_rating (period, fide_id, cursor):
    cursor.execute('''
                SELECT rating
                FROM ratings
                WHERE period = (%s)
                    AND fide_id = (%s)
                ''', (period, fide_id)) 
    rating = cursor.fetchone()
    return rating['rating']

def format_matches(name, id, data, cursor):
    mod_data = []
    periods = get_rating_list_periods(cursor)
    event = get_event_by_id(id, cursor)
    period = check_latest_rating_list(event['start_date'], periods)
    for row in data:
        row['w_rating'] = (get_rating(period, row['w_fide_id'], cursor))
        row['b_rating'] = (get_rating(period, row['b_fide_id'], cursor))
        if row['w_name'] != name:

            row['w_fide_id'], row['b_fide_id'] = row['b_fide_id'], row['w_fide_id']
            row['w_name'], row['b_name'] = row['b_name'], row['w_name']
            row['w_nat'], row['b_nat'] = row['b_nat'], row['w_nat']
            row['w_rating'], row['b_rating'] = row['b_rating'], row['w_rating']
            row['w_year'], row['b_year'] = row['b_year'], row['w_year']
            row['w_month'], row['b_month'] = row['b_month'], row['w_month']
            
            if row['result'] == '1-0':
                row['result'] = '0-1'
            elif row['result'] == '0-1':
                row['result'] = '1-0'
            row['color'] = ('b')
            
        else: row['color'] = ('w')
        row['rat_change'] = (calculate_fide(row['w_rating'], row['b_rating'], row['result']))
        row['event_id'] = event['event_id']
        row['event_name'] = event['event_name']
        mod_data.append(row)
    return mod_data

def get_results_by_event(id, cursor):
    result = []
    event = get_event_by_id(id, cursor)
    result = calculate_result(id, cursor)
    return result

def calculate_result(id, cursor):
    cursor.execute(RESULT_BY_EVENT, (id, id))
    return cursor.fetchall()
    

def calculate_fide(p_rat, o_rat, result):
    diff = (p_rat - o_rat)
    elvart = fide_calculator(diff)
    if result == '1-0': real = 1
    elif result == '0-1': real = 0
    else: real = 0.5
    return round(((real - elvart) * 10), 2)
    

def get_events_by_player(name, cursor):
    cursor.execute(EVENTS_BY_PLAYER, (name, name))
    return cursor.fetchall()

def get_matches_by_event(id, cursor):
    cursor.execute(MATCHES_BY_EVENT, (id,))
    return cursor.fetchall()

def get_event_by_id(id, cursor):
    cursor.execute(EVENT_BY_ID, (id,))
    return cursor.fetchone()

def add_event(cursor):
    cursor.execute(INSERT_EVENT)

def load_matches(cursor):
    cursor.execute(ADD_MATCHES)

def file_upload_to_database(connection, session):
    with connection:
        with connection.cursor() as cursor:
            
            with open(session['uploaded_data_file_path'], 'r') as f:
                cursor.copy_expert(sql=IMPORT_CSV, file=f)
                
                connection.commit()
            add_event(cursor)
            load_matches(cursor)
            cursor.close()