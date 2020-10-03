from datetime import datetime
from typing import Iterable

from req import requests

from models import Record
from scrapers import THIRTY_MINS
from utils import BERLIN_TIME


class RadioParadiso:
    schedule = THIRTY_MINS
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        # This only yields the last 10 results, there is an hour-by-hour search
        # but it requires parsing HTML.
        # Investigative start point is https://www.paradiso.de/playlist
        url = 'https://www.paradiso.de/pl/update.php?channel=paradiso_982'
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        for entry in r.json():
            yield Record(
                datetime.fromtimestamp(int(entry['timestamp']), tz=BERLIN_TIME),
                entry['song'],
                entry['artist'],
            )


if __name__ == '__main__':
    for x in RadioParadiso().fetch():
        print(x)
