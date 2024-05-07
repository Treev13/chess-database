MATCHES_BY_PLAYER = '''
                    SELECT m.date as date, m.round as round,
                        w.fide_id as w_fide_id, w.name as w_name, w.nationality as w_nat,
                        EXTRACT(YEAR FROM (age(m.date, w.born)) ) as w_year,
                        EXTRACT(MONTH FROM (age(m.date, w.born)) ) as w_month,
                        b.fide_id as b_fide_id, b.name as b_name, b.nationality as b_nat,
                        EXTRACT(YEAR FROM (age(m.date, b.born)) ) as b_year,
                        EXTRACT(MONTH FROM (age(m.date, b.born)) ) as b_month,
                        m.result as result, e.event_name as event
                    FROM matches m
                    JOIN players_new w ON m.white = w.fide_id
                    JOIN players_new b ON m.black = b.fide_id
                    JOIN events e ON e.event_id = m.event
                    WHERE w.name like (%s) or b.name like (%s)
                    ORDER BY m.date;
                '''
MATCHES_BY_PLAYER_AND_EVENT = '''
                    SELECT m.date as date, m.round as round,
                        w.fide_id as w_fide_id, w.name as w_name, w.nationality as w_nat,
                        EXTRACT(YEAR FROM (age(m.date, w.born)) ) as w_year,
                        EXTRACT(MONTH FROM (age(m.date, w.born)) ) as w_month,
                        b.fide_id as b_fide_id, b.name as b_name, b.nationality as b_nat,
                        EXTRACT(YEAR FROM (age(m.date, b.born)) ) as b_year,
                        EXTRACT(MONTH FROM (age(m.date, b.born)) ) as b_month,
                        m.result as result
                    FROM matches m
                    JOIN players_new w ON m.white = w.fide_id
                    JOIN players_new b ON m.black = b.fide_id
                    WHERE (w.name like (%s) OR b.name like (%s))
                        AND m.event = (%s)
                    ORDER BY m.date;
                '''

RESULT_BY_EVENT = '''SELECT fide_id, player, nat, year, month, SUM(points) AS points, SUM(games) AS games
                    FROM(
                    SELECT p.fide_id AS fide_id, p.name AS player, p.nationality AS nat,
                        EXTRACT(YEAR FROM (age(e.start_date, p.born)) ) as year,
                        EXTRACT(MONTH FROM (age(start_date, p.born)) ) as month,
                        SUM(CASE WHEN result = '1-0' THEN 1 
                                 WHEN result = '½-½' THEN 0.5
                                 ELSE 0 END) AS points,
                        COUNT(*) AS games
                    FROM matches m
                    JOIN players_new p ON m.white = p.fide_id
                    JOIN events e ON m.event = e.event_id
                    WHERE event = (%s)
                    GROUP BY fide_id, player, nat, year, month
                    UNION ALL
                    SELECT p.fide_id AS fide_id, p.name AS player, p.nationality AS nat,
                        EXTRACT(YEAR FROM (age(start_date, p.born)) ) as year,
                        EXTRACT(MONTH FROM (age(start_date, p.born)) ) as month,
                        SUM(CASE WHEN result = '0-1' THEN 1
                                 WHEN result = '½-½' THEN 0.5
                                 ELSE 0 END) AS points,
                        COUNT(*) AS games
                    FROM matches m
                    JOIN players_new p ON m.black = p.fide_id
                    JOIN events e ON m.event = e.event_id
                    WHERE event = (%s)
                    GROUP BY fide_id, black, nat, year, month
                    ) AS sub
                    GROUP BY fide_id, player, nat, year, month
                    ORDER BY points DESC;
                    '''

PLAYERS = '''
            SELECT p.fide_id, p.name, p.nationality, mr.max_rating, p.born
            FROM players_new AS p
            JOIN (
                SELECT name, MAX(rating) AS max_rating
                FROM ratings
                GROUP BY name
            ) AS mr ON mr.name = p.name
            ORDER BY mr.max_rating DESC
            LIMIT 200;
        '''


EVENTS_BY_PLAYER = '''
                    SELECT distinct e.event_id as id, e.start_date as start, e.event_name as name, e.event_site as site
                    FROM matches m
                    JOIN events e on e.event_id = m.event
                    JOIN players_new w on w.fide_id = m.white
                    JOIN players_new b on b.fide_id = m.black
                    WHERE w.name = (%s) or b.name = (%s)
                    ORDER BY e.start_date
                    '''

EVENT_BY_ID = '''
                SELECT * FROM events
                WHERE event_id = (%s)
                '''

RESULT_BYY_EVENT = """
                    select tour.id as id, tour.name as name, site, tour.start_date, tour.end_date,
                        extract(year from age(tour.start_date,players.born)) as years,
                        extract(month from age(tour.start_date,players.born)) as months,
                        elo,
                        sum(result) as points,
                        count(*) as games,
                        round( avg(o_elo + 800 * result - 400) ) as performance
                    FROM matches
                        inner join tournaments tour on tour.short_name = matches.event
                        inner join players on players.name = matches.player
                        where players.id = ?
                        group by player,event,elo,years,months,tour.id, tour.name, site, start_date, end_date
                    order by start_date
                    """

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
                JOIN players_new w ON mo."White" = w.name
                JOIN players_new b ON mo."Black" = b.name
                JOIN events e ON mo."Event" = e.event_name;
                '''
