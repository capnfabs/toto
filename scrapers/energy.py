import time
from datetime import datetime
from typing import Iterable

from req import requests
from bs4 import BeautifulSoup

from models import Record
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME, datetime_from_berlin_hhmmss


class Energy:
    schedule = THIRTY_MINS
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        url = 'https://www.energy.de/songserver.php'
        now_berlin = datetime.now(tz=BERLIN_TIME)
        data = {
            'stationnumber': 1,
            'startzeit': now_berlin.hour,
            # '02.10.2020'
            'tag': now_berlin.strftime('%d.%m.%Y'),
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


if __name__ == '__main__':
    for row in Energy().fetch():
        print(row)
