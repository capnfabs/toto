import datetime
from typing import NamedTuple

from dateutil import tz

HOUR = datetime.timedelta(hours=1)
DAY = datetime.timedelta(days=1)
BERLIN_TIME = tz.gettz('Europe/Berlin')

class Record(NamedTuple):
    timestamp: datetime.datetime
    title: str
    artist: str
    broadcaster: str

    def __str__(self):
        return f'{self.timestamp.isoformat()} - {self.title} - {self.artist} ({self.broadcaster})'
