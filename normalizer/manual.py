import json
import sys
from typing import Optional, Union

import musicbrainzngs
from pony.orm import db_session

import models
from normalizer import fetchmodels
from normalizer.fetchmodels import DECISION_MANUAL_CHOICE, DECISION_MANUAL_CHOICE_SKIPPED, \
    DECISION_MANUAL_ENTRY, MusicBrainzDetails
from normalizer.normalize import ListType, format_recording, load_candidates, \
    load_recording, normalize_title_artist_for_search, \
    print_candidates


@db_session
def process_item(sp: models.SongPlay) -> None:
    search_title, search_artist = normalize_title_artist_for_search(sp)
    query = MusicBrainzDetails.select(
        lambda deets: (
            deets.searched_artist == search_artist and
            deets.searched_title == search_title and
            not deets.musicbrainz_id
        )
    )

    obj = query.get()

    # We've already got an ID for this one.
    if not obj:
        return

    # We couldn't do this last time, don't try again.
    if obj.match_decision_source == DECISION_MANUAL_CHOICE_SKIPPED:
        return

    print(f"Reconciling '{sp.artist}' - '{sp.title}' using terms '{search_artist}', '{search_title}'")
    candidates = load_candidates(search_title, search_artist, 11)
    print_candidates(candidates, list_type=ListType.ORDERED)
    selection = gimme_a_digit_or_url(len(candidates))
    if selection is None:
        # Aborted
        obj.match_decision_source = DECISION_MANUAL_CHOICE_SKIPPED
        print('Skipped')
        return
    elif isinstance(selection, str):
        print('Fetching...')
        chosen = load_recording(selection)
        decision_src = DECISION_MANUAL_ENTRY
    elif isinstance(selection, int):
        chosen = candidates[selection]
        decision_src = DECISION_MANUAL_CHOICE
    else:
        assert False

    obj.match_decision_source = decision_src
    obj.musicbrainz_id = chosen['id']
    obj.musicbrainz_json = json.dumps(chosen)
    print(f"Alright, search tuple ('{search_artist}', '{search_title}') to use {format_recording(chosen)}")


def gimme_a_digit_or_url(maxval: int) -> Union[int, str, None]:
    while True:
        val = input("Pick a number ('s' to skip, ENTER to accept #0, paste a url to override): ")
        if val.lower() == 's':
            return None
        if val.lower().startswith('https://'):
            return val
        if val == '':
            # 'Accept #0'
            return 0
        try:
            index = int(val)
            if 0 <= index < maxval:
                return index
            else:
                print(f'Must be between 0..{maxval}.')
        except ValueError:
            pass


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
