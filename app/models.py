from pydantic import BaseModel
from datetime import date

class FlightSearchRequest(BaseModel):
    origins: list[str]
    destinations: list[str]
    depart_from: date
    depart_to: date
    min_days: int
    max_days: int