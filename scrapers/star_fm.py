import json
from time import strptime
from typing import Iterable

from req import requests

from models import Record
from scrapers import THIRTY_MINS
from utils import datetime_from_berlin_hhmmss


class StarFm:
    def __init__(self) -> None:
        pass

    schedule = THIRTY_MINS

    def fetch(self) -> Iterable[Record]:
        url = "https://berlin.starfm.de/player/ajax/getCurrentSongList.php"
        r = requests.get(url)
        r.raise_for_status()
        assert r.text.startswith('(') and r.text.endswith(');')
        body = json.loads(r.text[1:-2])
        # It's a dict with "0", "1" etc for keys (strings containing numbers) => objects
        for _index, record in body['all'].items():
            # TODO: this clause hasn't been tested.
            if not (record.get('cDate') and record.get('artist') and record.get('song')):
                print(f'Skipped bad record: {record}')
                continue

            time = strptime(record['cDate'], '%H:%M:%S')
            timestamp = datetime_from_berlin_hhmmss(time.tm_hour, time.tm_min, time.tm_sec)

            yield Record(
                timestamp,
                record['song'],
                record['artist'],
            )


if __name__ == '__main__':
    for x in StarFm().fetch():
        print(x)
