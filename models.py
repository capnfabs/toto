import datetime
from typing import NamedTuple

from pony.orm import Database, Optional, Required, composite_index, composite_key


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


BLANK = ""
DECISION_AUTO = "auto"
DECISION_MANUAL_CHOICE = "manual_choice"
DECISION_MANUAL_CHOICE_SKIPPED = "manual_choice_skipped"
DECISION_MANUAL_ENTRY = "manual_entry"


class MusicBrainzDetails(db.Entity):
    searched_title = Required(str)
    searched_artist = Required(str)
    musicbrainz_id = Optional(str)
    musicbrainz_json = Optional(str)
    # Only use the DECISION_[whatever] entries
    match_decision_source = Required(str, index=True)

    # Make searching on this fast
    composite_key(searched_title, searched_artist)


def connect_db(filename: str = 'database.sqlite'):
    db.bind(provider='sqlite', filename=filename, create_db=True)
    db.generate_mapping(create_tables=True)
