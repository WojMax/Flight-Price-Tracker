from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import get_connection
from psycopg2.extras import RealDictCursor
from app.api.ryanair import get_all_airports, get_all_routes, get_all_schedules
from app.logger import get_logger
from app.models import FlightSearchRequest
from app.services.db_sync import insert_airports_to_db, insert_routes_to_db, insert_schedules_to_db, \
    get_all_airports_db, get_flight_search

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
            logger.warning(f"No routes returned from API")
    except Exception as e:
        logger.error(f"Failed to sync routes: {e}")

##    logger.info("Start fetching schedules...")
##    try:
##        all_schedules = get_all_schedules()
##        if all_schedules:
##            schedules_inserted = insert_schedules_to_db(schedules=all_schedules)
##            logger.info(f"Successfully inserted: {schedules_inserted} rows to schedules table")
##        else:
##            logger.warning(f"No schedules returned from API")
##    except Exception as e:
##        logger.error(f"Failed to sync schedules: {e}")

    yield

    logger.info("Server shutting down...")


app = FastAPI(title="Flight Scanner", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/airports/origins")
def airports_origins():
    return {"airports": get_all_airports_db(code_only=False, from_poland=True)}


@app.get("/airports/destinations")
def airports_destinations():
    return {"airports": get_all_airports_db(code_only=False, from_poland=False)}


@app.post("/flights/search")
def search_flights(request: FlightSearchRequest):
    return get_flight_search(flight_search_request=request)