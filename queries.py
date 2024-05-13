PLAYERS = '''
            SELECT p.fide_id, p.name, mr.fed, mr.max_rating, p.born
            FROM players AS p
            JOIN (
                SELECT name, fed, MAX(rating) AS max_rating
                FROM ratings
                GROUP BY name, fed
            ) AS mr ON mr.name = p.name
            ORDER BY mr.max_rating DESC
            LIMIT 200;
        '''
MATCHES_BY_PLAYER = '''
                    SELECT m.date as date, m.round as round,
                        w.fide_id as w_fide_id, w.name as w_name,
                        EXTRACT(YEAR FROM (age(m.date, w.born)) ) as w_year,
                        EXTRACT(MONTH FROM (age(m.date, w.born)) ) as w_month,
                        b.fide_id as b_fide_id, b.name as b_name,
                        EXTRACT(YEAR FROM (age(m.date, b.born)) ) as b_year,
                        EXTRACT(MONTH FROM (age(m.date, b.born)) ) as b_month,
                        m.result as result, e.event_name as event
                    FROM matches m
                    JOIN players w ON m.white = w.fide_id
                    JOIN players b ON m.black = b.fide_id
                    JOIN events e ON e.event_id = m.event
                    WHERE w.name = (%s) or b.name = (%s)
                    ORDER BY m.date;
                '''
MATCHES_BY_PLAYER_ON_EVENT = '''
                    SELECT m.date as date, m.round as round,
                        w.fide_id as w_fide_id, w.name as w_name,
                        EXTRACT(YEAR FROM (age(m.date, w.born)) ) as w_year,
                        EXTRACT(MONTH FROM (age(m.date, w.born)) ) as w_month,
                        b.fide_id as b_fide_id, b.name as b_name,
                        EXTRACT(YEAR FROM (age(m.date, b.born)) ) as b_year,
                        EXTRACT(MONTH FROM (age(m.date, b.born)) ) as b_month,
                        m.result as result
                    FROM matches m
                    JOIN players w ON m.white = w.fide_id
                    JOIN players b ON m.black = b.fide_id
                    WHERE (w.name = (%s) OR b.name = (%s))
                        AND m.event = (%s)
                    ORDER BY m.round;
                '''
RESULT_BY_EVENT = '''
                    SELECT fide_id, player, year, month, SUM(points) AS points, SUM(games) AS games
                    FROM(
                        SELECT p.fide_id AS fide_id, p.name AS player,
                            EXTRACT(YEAR FROM (age(start_date, p.born)) ) as year,
                            EXTRACT(MONTH FROM (age(start_date, p.born)) ) as month,
                            SUM(CASE WHEN result = '1-0' THEN 1 
                                 WHEN result = '½-½' THEN 0.5
                                 ELSE 0 END) AS points,
                            COUNT(*) AS games
                        FROM matches m
                        JOIN players p ON m.white = p.fide_id
                        JOIN events e ON m.event = e.event_id
                        WHERE event = (%s)
                        GROUP BY fide_id, player, year, month, start_date

                        UNION ALL

                        SELECT p.fide_id AS fide_id, p.name AS player,
                            EXTRACT(YEAR FROM (age(start_date, p.born)) ) as year,
                            EXTRACT(MONTH FROM (age(start_date, p.born)) ) as month,
                            SUM(CASE WHEN result = '0-1' THEN 1
                                 WHEN result = '½-½' THEN 0.5
                                 ELSE 0 END) AS points,
                            COUNT(*) AS games
                        FROM matches m
                        JOIN players p ON m.black = p.fide_id
                        JOIN events e ON m.event = e.event_id
                        WHERE event = (%s)
                        GROUP BY fide_id, black, year, month, start_date
                        ) AS sub
                    GROUP BY fide_id, player, year, month
                    ORDER BY points DESC;
                    '''
EVENTS_BY_PLAYER = '''
                    SELECT distinct e.event_id as id, e.start_date as start, e.event_name as name, e.event_site as site
                    FROM matches m
                    JOIN events e on e.event_id = m.event
                    JOIN players w on w.fide_id = m.white
                    JOIN players b on b.fide_id = m.black
                    WHERE w.name = (%s) or b.name = (%s)
                    ORDER BY e.start_date
                    '''
EVENT_BY_ID = '''
                SELECT * FROM events
                WHERE event_id = (%s)
                '''
INFO_FROM_RATINGS = '''
                    SELECT rating, fed
                    FROM ratings
                    WHERE period = (%s)
                        AND fide_id = (%s)
                    '''
DISTINCT_PERIODS = '''
                SELECT DISTINCT period as period
                FROM ratings
                '''
IMPORT_CSV = '''
            TRUNCATE matches_old;
            COPY matches_old
            FROM stdin
            DELIMITER ','
            CSV HEADER;
        '''
INSERT_EVENT = '''
                INSERT INTO events (event_name, event_site, start_date, end_date, players_number)
                SELECT "Event", "Site", MIN("Date"), MAX("Date"),
                count(distinct "White")
                FROM matches_old
                WHERE NOT EXISTS (
                    SELECT * FROM events
                    WHERE events.event_name = matches_old."Event"
                    )
                GROUP BY "Event", "Site";
                '''
ADD_MATCHES = '''
                INSERT INTO matches (date, event, round, white, black, result, moves, eco)
                SELECT 
                    mo."Date",
                    e.event_id,
                    mo."Round",
                    w.fide_id,
                    b.fide_id,
                    mo."Res",
                    mo."# Mvs",
                    mo."ECO"
                FROM matches_old mo
                LEFT JOIN players w ON mo."White" = w.name
                LEFT JOIN players b ON mo."Black" = b.name
                JOIN events e ON mo."Event" = e.event_name;
                '''
