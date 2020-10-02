import json
from datetime import datetime
from time import strptime
from typing import Iterable

import requests

from models import BERLIN_TIME, DAY, Record


class StarFm:
    def __init__(self) -> None:
        pass

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
            # TODO: check that this handles wrapping correctly
            time = strptime(record['cDate'], '%H:%M:%S')
            now = datetime.now(tz=BERLIN_TIME)
            timestamp = now.replace(hour=time.tm_hour, minute=time.tm_min, second=time.tm_sec, microsecond=0)
            if timestamp > now:
                timestamp -= DAY
            yield Record(
                timestamp,
                record['song'],
                record['artist'],
                'starfm',
            )


if __name__ == '__main__':
    [print(x) for x in StarFm().fetch()]
