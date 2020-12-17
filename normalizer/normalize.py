import sys
from typing import Tuple

import musicbrainzngs
from pony.orm import db_session

import models


def normalize_artist_title(sp: models.SongPlay) -> Tuple[str, str]:
    title = sp.title.lower()
    artist = sp.artist.lower()
    if '(' in title:
        title: str
        # Intentionally chose first one because sometimes they have multiple
        # bits after, e.g. heroes (david bowie cover) (radio edit)
        cut_title = title[:title.index('(')]
        #print(f"Trimming title '{title}' to '{cut_title}")
        return cut_title, artist
    return title, artist


PRINT_ALTS = False


def process_item(sp: models.SongPlay) -> None:
    title, artist = normalize_artist_title(sp)
    query = models.MusicBrainzDetails.select(lambda deets: deets.searched_artist == artist and deets.searched_title == title)
    with db_session:
        if not query.exists():
            print('Hitting MB for', artist, '-', title)
            data = musicbrainzngs.search_recordings(recording=title, artist=artist, limit=5)
            #print(data)
            guessed_track = data['recording-list'][0]
            mbid = guessed_track['id']
            check_url = f'https://musicbrainz.org/recording/{mbid}'
            check_title = guessed_track['title']
            check_artist = ' /plus/ '.join(artist['name'] for artist in guessed_track['artist-credit'] if isinstance(artist, dict))
            print('Chose         ', check_artist, '-', check_title, '-->', check_url)
            if PRINT_ALTS:
                alts = data['recording-list'][1:]
                if alts:
                    print('from')
                for track in alts:
                    #print(track)
                    check_title = track['title']
                    check_artist = ' /plus/ '.join(
                        artist['name'] for artist in track['artist-credit'] if isinstance(artist, dict))
                    print('    - ', check_artist, '-', check_title, '-->', check_url)


def main():
    musicbrainzngs.set_useragent('toto-radiometadata', '0.00001', 'https://capnfabs.net/contact')
    [_, dbfile] = sys.argv
    models.connect_db(dbfile)

    with db_session:
        all_songplays = models.SongPlay.select()[:100]
        for sp in all_songplays:
            process_item(sp)


if __name__ == '__main__':
    main()
