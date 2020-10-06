import datetime
from typing import NamedTuple

from pony.orm import Database, Optional, Required, composite_key


class Record(NamedTuple):
    timestamp: datetime.datetime
    title: str
    artist: str

    def __str__(self) -> str:
        return f'{self.timestamp.isoformat()}: {self.title} - {self.artist}'


db = Database()


class SongPlay(db.Entity):
    timestamp = Required(datetime.datetime)
    station = Required(str)
    title = Optional(str)  # means, can be blank, can't be NULL.
    artist = Optional(str) # means, can be blank, can't be NULL.
    # Prevent dupes
    composite_key(station, timestamp, title, artist)


def connect_db():
    db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
