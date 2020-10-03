from datetime import datetime
from typing import Iterable

from req import requests

from models import Record
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME


class FluxFM:
    schedule = THIRTY_MINS
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        url = 'https://www.fluxfm.de/fluxfm-playlist/api.php?act=list&loc=berlin&cuttime=1&limit=50'
        # NOTE: this only retrieves stuff for the same day!
        # So probably good to make sure we fetch at 11:59 Berlin time :)
        r = requests.get(url)
        r.raise_for_status()
        body = r.json()
        assert body['status'] == 'ok'
        for row in body['tracks']:
            timestamp = datetime.strptime(f"{row['date']} {row['time']}", '%Y-%m-%d %H:%M')
            timestamp = timestamp.replace(tzinfo=BERLIN_TIME)
            artist = row['artist']
            title = row['title']
            yield Record(timestamp, title, artist)

if __name__ == '__main__':
    for x in FluxFM().fetch():
        print(x)
