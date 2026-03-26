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
