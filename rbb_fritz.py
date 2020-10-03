# This god-forsaken website has 'playlists from the last 24 hours' and no
# timestamps.
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from models import Record


# TODO: maybe finish this? I decided to skip it because it's pretty patchy and also super hard to implement.
class RbbFritz:
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        url = 'https://www.fritz.de/programm/sendungen/playlists/'
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.select_one('.playlist_tables')
        print(table)
        headers = table.find_all('h2')
        playlist_containers = table.select('div.table_container')
        assert len(headers) == len(playlist_containers)
        for (header, playlist) in zip(headers, playlist_containers):
            times = header.span.text
            [start, end] = times.split(' - ')
            # Converts <div class="sub_heading">vom 03.10.2020 <p class="moderation">mit <a href="/alles-fritzen/team/fritz_team/2721.html" title="Henrike Möller">Henrike Möller</a></p></div>
            # to 'vom 03.10.2020 '
            # See https://stackoverflow.com/questions/44858226/how-to-extract-the-text-inside-a-tag-with-beautifulsoup-in-python/44859413
            date_texts = playlist.select_one('.sub_heading').find_all(text=True, recursive=False)
            # There's sometimes whitespace floating around, this removes it
            stripped_and_filtered = [t.strip() for t in date_texts if t.strip()]
            assert len(stripped_and_filtered) == 1

            [date_text] = stripped_and_filtered
            yield (date_text, start, end)

if __name__ == '__main__':
    for x in RbbFritz().fetch():
        print(x)
