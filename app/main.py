from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import get_connection
from psycopg2.extras import RealDictCursor
from app.api.ryanair import get_all_airports, get_all_routes
from app.logger import get_logger
from app.services.db_sync import insert_airports_to_db, insert_routes_to_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting...")
    logger.info("Start fetching airports...")
    try:
        airports = get_all_airports()
        if airports:
            airports_inserted = insert_airports_to_db(airports=airports)
            logger.info(f"Successfully inserted: {airports_inserted} rows to airports table")
        else:
            logger.warning(f"No airports returned from API")
    except Exception as e:
        logger.error(f"Failed to sync airports: {e}")

    logger.info("Start fetching routes...")
    try:
        all_airport_routes = get_all_routes()
        if all_airport_routes:
            routes_inserted = insert_routes_to_db(routes=all_airport_routes)
            logger.info(f"Successfully inserted: {routes_inserted} rows to routes table")
        else:
            logger.warning(f"No airports returned from API")
    except Exception as e:
        logger.error(f"Failed to sync airports: {e}")

    yield

    logger.info("Server shutting down...")


app = FastAPI(title="Flight Scanner", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM routes;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"routes": rows}
