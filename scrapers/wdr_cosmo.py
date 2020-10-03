from datetime import datetime
from typing import Iterable

from req import requests
from bs4 import BeautifulSoup

from models import Record
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME, MINUTE

FAIL_TEXT = 'Für Ihre Suchanfrage wurde nichts gefunden. Bitte ändern Sie die Suchparameter.'

class WdrCosmo:
    schedule = THIRTY_MINS
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        url = 'https://www1.wdr.de/radio/cosmo/musik/playlist/index.jsp'
        # playlistSearch_date=2020-10-03&playlistSearch_hours=07&playlistSearch_minutes=00&submit=suchen

        # This API is kinda nuts; it returns the 30 minutes on either side of the supplied timestamp
        # So this returns the last hour.
        midpoint_time = datetime.now(tz=BERLIN_TIME) - 30*MINUTE
        form_data = {
            # '2020-10-03'
            'playlistSearch_date': midpoint_time.strftime('%Y-%m-%d'),
            'playlistSearch_hours': midpoint_time.strftime('%H'),
            'playlistSearch_minutes': midpoint_time.strftime('%M'),
            'submit': 'suchen',
        }
        r = requests.post(url, data=form_data)
        r.raise_for_status()
        if FAIL_TEXT in r.text:
            return
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.select_one('#searchPlaylistResult table')
        [header, *rows] = table.select('tr')
        assert [el.text for el in header.select('th')] == ['Datum und Uhrzeit', 'Titel', 'Interpret']
        for row in rows:
            timestamp_raw = row.th.text
            [song_name, artist] = [el.text.strip() for el in row.find_all('td')]
            # '03.10.2020,07.29 Uhr'
            timestamp_naive = datetime.strptime(timestamp_raw, '%d.%m.%Y,%H.%M Uhr')
            timestamp = timestamp_naive.replace(tzinfo=BERLIN_TIME)
            yield Record(timestamp, song_name, artist)


if __name__ == '__main__':
    for row in WdrCosmo().fetch():
        print(row)
