import httpx


def get_all_airports() -> list[tuple[str, str, str]] | None:
    url = "https://www.ryanair.com/api/views/locate/5/airports/en/active"
    try:
        response = httpx.get(url)
        response.raise_for_status()
        airports_json = response.json()
        return [(x["code"], x["name"], x["country"]["name"]) for x in airports_json]
    except httpx.HTTPError as e:
        print(f"Failed to fetch airports: {e}")
        return None