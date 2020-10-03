from typing import List, Tuple

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


def main() -> None:
    for (scraper, name) in ALL_SCRAPERS:
        print(f'----- {name} -----')
        for record in scraper.fetch():
            print(record)


if __name__ == '__main__':
    main()
