from typing import Iterable, Protocol

import requests

from models import Record

Schedule = str


class FutureScraper(Protocol):
    def schedule(self) -> Schedule:
        raise NotImplemented

    def fetch(self) -> requests.Response:
        raise NotImplemented

    def parse(self, r: requests.Response) -> Iterable[Record]:
        raise NotImplemented


class Scraper(Protocol):
    def fetch(self) -> Iterable[Record]: ...
