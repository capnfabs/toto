from datetime import datetime
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from models import Record
from utils import BERLIN_TIME


class Rbb:
    def __init__(self, station: str) -> None:
        self.url = f'http://playlisten.rbb-online.de/{station}/main/'

    def fetch(self) -> Iterable[Record]:
        r = requests.get(self.url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        [table] = soup.select('table')
        header = table.select('th')
        assert [h.text for h in header] == ['Datum', 'Zeit', 'Interpret', 'Titel']
        rows = table.find_all('tr')
        # first row is the header
        for row in rows[1:]:
            [datum, zeit, interpret, titel] = [cell.text for cell in row.find_all('td')]
            timestamp = datetime.strptime(f'{datum} {zeit}', '%d.%m.%Y %H:%M').replace(tzinfo=BERLIN_TIME)
            yield Record(timestamp, titel, interpret)


if __name__ == '__main__':
    for x in Rbb('radioberlin').fetch():
        print(x)
    for x in Rbb('antenne_brandenburg').fetch():
        print(x)
