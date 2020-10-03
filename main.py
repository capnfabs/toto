import sys
from typing import List, Tuple

from pony.orm import TransactionIntegrityError, db_session

from models import Record, SongPlay, connect_db
from scrapers import Scraper
from scrapers.dmhub import DmHub
from scrapers.energy import Energy
from scrapers.fluxfm import FluxFM
from scrapers.iris import IrisScraper
from scrapers.paradiso import RadioParadiso
from scrapers.radioeins import RadioEins
from scrapers.rbb import Rbb
from scrapers.star_fm import StarFm
from scrapers.wdr_cosmo import WdrCosmo
from utils import continue_on_error

ALL_SCRAPERS: List[Tuple[Scraper, str]] = [
    (StarFm(), 'starfm'),
    (Rbb('radioberlin'), 'rbb'),
    (IrisScraper('iris-brf', 5), 'Berliner Rundfunk'),
    (DmHub('www.jam.fm', 'jam'), 'jamfm'),
    (IrisScraper('iris-rs2', 7), 'RS2'),
    (RadioEins(), 'rbb_radio_eins'),
    (WdrCosmo(), 'wdr_cosmo'),
    (RadioParadiso(), 'paradiso'),
    (IrisScraper('iris-kissfm', 3), 'KissFM'),
    (Rbb('antenne_brandenburg'), 'antenne_brandenburg'),
    (FluxFM(), 'fluxfm'),
    (Energy(), 'energy_berlin'),
    (DmHub('104.6rtl.com', 'rtl'), 'rtl'),
    (DmHub('spreeradio.de', 'spree'), 'spreeradio'),
]

ALL_SCRAPER_NAMES = set(name for (_, name) in ALL_SCRAPERS)

def process_record(record: Record, station: str) -> None:
    status = '✅'
    try:
        with db_session:
            r = SongPlay(
                timestamp=record.timestamp,
                title=record.title,
                artist=record.artist,
                station=station,
            )
    except TransactionIntegrityError as ex:
        # It's a dupe.
        status = '⚠️ '

    print(f'{status} {record}')


def main() -> None:
    allowed_scrapers = set(sys.argv[1:]) or ALL_SCRAPER_NAMES

    # Validate
    for name in allowed_scrapers:
        assert name in ALL_SCRAPER_NAMES, f'"{name}" must be one of the permitted stations: {ALL_SCRAPER_NAMES}'

    connect_db()

    for (scraper, name) in ALL_SCRAPERS:
        if name not in allowed_scrapers:
            continue
        print(f'----- {name} -----')
        with continue_on_error():
            for record in scraper.fetch():
                process_record(record, name)


if __name__ == '__main__':
    # Strategy: every half hour + once at 11:58 and 11:59
    main()
