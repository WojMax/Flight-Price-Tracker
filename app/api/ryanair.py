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
    url = "https://www.ryanair.com/api/views/locate/3/aggregate/all/en"
    try:
        response = httpx.get(url)
        response.raise_for_status()
        routes_aggregated_json = response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch routes for all airports: {e}")
        return []
    airports_dict = {airport["iataCode"]: airport for airport in routes_aggregated_json["airports"]}
    airports = get_all_polish_airports()
    if not airports:
        logger.warning("No Polish airports found in DB")
        return []
    airline = 'FR'
    all_airport_routes = []
    for airport in airports:
        if airport in airports_dict:
            destinations = [
                dest.replace('airport:','')
                for dest in airports_dict[airport]['routes']
                if dest.startswith('airport:')
            ]
            for route in destinations:
                all_airport_routes.append((airline,airport,route))
                all_airport_routes.append((airline,route,airport))
        else:
            logger.warning(f"Airport {airport} not found in Ryanair aggregate data")
            continue
    return list(set(all_airport_routes))