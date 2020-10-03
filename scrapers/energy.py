import time
from datetime import datetime
from typing import Iterable

from req import requests
from bs4 import BeautifulSoup

from models import Record
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME, HOUR, datetime_from_berlin_hhmmss


class Energy:
    schedule = THIRTY_MINS
    def __init__(self) -> None:
        pass

    def _fetch_at_time(self, dt: datetime) -> Iterable[Record]:
        assert dt.tzinfo # Avoid common mistakes
        url = 'https://www.energy.de/songserver.php'
        data = {
            'stationnumber': 1,
            'startzeit': dt.hour,
            # '02.10.2020'
            'tag': dt.strftime('%d.%m.%Y'),
        }
        r = requests.post(url, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for row in soup.find_all('tr'):
            timestamp = row.select_one('.songtime').text
            tt = time.strptime(timestamp, '%H:%M Uhr')
            timestamp = datetime_from_berlin_hhmmss(tt.tm_hour, tt.tm_min, 0)

            artist_track = row.select_one('.songinfo')
            artist = artist_track.a.extract().text
            # now we've detached the artist, we should just have the track with a prefix
            track = artist_track.text
            assert track.startswith(' - ')
            title = track[3:]
            yield Record(timestamp, title, artist)

    def fetch(self) -> Iterable[Record]:
        now_berlin = datetime.now(tz=BERLIN_TIME)
        # This API is not continuous (i.e. fetching at 10:01 only returns two
        # mins of results) so we make multiple fetches.
        for val in self._fetch_at_time(now_berlin):
            yield val
        for val in self._fetch_at_time(now_berlin - HOUR):
            yield val


if __name__ == '__main__':
    for row in Energy().fetch():
        print(row)
