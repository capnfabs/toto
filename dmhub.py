import datetime
from typing import Iterable

import requests
from dateutil import tz

from models import Record

# Tested with RTL on 2 Oct 2020
DMHUB_API_LIMIT = 50
BERLIN_TIME = tz.gettz('Europe/Berlin')

class DmHub:
    def __init__(self, host: str, station: str, broadcaster: str) -> None:
        self.host = host
        self.station = station
        self.broadcaster = broadcaster

    def fetch(self) -> Iterable[Record]:
        # Here's a timezone aware UTC
        end = datetime.datetime.now(datetime.timezone.utc)
        assert end.date() == datetime.date.today()

        end_berlin_time = end.astimezone(tz=BERLIN_TIME)
        hour = end_berlin_time.hour
        minute = end_berlin_time.minute
        print(f'Requesting time at {hour}:{minute} (berlin time)')
        # TODO: do I need to change the word air here?
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
            # TODO: this will break on the 25th of October at 3am
            timestamp = datetime.datetime.fromtimestamp(record['start'] / 1000, tz=BERLIN_TIME)
            song_title = record['track']['title']
            artist_name = record['track']['artist']

            yield Record(
                timestamp=timestamp,
                title=song_title,
                artist=artist_name,
                broadcaster=self.broadcaster)

def main():
    dm = DmHub('104.6rtl.com', 'rtl', 'rtl')
    for x in dm.fetch():
        print(x)

    dm = DmHub('www.jam.fm', 'jam', 'jamfm')
    for x in dm.fetch():
        print(x)

    dm = DmHub('spreeradio.de', 'spree', 'spreeradio')
    for x in dm.fetch():
        print(x)

if __name__ == '__main__':
    main()
