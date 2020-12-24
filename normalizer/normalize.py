import enum
import json
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import musicbrainzngs
from pony.orm import db_session

import models


def strip_accents(string: str) -> str:
    """Borrowed from https://stackoverflow.com/questions/517923/"""
    nfkd_form = unicodedata.normalize('NFKD', string)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


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
            # Bunch of artists and titles do this
            .replace('&', 'and')
            .lower()
            .strip()
            )

    string = strip_accents(string)
    return string


def normalize_title_artist_for_search(sp: models.SongPlay) -> Tuple[str, str]:
    # Remove e.g. (Radio Edit)
    title = strip_bracketed(sp.title)
    artist = sp.artist
    return standardize(title), standardize(artist)


PRINT_ALTS = True


def process_item(sp: models.SongPlay) -> None:
    search_title, search_artist = normalize_title_artist_for_search(sp)
    query = models.MusicBrainzDetails.select(
        lambda deets: (
            deets.searched_artist == search_artist and
            deets.searched_title == search_title
        )
    )
    with db_session:
        if query.exists():
            return

    print(f"Looking for '{sp.artist}' - '{sp.title}' using terms '{search_artist}', '{search_title}'")
    # This adds to the database.
    find_candidate(sp, search_title, search_artist)


MbRecording = Dict[str, Any]


def strip_bracketed(string: str) -> str:
    string, _ = re.subn(r'\(.*\)', '', string)
    # Also handle the case where there's an unterminated bracket.
    string, _ = re.subn(r'\(.*?$', '', string)
    # Trim spaces that might be left over.
    string = string.strip()
    return string

def songplay_matches(sp: models.SongPlay, recording: MbRecording) -> bool:
    found_title_std = standardize(recording['title'])
    # artists are either an object or a string '/'.
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    found_first_artist_std = standardize(artist_names[0])
    songplay_artist_std = standardize(sp.artist)
    songplay_title_std = standardize(sp.title)
    if len(found_first_artist_std) < 2 or len(found_title_std) < 2:
        print('Bailed because found details are too short')
        return False

    artist_match = (
       songplay_artist_std.startswith(found_first_artist_std) or
       f"the {songplay_artist_std}".startswith(found_first_artist_std)
    )
    # Ok, so:
    # - If the song titles match
    # - Or the found title matches the title of the thing without brackets
    #     (e.g. to remove "(Radio Edit)")
    # then it's a match.
    # UNDER NO CIRCUMSTANCES should we remove the bracketed bits from the found
    # title, because then we'll pick up Will Smith - "Miami (Miami Mix)" as the
    # canonical version. No.
    title_match = (
            (songplay_title_std == found_title_std) or
            (strip_bracketed(songplay_title_std) == found_title_std) or
            (f"the {songplay_title_std}" == found_title_std) or
            (songplay_title_std == f"the {found_title_std}")
    )

    return artist_match and title_match


def format_recording(recording: MbRecording) -> str:
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    check_artist = ' /plus/ '.join(artist_names)
    check_title = recording['title']
    mbid = recording['id']
    check_url = f'https://musicbrainz.org/recording/{mbid}'
    return f"'{check_artist}' - '{check_title}' --> {check_url}"


def find_candidate(
        sp: models.SongPlay,
        search_title: str,
        search_artist: str,
        record_limit: int = 5) -> models.MusicBrainzDetails:
    """Returns either a match, or a "no match" object. """
    candidates = load_candidates(search_title, search_artist, record_limit)

    # Matching algorithm!
    for attempt, candidate in enumerate(candidates):
        if songplay_matches(sp, candidate):
            mbid = candidate['id']
            print(f'Chose #{attempt}      ', format_recording(candidate))
            with db_session:
                return models.MusicBrainzDetails(
                    searched_title=search_title,
                    searched_artist=search_artist,
                    musicbrainz_id=mbid,
                    musicbrainz_json=json.dumps(candidate),
                    match_decision_source=models.DECISION_AUTO,
                )

    if PRINT_ALTS:
        print("Didn't find a good option, all candidates:")
        print_candidates(candidates)
    else:
        print("Didn't find a good options, skipping")

    with db_session:
        return models.MusicBrainzDetails(
            searched_title=search_title,
            searched_artist=search_artist,
            musicbrainz_id=models.BLANK,
            musicbrainz_json=models.BLANK,
            match_decision_source=models.DECISION_AUTO,
        )

class ListType(enum.Enum):
    ORDERED = 0
    UNORDERED = 1


def print_candidates(candidates: List[MbRecording], list_type: ListType = ListType.UNORDERED) -> None:
    prefix_fmt: str
    if list_type == ListType.ORDERED:
        count = len(candidates)
        pad_to = len(f'{count - 1}')
        # This feels terrible but we're basically dynamically constructing
        # a format string
        prefix_fmt = '  {ordinal:' + f'{pad_to}' + 'd}.'
    elif list_type == ListType.UNORDERED:
        prefix_fmt = '  -'
    else:
        assert False, "unexpected ListType"
    for i, track in enumerate(candidates):
        print(prefix_fmt.format(ordinal=i), format_recording(track))


def load_candidates(search_title: str, search_artist: str, candidate_limit: int) -> List[MbRecording]:
    data = musicbrainzngs.search_recordings(
        recording=search_title,
        artist=search_artist,
        limit=candidate_limit)
    candidates: List[MbRecording] = data['recording-list']
    return candidates


def main():
    musicbrainzngs.set_useragent('toto-radiometadata', '0.00001', 'https://capnfabs.net/contact')
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)

    with db_session:
        all_songplays = models.SongPlay.select()[0:400]
    for sp in all_songplays:
        process_item(sp)


if __name__ == '__main__':
    main()
