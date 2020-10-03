import json
import time
from datetime import datetime
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from models import Record
from utils import BERLIN_TIME, HOUR, RequestParams, datetime_from_berlin_hhmmss


class RadioEins:
    def __init__(self) -> None:
        pass

    def fetch(self) -> Iterable[Record]:
        url = 'https://playlist.funtip.de/playList.do'

        end = datetime.now(tz=BERLIN_TIME)
        start = end - 5*HOUR

        params: RequestParams = {
            # action, remote, version copied verbatim from template request
            'action': 'searching',
            'remote': 1,
            'version': 2,
            # format: dd-mm-yyyy_hh-mm
            'from': start.strftime('%d-%m-%Y_%H-%M'),
            'to': end.strftime('%d-%m-%Y_%H-%M'),
            'jsonp_callback': 'lol',
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        # Ok, this is nasty. It's JSONP (i.e. wrapped in a callback) and the keys of the object
        # don't have quotes so we can't parse as JSON directly. There's a single property, 'key',
        # which contains HTML.
        # Strip the callback
        assert r.text.startswith('lol(') and r.text.endswith(')')
        json_text = r.text[4:-1]
        # Replace `key` (without quotes) with `"key"` (with quotes) so we can JSON-parse it
        json_text = json_text.replace('key', '"key"', 1)
        # Now parse and grab the HTML
        html = json.loads(json_text)['key']
        # Parse content from HTML
        soup = BeautifulSoup(html, 'html.parser')
        [table] = soup.select('table.trackList')
        [header, *data] = table.find_all('tr')
        assert [el.text for el in header.find_all('th')] == ['Zeit', 'Artist - Track - Album']

        for row in data:
            # This is actually when it was played, not the track length
            [timestamp] = row.select('td.trackLength')
            # .trackInterpret seems semantic, .left seems formatting-related
            [artist_and_title] = row.select('.trackInterpret .left')
            # Remove album info if it's present (it's in a span.trackLabel)
            track_label = artist_and_title.select_one('.trackLabel')
            if track_label:
                track_label.decompose()
            # This is the time (just the time, Berlin time)
            tt = time.strptime(timestamp.text, '%H:%M')
            timestamp = datetime_from_berlin_hhmmss(tt.tm_hour, tt.tm_min, 0)

            # That's an em-dash
            [artist, title_in_quotes] = artist_and_title.text.strip().split(" — ")
            yield Record(timestamp, title_in_quotes.strip('"'), artist, "rbb_radioeins")



if __name__ == '__main__':
    for row in RadioEins().fetch():
        print(row)
