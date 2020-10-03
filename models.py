import datetime
from typing import NamedTuple


class Record(NamedTuple):
    timestamp: datetime.datetime
    title: str
    artist: str
    broadcaster: str

    def __str__(self) -> str:
        return f'{self.timestamp.isoformat()} - {self.title} - {self.artist} ({self.broadcaster})'
