from datetime import date, timedelta
from queries import INSERT_EVENT, ADD_MATCHES, IMPORT_CSV, EVENTS_BY_PLAYER, EVENT_BY_ID
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
                SELECT DISTINCT period
                FROM ratings
                ''')
    data = cursor.fetchall()
    dates = []
    for row in data:
        dates.append(row[0])
    return dates

def get_rating (period, fide_id, cursor):
    cursor.execute('''
                SELECT rating
                FROM ratings
                WHERE period = (%s)
                    AND fide_id = (%s)
                ''', (period, fide_id)) 
    data = cursor.fetchone() 
    return data[0]

def format_matches(name, id, data, cursor):
    mod_data = []
    periods = get_rating_list_periods(cursor)
    event = get_event_by_id(id, cursor)
    print(event)
    for tup in data:
        row = list(tup)
        period = check_latest_rating_list(row[0], periods)
        row.insert(5, get_rating(period, row[2], cursor))
        row.insert(11, get_rating(period, row[8], cursor))
        if row[3] != name:
            temp = (row[2:8])
            row[2:8] = row[8:14]
            row[8:14] = temp
            if row[14] == '1-0':
                row[14] = '0-1'
            elif row[14] == '0-1':
                row[14] = '1-0'
            row.append('b')
        else: row.append('w')
        row.append(calculate_fide(row[5], row[11], row[14]))
        mod_data.append(tuple(row))
    return mod_data



def calculate_fide(p_rat, o_rat, result):
    diff = (p_rat - o_rat)
    elvart = fide_calculator(diff)
    print(p_rat, o_rat, elvart)
    real = 0
    if result == '1-0': real = 1
    elif result == '0-1': real = 0
    else: real = 0.5
    return round(((real - elvart) * 10), 2)
    

def get_events_by_player(name, cursor):
    cursor.execute(EVENTS_BY_PLAYER, (name, name))
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