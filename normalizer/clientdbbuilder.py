import datetime
import json
from typing import Any, Dict, Optional

from pony.orm import db_session, flush, sql_debugging

import models
from models import MusicBrainzDetails
from normalizer import clientschema
from normalizer.normalize import normalize_title_artist_for_search


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
    query = models.MusicBrainzDetails.select(
        lambda deets: (
                deets.searched_artist == search_artist and
                deets.searched_title == search_title
        )
    )

    obj: Optional[MusicBrainzDetails] = query.get()
    assert obj

    if not obj.musicbrainz_id:
        # Drop it like it's hawwttttt
        print(obj.searched_artist, '-', obj.searched_title)
        return None

    song = clientschema.Song.get(lambda s: s.musicbrainz_recording_id == obj.musicbrainz_id)
    if song:
        return song

    objjson = json.loads(obj.musicbrainz_json)

    song_title = objjson['title']
    artists = [credit['artist'] for credit in objjson['artist-credit'] if
               isinstance(credit, dict)]

    artists = [_get_or_create_artist(artist) for artist in artists]
    print(artists)

    return clientschema.Song(
        title=song_title,
        artists=artists,
        musicbrainz_recording_id=obj.musicbrainz_id)


def process_item(sp: models.SongPlay) -> None:
    print(f'Processing {sp}')
    ts = datetime.datetime.fromisoformat(sp.timestamp)
    with db_session:
        song = _get_or_create_song(sp)
        if not song:
            return

        clientschema.SongPlay(
            timestamp=ts,
            station=_get_or_create_station(sp.station),
            song=song,
        )


def main():
    models.connect_db('/Users/fabian/Downloads/database.sqlite')
    clientschema.connect_db('/Users/fabian/Downloads/output.sqlite')

    with db_session:
        all_songplays = models.SongPlay.select()[0:400]
    for sp in all_songplays:
        process_item(sp)

    # This saves maybe 10%?
    #drop_nonessential_indexes(clientschema.db)


def drop_nonessential_indexes(db):
    with db_session:
        indexes = db.select("SELECT name FROM sqlite_master WHERE type == 'index'")
        for index in indexes:
            if not index.startswith('sqlite_autoindex'):
                # WARNING THIS IS TERRIBLE DO NOT DO IT ON UNTRUSTED INPUT
                db.execute('DROP INDEX ' + index)


if __name__ == '__main__':
    main()
