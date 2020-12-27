import enum
import json
import re
import sys
import unicodedata
from typing import Any, Dict, List, Tuple

import musicbrainzngs
from fuzzywuzzy import fuzz
from pony.orm import db_session

import models
from normalizer import fetchmodels
from normalizer.fetchmodels import BLANK, DECISION_AUTO, MusicBrainzDetails


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


def standardize_title(title: str) -> str:
    return standardize(title)


def standardize_artist(artist: str) -> str:
    artist = standardize(artist)
    # This is a super common artist and it confuses the hell out of whatever
    # Musicbrainz' DB is doing (probably splitting on symbols).
    if artist.lower() == "pink":
        artist = "p!nk"
    return artist


def normalize_title_artist_for_search(sp: models.SongPlay) -> Tuple[str, str]:
    # Remove e.g. (Radio Edit)
    title = strip_bracketed(sp.title)
    artist = sp.artist

    return standardize_title(title), standardize_artist(artist)


PRINT_ALTS = True


def process_item(sp: models.SongPlay) -> None:
    search_title, search_artist = normalize_title_artist_for_search(sp)
    query = MusicBrainzDetails.select(
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

FUZZ_TITLE_THRESHOLD = 80
FUZZ_ARTIST_THRESHOLD = 85
DEBUG_MATCH_RATIOS = True

def songplay_matches(sp: models.SongPlay, recording: MbRecording) -> bool:
    found_title_std = standardize_title(recording['title'])
    # artists are either an object or a string '/'.
    artist_names = [artist['name'] for artist in recording['artist-credit'] if
                    isinstance(artist, dict)]
    found_first_artist_std = standardize_artist(artist_names[0])
    songplay_artist_std = standardize_artist(sp.artist)
    songplay_title_std = standardize_title(sp.title)
    if len(found_first_artist_std) < 2 or len(found_title_std) < 2:
        print('Bailed because found details are too short')
        return False

    print("artist_names:", artist_names)
    print("found_first_artist_std:", found_first_artist_std)
    print("found_title:", found_title_std)

    # Heuristics
    artist_match = (
       songplay_artist_std.startswith(found_first_artist_std) or
       f"the {songplay_artist_std}".startswith(found_first_artist_std)
    )

    # Fuzzy rescue! Note that fuzzy artist matching requires the _whole_ artist
    # so that we skip cases where the MB record has them around the wrong way.
    artist_match_ratio = fuzz.ratio(songplay_artist_std, found_first_artist_std)
    fuzzy_artist_match = artist_match_ratio >= FUZZ_ARTIST_THRESHOLD
    if not artist_match and fuzzy_artist_match:
        artist_match = True
        print('Fuzzy-matched artist, score:', artist_match_ratio)

    # Heuristics
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

    # Fuzzy rescue!
    title_match_ratio = fuzz.ratio(songplay_title_std, found_title_std)
    fuzzy_title_match = title_match_ratio >= FUZZ_TITLE_THRESHOLD
    if not title_match and fuzzy_title_match:
        title_match = True
        print('Fuzzy-matched title, score:', title_match_ratio)

    return artist_match and title_match


def join_artists(artist_credit) -> str:
    def selector():
        for artist_or_sep in artist_credit:
            if isinstance(artist_or_sep, str):
                yield artist_or_sep
            else:
                yield artist_or_sep['name']
    return ' '.join(token for token in selector())


def format_recording(recording: MbRecording) -> str:
    # The search API and the explicit 'lookup by ID' API have different results
    # here, so we need to treat them differently
    artist_names = [
        artist.get('name') or artist.get('artist', {})['name']
        for artist in recording['artist-credit'] if isinstance(artist, dict)]
    check_artist = ' /plus/ '.join(artist_names)
    check_title = recording['title']
    mbid = recording['id']
    check_url = f'https://musicbrainz.org/recording/{mbid}'
    return f"'{check_artist}' - '{check_title}' --> {check_url}"


def find_candidate(
        sp: models.SongPlay,
        search_title: str,
        search_artist: str,
        record_limit: int = 5) -> MusicBrainzDetails:
    """Returns either a match, or a "no match" object. """
    candidates = load_candidates(search_title, search_artist, record_limit)

    # Matching algorithm!
    for attempt, candidate in enumerate(candidates):
        if songplay_matches(sp, candidate):
            mbid = candidate['id']
            print(f'Chose #{attempt}      ', format_recording(candidate))
            with db_session:
                return MusicBrainzDetails(
                    searched_title=search_title,
                    searched_artist=search_artist,
                    musicbrainz_id=mbid,
                    musicbrainz_json=json.dumps(candidate),
                    match_decision_source=DECISION_AUTO,
                )

    if PRINT_ALTS:
        print("Didn't find a good option, all candidates:")
        print_candidates(candidates)
    else:
        print("Didn't find a good options, skipping")

    with db_session:
        return MusicBrainzDetails(
            searched_title=search_title,
            searched_artist=search_artist,
            musicbrainz_id=BLANK,
            musicbrainz_json=BLANK,
            match_decision_source=DECISION_AUTO,
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


def load_recording(url: str) -> MbRecording:
    prefix = 'https://musicbrainz.org/recording/'
    assert url.startswith(prefix)
    id = url[len(prefix):]
    print('loading ID:', id)
    return musicbrainzngs.get_recording_by_id(id, includes=['releases', 'artist-credits', 'isrcs'])['recording']


def main():
    musicbrainzngs.set_useragent('toto-radiometadata', '0.00001', 'https://capnfabs.net/contact')
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)
    fetchmodels.connect_db()

    with db_session:
        all_songplays = models.SongPlay.select()[0:400]
    for sp in all_songplays:
        process_item(sp)


if __name__ == '__main__':
    main()
