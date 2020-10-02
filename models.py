import datetime
from typing import NamedTuple

HOUR = datetime.timedelta(hours=1)


class Record(NamedTuple):
    timestamp: datetime.datetime
    title: str
    artist: str
    broadcaster: str
