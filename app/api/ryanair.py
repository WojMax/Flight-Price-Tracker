import httpx
from app.logger import get_logger
from app.services.db_sync import get_all_polish_airports

logger = get_logger(__name__)

def get_all_airports() -> list[tuple[str, str, str]] | None:
    url = "https://www.ryanair.com/api/views/locate/5/airports/en/active"
    try:
        response = httpx.get(url)
        response.raise_for_status()
        airports_json = response.json()
        return [(x["code"], x["name"], x["country"]["name"]) for x in airports_json]
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch airports: {e}")
        return None


def get_all_routes() -> list[tuple[str,str,str]]:
    airports = get_all_polish_airports()
    if not airports:
        logger.warning("No Polish airports found in DB")
        return []
    airline = 'FR'
    all_airport_routes = []
    for airport in airports:
        url = f'https://www.ryanair.com/api/views/locate/searchWidget/routes/en/airport/{airport}'
        try:
            response = httpx.get(url)
            response.raise_for_status()
            routes_json = response.json()
            for route in routes_json:
                all_airport_routes.append((airline,airport,route["arrivalAirport"]["code"]))
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch routes for {airport} airport: {e}")
            continue
    return all_airport_routes