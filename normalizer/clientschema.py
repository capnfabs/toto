import datetime

from pony.orm import Database, Required, Set, composite_key

db = Database()


class Station(db.Entity):
    name = Required(str, index=True, unique=True)
    play_history = Set(lambda: SongPlay)


class Artist(db.Entity):
    name = Required(str)
    musicbrainz_artist_id = Required(str, index=True, unique=True)
    songs = Set(lambda: Song)


class Song(db.Entity):
    title = Required(str)
    artists = Set(lambda: Artist)
    musicbrainz_recording_id = Required(str, index=True)
    plays = Set(lambda: SongPlay)


class SongPlay(db.Entity):
    timestamp = Required(datetime.datetime)
    station = Required(lambda: Station)
    song = Required(lambda: Song)
    # Prevent dupes
    composite_key(station, timestamp, song)


def connect_db(filename: str):
    db.bind(provider='sqlite', filename=filename, create_db=True)
    db.generate_mapping(create_tables=True)
