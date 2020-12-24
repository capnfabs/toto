import sys

from pony.orm import db_session

import models
from normalizer.normalize import normalize_title_artist_for_search


def main():
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)

    all_results = set()

    with db_session:
        all_songplays = models.SongPlay.select()

        for sp in all_songplays:
            result = normalize_title_artist_for_search(sp)
            all_results.add(result)

    print(f'Calculated {len(all_results)} unique search terms.')


if __name__ == '__main__':
    main()
