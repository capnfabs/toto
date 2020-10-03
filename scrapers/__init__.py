from typing import Iterable, Protocol

from models import Record

Schedule = str

THIRTY_MINS: Schedule = '30 mins'


class Scraper(Protocol):
    schedule: Schedule
    def fetch(self) -> Iterable[Record]: ...
