from typing import Any

from psycopg2.extras import RealDictCursor

from app.database import get_connection
from app.models import FlightSearchRequest


def insert_airports_to_db(airports: list[tuple[str, str, str]] ) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.executemany("""
        INSERT INTO airports (code, city, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (code) DO UPDATE
        SET city = EXCLUDED.city,
            country = EXCLUDED.country,
            datemodified = NOW()
    """, airports)

    connection.commit()
    airports_inserted = cursor.rowcount
    cursor.close()
    connection.close()

    return airports_inserted


def get_all_airports_db(code_only: bool, from_poland: bool) -> None | list[str] | list[dict[str, str]]:
    connection = get_connection()
    cursor = connection.cursor()

    if code_only and from_poland:
        cursor.execute("SELECT code FROM airports WHERE country = 'Poland';")
    elif (not code_only) and from_poland:
        cursor.execute("SELECT code, city FROM airports WHERE country = 'Poland';")
    elif code_only and (not from_poland):
        cursor.execute("SELECT code FROM airports WHERE country != 'Poland';")
    else:
        cursor.execute("SELECT code, city FROM airports WHERE country != 'Poland';")

    airports = cursor.fetchall()
    cursor.close()
    connection.close()

    if not airports:
        return None
    if code_only:
        return [airport[0] for airport in airports]
    return [{"code": airport[0], "city": airport[1]} for airport in airports]


def insert_routes_to_db(routes: list[tuple[str, str, str]] ) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
            DELETE FROM routes 
            WHERE airline = 'FR'
            AND (originairport, destinationairport) NOT IN %s
        """, (tuple([(r[1], r[2]) for r in routes]),))

    cursor.executemany("""
            INSERT INTO routes (airline, originairport, destinationairport)
            VALUES (%s, %s, %s)
            ON CONFLICT (Airline, OriginAirport, DestinationAirport) DO UPDATE
            SET datemodified = NOW()
        """, routes)

    connection.commit()
    routes_inserted = cursor.rowcount
    cursor.close()
    connection.close()

    return routes_inserted


def get_all_routes_db() -> list[tuple[int,str,str]] | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT routeid, originairport, destinationairport FROM routes;")

    routes = cursor.fetchall()
    cursor.close()
    connection.close()

    if routes:
        return routes
    return None


def insert_schedules_to_db(schedules: list[tuple[int,str]]) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM schedules WHERE FlightDate < CURRENT_DATE;")

    cursor.executemany("""
                INSERT INTO schedules (routeid, flightdate)
                VALUES (%s, %s)
                ON CONFLICT (routeid, flightdate) DO UPDATE
                SET datemodified = NOW()
            """, schedules)

    connection.commit()
    schedules_inserted = cursor.rowcount
    cursor.close()
    connection.close()

    return schedules_inserted


def get_flight_search(flight_search_request: FlightSearchRequest) -> list[dict[str, Any]] | None:
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
            SELECT DISTINCT
                s_out.flightdate AS outbound,
                s_ret.flightdate AS return,
                r_out.originairport,
                r_out.destinationairport,
                (s_ret.flightdate - s_out.flightdate + 1) AS days
            FROM schedules s_out
            JOIN routes r_out ON s_out.routeid = r_out.routeid
            JOIN routes r_ret ON r_ret.originairport = r_out.destinationairport 
                             AND r_ret.destinationairport = r_out.originairport
            JOIN schedules s_ret ON s_ret.routeid = r_ret.routeid
            WHERE r_out.originairport = ANY(%(origins)s)
            AND r_out.destinationairport = ANY(%(destinations)s)
            AND s_out.flightdate BETWEEN %(depart_from)s AND %(depart_to)s
            AND s_ret.flightdate BETWEEN %(depart_from)s AND %(depart_to)s
            AND (s_ret.flightdate - s_out.flightdate + 1) BETWEEN %(min_days)s AND %(max_days)s
        """, {
        "origins": flight_search_request.origins,
        "destinations": flight_search_request.destinations,
        "depart_from": flight_search_request.depart_from,
        "depart_to": flight_search_request.depart_to,
        "min_days": flight_search_request.min_days,
        "max_days": flight_search_request.max_days
    })

    flight_results = cursor.fetchall()
    cursor.close()
    connection.close()

    if flight_results:
        return list(flight_results)
    return None