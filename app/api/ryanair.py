import httpx
from app.logger import get_logger
from app.services.db_sync import get_all_routes_db, get_all_airports_db
from app.utils import extract_flight_info
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    airports = get_all_airports_db(code_only=True, from_poland=True)
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


def get_all_schedules() -> list[tuple[int,str]]:
    all_schedules = []
    routes = get_all_routes_db()
    if routes:
        for i, route in enumerate(routes):
            logger.info(f"Fetching schedules {i + 1}/{len(routes)}: {route[1]}->{route[2]}")
            url = f'https://www.ryanair.com/api/farfnd/v4/oneWayFares/{route[1]}/{route[2]}/availabilities'
            try:
                response = httpx.get(url)
                response.raise_for_status()
                schedules_json = response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch routes for {route[1]}->{route[2]}: {e}")
                continue
            for schedule in schedules_json:
                all_schedules.append((route[0],schedule))
        return all_schedules
    else:
        logger.warning("No routes found in DB")
        return []


def get_one_way_fares(api_calls: list[tuple[str, str, str]]) -> list[tuple[str, str, str, str, str, float, str]]:
    def fetch_single(flight: tuple[str, str, str]):
        origin, destination, month_date = flight
        logger.info(f"Fetching flight {origin}->{destination} info for {month_date}")
        url = f'https://www.ryanair.com/api/farfnd/3/oneWayFares/{origin}/{destination}/cheapestPerDay?outboundMonthOfDate={month_date}&currency=PLN'
        try:
            response = httpx.get(url)
            response.raise_for_status()
            return extract_flight_info(flights=response.json(), origin=origin, destination=destination)
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch flight {origin}->{destination} info for {month_date}: {e}")
            return []

    flights_list = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_single, flight): flight for flight in api_calls}
        for future in as_completed(futures):
            flights_list.extend(future.result())
    return flights_list