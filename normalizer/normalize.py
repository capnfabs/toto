import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import musicbrainzngs
from pony.orm import db_session

import models


def standardize(string: str) -> str:
    string = (string
            # em dash to ascii dash
            .replace('‐', '-')
            # fancy apostrophe to regular apostrophe
            .replace('’', "'")
            # Encoding bugs somewhere, can't figure out how this is happening
            .replace('ÃÂ¼', 'ü')
            .replace('ÃÂ', 'Ä')
            .replace('ÃÂ¶', 'ö')
            .replace('Ã¶', 'ö')
            .replace('Ã¤', 'ä')
            .lower()
            .strip()
            )
    # regex matches "entire string is symbols"
    # i.e. unless the string is only symbols
    if not re.match(r'^[^\d\w\s]+$', string):
        # replace all the symbols in the string
        string, _ = re.subn(r'[^\d\w\s]', '', string)
    return string


def normalize_artist_title(sp: models.SongPlay) -> Tuple[str, str]:
    title = sp.title
    artist = sp.artist
    if '(' in title:
        # Intentionally chose first one because sometimes they have multiple
        # bits after, e.g. heroes (david bowie cover) (radio edit)
        cut_title = title[:title.index('(')]
        return standardize(cut_title), standardize(artist)
    return standardize(title), standardize(artist)


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
    title_std = standardize(recording['title'])
    # artists are either an object or a string '/'.
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    first_artist_std = standardize(artist_names[0])
    artist_match = (
            artist.startswith(first_artist_std) or
            # Some providers drop the 'the'.
            f'the {artist}'.startswith(first_artist_std))
    title_match = title == title_std

    # TODO: try restoring the bracketed texts

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
    candidates: List[MbRecording] = data['recording-list']

    # TODO: Next things to try:
    # - Adding some kind of measure of similarity?
    # - Add a layer between 'searched text' and 'result', and allow 'nomatch'
    for attempt, candidate in enumerate(candidates):
        if songplay_matches(title, artist, candidate):
            mbid = candidate['id']
            print(f'Chose #{attempt}      ', format_recording(candidate))
            with db_session:
                return models.MusicBrainzDetails(
                    searched_title=sp.title,
                    searched_artist=sp.artist,
                    musicbrainz_id=mbid,
                    musicbrainz_json=json.dumps(candidate),
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
        all_songplays = models.SongPlay.select()[200:400]
    for sp in all_songplays:
        process_item(sp)


if __name__ == '__main__':
    main()
