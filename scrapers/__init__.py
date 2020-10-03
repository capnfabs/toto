from typing import Iterable, Protocol

import req

from models import Record

Schedule = str


class FutureScraper(Protocol):
    def schedule(self) -> Schedule:
        raise NotImplemented

    def fetch(self) -> req.Response:
        raise NotImplemented

    def parse(self, r: req.Response) -> Iterable[Record]:
        raise NotImplemented


class Scraper(Protocol):
    def fetch(self) -> Iterable[Record]: ...
