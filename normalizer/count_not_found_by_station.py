import sys
from collections import defaultdict

import models
from normalizer import fetchmodels
from normalizer.normalize import load_normalized_for


def main():
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)
    fetchmodels.connect_db()

    missing_plays_by_station = defaultdict(lambda: 0)
    missing_tracks_by_station = defaultdict(lambda: set())

    def process(sp: models.SongPlay) -> None:
        title, artist, result = load_normalized_for(sp)
        if not result:
            # We never attempted lookup.
            missing_plays_by_station['[skipped]'] += 1
            missing_tracks_by_station['[skipped]'].add((title, artist))
            return

        if not result.musicbrainz_id:
            missing_plays_by_station[sp.station] += 1
            missing_tracks_by_station[sp.station].add((title, artist))

    models.iterate_thru_songplays(process, batch_size=10_000)

    print('Missing by station:')
    for station, missing_tracks in sorted(missing_tracks_by_station.items()):
        missing_plays = missing_plays_by_station[station]
        print(f' - {station:>20}: {len(missing_tracks)} tracks, comprising {missing_plays} plays')


if __name__ == '__main__':
    main()
