import datetime
from typing import Iterable

import requests

from models import Record
from utils import HOUR, RequestParams


class IrisScraper:
    def __init__(self, host: str, station: int) -> None:
        self.host = host
        self.station = station

    def fetch(self) -> Iterable[Record]:
        url = f'https://{self.host}.loverad.io/search.json'
        end = datetime.datetime.utcnow()
        start = end - HOUR
        params: RequestParams = {
            'station': self.station,
            'start': start.isoformat(),
            'end': end.isoformat(),
        }
        resp = requests.get(url, params=params)
        assert resp.ok
        body = resp.json()
        found = body['result']['found']
        print(f'Found {found} records')
        for record in body['result']['entry']:
            timestamp = record['airtime']
            assert record['song']['found'] == '1', record['song']
            [song] = record['song']['entry']
            song_title = song['title']
            # This is potentially a very bad assumption, that there will be 1
            # artist?
            [artist] = song['artist']['entry']
            artist_name = artist['name']
            yield Record(
                timestamp=datetime.datetime.fromisoformat(timestamp),
                title=song_title,
                artist=artist_name)
