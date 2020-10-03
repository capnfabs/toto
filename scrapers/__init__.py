from typing import Iterable, Protocol

import req

from models import Record

Schedule = str

THIRTY_MINS: Schedule = '30 mins'


class FutureScraper(Protocol):
    def schedule(self) -> Schedule:
        raise NotImplemented

    def fetch(self) -> req.Response:
        raise NotImplemented

    def parse(self, r: req.Response) -> Iterable[Record]:
        raise NotImplemented


class Scraper(Protocol):

    schedule: Schedule

    def fetch(self) -> Iterable[Record]: ...
