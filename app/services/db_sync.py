from app.database import get_connection


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


def get_all_polish_airports_db() -> list[str] | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT code FROM airports WHERE country = 'Poland';")

    airports = cursor.fetchall()
    cursor.close()
    connection.close()

    if airports:
        return [airport[0] for airport in airports]
    return None


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


def insert_schedules_to_db(schedules: list[tuple[int,str]] ) -> int:
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