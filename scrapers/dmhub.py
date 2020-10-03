import datetime
from typing import Iterable

from req import requests

from models import Record

# Tested with RTL on 2 Oct 2020
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME

DMHUB_API_LIMIT = 50


class DmHub:
    schedule = THIRTY_MINS

    def __init__(self, host: str, station: str) -> None:
        self.host = host
        self.station = station

    def fetch(self) -> Iterable[Record]:
        end_berlin_time = datetime.datetime.now(tz=BERLIN_TIME)
        hour = end_berlin_time.hour
        minute = end_berlin_time.minute
        print(f'Requesting time at {hour}:{minute} (berlin time)')
        # Word 'air' is a constant, not program related
        url = f'https://{self.host}/services/program-info/history/{self.station}/air/0/{hour}/{minute}'

        params = {
            'items': DMHUB_API_LIMIT,
        }
        resp = requests.get(url, params=params)
        assert resp.ok
        body = resp.json()
        print(f'Found {len(body)} records')
        for record in body:
            # Millis to seconds
            timestamp = datetime.datetime.fromtimestamp(record['start'] / 1000, tz=BERLIN_TIME)
            song_title = record['track']['title']
            artist_name = record['track']['artist']

            yield Record(
                timestamp=timestamp,
                title=song_title,
                artist=artist_name)


def main() -> None:
    dm = DmHub('104.6rtl.com', 'rtl')
    for x in dm.fetch():
        print(x)

    dm = DmHub('www.jam.fm', 'jam')
    for x in dm.fetch():
        print(x)

    dm = DmHub('spreeradio.de', 'spree')
    for x in dm.fetch():
        print(x)


if __name__ == '__main__':
    main()
