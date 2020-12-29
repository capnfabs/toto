import datetime
from typing import Callable, NamedTuple

from pony.orm import Database, Optional, Required, composite_key, count, db_session


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

def connect_db(filename: str = 'database.sqlite'):
    db.bind(provider='sqlite', filename=filename, create_db=True)
    db.generate_mapping(create_tables=True)


DEFAULT_BATCH_SIZE = 1000


def iterate_thru_songplays(process_item: Callable[[SongPlay], None], batch_size=DEFAULT_BATCH_SIZE) -> None:
    with db_session:
        total_songplays = count(sp for sp in SongPlay)

    for i in range(total_songplays // batch_size + 1):
        start = i * batch_size
        end = (i + 1) * batch_size
        print(f'Running batch #{i} (items {start}-{end})')

        with db_session:
            all_songplays = SongPlay.select()[start:end]
        for sp in all_songplays:
            process_item(sp)
