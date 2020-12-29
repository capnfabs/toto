import datetime
import json
import sys
from typing import Any, Dict, Optional

from pony.orm import TransactionIntegrityError, db_session

import models
from models import iterate_thru_songplays
from normalizer import clientschema, fetchmodels
from normalizer.normalize import normalize_title_artist_for_search


INCLUDE_STATIONS = ['Berliner Rundfunk']


def _get_or_create_station(label: str) -> clientschema.Station:
    with db_session:
        return clientschema.Station.get(lambda s: s.name == label) or clientschema.Station(
            name=label)


ArtistJson = Dict[str, Any]


@db_session
def _get_or_create_artist(artist_json: ArtistJson) -> clientschema.Artist:
    return (
            clientschema.Artist.get(lambda a: a.musicbrainz_artist_id == artist_json['id']) or
            clientschema.Artist(name=artist_json['name'],
                                musicbrainz_artist_id=artist_json['id']))


@db_session
def _get_or_create_song(sp: models.SongPlay) -> Optional[clientschema.Song]:
    search_title, search_artist = normalize_title_artist_for_search(sp)
    query = fetchmodels.MusicBrainzDetails.select(
        lambda deets: (
                deets.searched_artist == search_artist and
                deets.searched_title == search_title
        )
    )

    obj: Optional[fetchmodels.MusicBrainzDetails] = query.get()

    if not obj:
        # Hasn't been processed yet
        return None

    if not obj.musicbrainz_id:
        # Drop it like it's hawwttttt
        # print('Dropping', obj.searched_artist, '-', obj.searched_title)
        return None

    song = clientschema.Song.get(lambda s: s.musicbrainz_recording_id == obj.musicbrainz_id)
    if song:
        return song

    objjson = json.loads(obj.musicbrainz_json)

    song_title = objjson['title']
    artists = [credit['artist'] for credit in objjson['artist-credit'] if
               isinstance(credit, dict)]

    artists = [_get_or_create_artist(artist) for artist in artists]

    return clientschema.Song(
        title=song_title,
        artists=artists,
        musicbrainz_recording_id=obj.musicbrainz_id)


def process_item(sp: models.SongPlay) -> None:
    if sp.station not in INCLUDE_STATIONS:
        return
    ts = datetime.datetime.fromisoformat(sp.timestamp)
    try:
        with db_session:
            song = _get_or_create_song(sp)
            if not song:
                return

            clientschema.SongPlay(
                timestamp=ts,
                station=_get_or_create_station(sp.station),
                song=song,
            )
    except TransactionIntegrityError:
        # This is really noisy
        # print(f'Skipping {sp.to_dict()}, already processed')
        pass


def main():
    models.connect_db('/Users/fabian/Downloads/database.sqlite')
    clientschema.connect_db('/Users/fabian/Downloads/output.sqlite')
    fetchmodels.connect_db()

    iterate_thru_songplays(process_item)

    # This saves about 20% before compression / 30% after
    if '--shrinkwrap' in sys.argv:
        shrinkwrap(clientschema.db)


def shrinkwrap(db):
    with db_session:
        indexes = db.select("SELECT name FROM sqlite_master WHERE type == 'index'")
        for index in indexes:
            if not index.startswith('sqlite_autoindex'):
                # WARNING THIS IS TERRIBLE DO NOT DO IT ON UNTRUSTED INPUT
                db.execute('DROP INDEX ' + index)

    # Can't be done within transaction so we use Tricks™️
    with db_session:
        db._exec_raw_sql('VACUUM', None, None, 0)


if __name__ == '__main__':
    main()
