import json
import sys
from typing import Optional

import musicbrainzngs
from pony.orm import db_session

import models
from normalizer.fetchmodels import DECISION_MANUAL_CHOICE, DECISION_MANUAL_CHOICE_SKIPPED, \
    MusicBrainzDetails
from normalizer.normalize import ListType, format_recording, load_candidates, \
    normalize_title_artist_for_search, \
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

    print(f"Reconciling '{sp.artist}' - '{sp.title}' using terms '{search_artist}', '{search_title}'")
    candidates = load_candidates(search_title, search_artist, 11)
    print_candidates(candidates, list_type=ListType.ORDERED)
    selection = gimme_a_digit(len(candidates))
    if selection is None:
        # Aborted
        obj.match_decision_source = DECISION_MANUAL_CHOICE_SKIPPED
        print('Skipped')
        return

    chosen = candidates[selection]

    obj.match_decision_source = DECISION_MANUAL_CHOICE
    obj.musicbrainz_id = chosen['id']
    obj.musicbrainz_json = json.dumps(chosen)
    print(f"Alright, search tuple ('{search_artist}', '{search_title}') to use {format_recording(chosen)}")


def gimme_a_digit(maxval: int) -> Optional[int]:
    while True:
        val = input("Pick a number (or 's' to skip, ENTER to accept #0): ")
        if val.lower() == 's':
            return None
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
