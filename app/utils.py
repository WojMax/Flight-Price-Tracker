from typing import Any
from datetime import datetime as dt, timedelta, date
from decimal import Decimal
import httpx
from app.logger import get_logger

logger = get_logger(__name__)


def fetch_holidays(start: date, end: date, country_code: str = "PL") -> set[date]:
    years = set(range(start.year, end.year + 1))
    holidays: set[date] = set()
    for year in years:
        try:
            response = httpx.get(
                f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
            )
            response.raise_for_status()
            holidays |= {date.fromisoformat(h["date"]) for h in response.json()}
            logger.info(f"Fetched {len(holidays)} holidays for {country_code} {year}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch holidays for {country_code} {year}: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Network error fetching holidays for {country_code} {year}: {e}")
    return holidays


def analyze_pto(start: date, end: date, holidays: set[date]) -> dict[str, int]:
    pto_days = 0
    free_days = 0
    current = start
    while current <= end:
        if current.weekday() >= 5 or current in holidays:
            free_days += 1
        else:
            pto_days += 1
        current += timedelta(days=1)
    return {"pto_days": pto_days, "free_days": free_days}


def extract_fare_requests(candidates: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    fare_requests = set()
    for flight in candidates:
        fare_requests.add(
            (
                flight["originairport"],
                flight["destinationairport"],
                flight["outbound"].replace(day=1).strftime('%Y-%m-%d')
            )
        )
        fare_requests.add(
            (
                flight["destinationairport"],
                flight["originairport"],
                flight["return"].replace(day=1).strftime('%Y-%m-%d')
            )
        )
    return list(fare_requests)


def extract_flight_info(
        flights: dict[str, Any],
        origin: str,
        destination: str
) -> list[tuple[str, str, str, str, str, float, str]]:
    flights_info_list = []
    for flight_info in flights["outbound"]["fares"]:
        if not flight_info["soldOut"] and not flight_info["unavailable"]:
            flights_info_list.append(
                (
                    origin,
                    destination,
                    flight_info["day"],
                    flight_info["departureDate"],
                    flight_info["arrivalDate"],
                    flight_info["price"]["value"],
                    flight_info["price"]["currencyCode"]
                )
            )
    return flights_info_list


def enrich_candidates(
        candidates: list[dict[str, Any]],
        fares: list[tuple[str, str, str, str, str, float, str]],
        holidays: set[date]
) -> list[dict[str, Any]]:
    enriched_candidates = []
    fare_lookup = {
        (fare[0], fare[1], fare[2]): fare  # key: (origin, destination, day)
        for fare in fares
    }
    for candidate in candidates:
        outbound_enrichment = fare_lookup.get(
            (
            candidate["originairport"],
            candidate["destinationairport"],
            str(candidate["outbound"])
            )
        )
        return_enrichment = fare_lookup.get(
            (
            candidate["destinationairport"],
            candidate["originairport"],
            str(candidate["return"])
            )
        )
        if outbound_enrichment is not None and return_enrichment is not None:
            outbound_departure_dt = dt.fromisoformat(outbound_enrichment[3])
            outbound_arrival_dt = dt.fromisoformat(outbound_enrichment[4])
            return_departure_dt = dt.fromisoformat(return_enrichment[3])
            return_arrival_dt = dt.fromisoformat(return_enrichment[4])
            pto = analyze_pto(candidate["outbound"], candidate["return"], holidays)

            enriched_candidates.append(
                {
                    "origin": candidate["originairport"],
                    "destination": candidate["destinationairport"],
                    "days": candidate["days"],
                    "hours": round(((return_departure_dt - outbound_arrival_dt).total_seconds() / 3600) * 2) / 2,
                    "pto_days": pto["pto_days"],
                    "free_days": pto["free_days"],
                    "outbound_date": candidate["outbound"],
                    "outbound_day": outbound_departure_dt.strftime("%A"),
                    "outbound_departure_hour": outbound_departure_dt.strftime("%H:%M"),
                    "outbound_departure_datetime": outbound_enrichment[3],
                    "outbound_arrival_datetime": outbound_enrichment[4],
                    "outbound_price": outbound_enrichment[5],
                    "return_date": candidate["return"],
                    "return_day": return_arrival_dt.strftime("%A"),
                    "return_arrival_hour": return_arrival_dt.strftime("%H:%M"),
                    "return_departure_datetime": return_enrichment[3],
                    "return_arrival_datetime": return_enrichment[4],
                    "return_price": return_enrichment[5],
                    "total_price": float(Decimal(str(outbound_enrichment[5])) + Decimal(str(return_enrichment[5]))),
                    "currency": outbound_enrichment[6],
                }
            )
    return enriched_candidates