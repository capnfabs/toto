import json
import sys
from typing import Any, Dict, Optional, Tuple

import musicbrainzngs
from pony.orm import db_session, sql_debug

import models


def normalize_artist_title(sp: models.SongPlay) -> Tuple[str, str]:
    title = sp.title.lower().strip()
    artist = sp.artist.lower().strip()
    if '(' in title:
        title: str
        # Intentionally chose first one because sometimes they have multiple
        # bits after, e.g. heroes (david bowie cover) (radio edit)
        cut_title = title[:title.index('(')]
        return cut_title.strip(), artist
    return title, artist


PRINT_ALTS = True


def process_item(sp: models.SongPlay) -> None:
    query = models.MusicBrainzDetails.select(lambda deets: deets.searched_artist == sp.artist and deets.searched_title == sp.title)
    with db_session:
        if query.exists():
            return

    print(f"Looking for '{sp.artist}' - '{sp.title}'")
    # This adds to the database too.
    find_candidate(sp)
    pass


MbRecording = Dict[str, Any]


def songplay_matches(title: str, artist: str, recording: MbRecording) -> bool:
    check_title = recording['title']
    # artists are either an object or a string '/'.
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    first_artist = artist_names[0]
    artist_match = artist.lower().startswith(first_artist.lower())
    title_match = title.lower() == check_title.lower()
    print('Artist match:', artist_match)
    print('Title  match:', title_match)
    return artist_match and title_match


def format_recording(recording: MbRecording) -> str:
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    check_artist = ' /plus/ '.join(artist_names)
    check_title = recording['title']
    mbid = recording['id']
    check_url = f'https://musicbrainz.org/recording/{mbid}'
    return f"'{check_artist}' - '{check_title}' --> {check_url}"


def find_candidate(sp: models.SongPlay) -> Optional[models.MusicBrainzDetails]:
    title, artist = normalize_artist_title(sp)
    print(f"Hitting MB for '{artist}' - '{title}'")
    data = musicbrainzngs.search_recordings(recording=title, artist=artist, limit=5)
    guessed_track: MbRecording = data['recording-list'][0]

    if songplay_matches(title, artist, guessed_track):
        mbid = guessed_track['id']
        print('Chose         ', format_recording(guessed_track))
        with db_session:
            return models.MusicBrainzDetails(
                searched_title=sp.title,
                searched_artist=sp.artist,
                musicbrainz_id=mbid,
                musicbrainz_json=json.dumps(guessed_track),
            )

    if PRINT_ALTS:
        print("Didn't find a good option, all candidates:")
        alts = data['recording-list']
        for track in alts:
            print('    - ', format_recording(track))
    else:
        print("Didn't find a good options, skipping")

    return None


def main():
    musicbrainzngs.set_useragent('toto-radiometadata', '0.00001', 'https://capnfabs.net/contact')
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)

    with db_session:
        all_songplays = models.SongPlay.select()[:200]
    for sp in all_songplays:
        process_item(sp)


if __name__ == '__main__':
    main()
