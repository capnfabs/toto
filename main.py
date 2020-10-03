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
    (IrisScraper('iris-brf', 5), 'Berliner Rundfunk'),
    (IrisScraper('iris-rs2', 7), 'RS2'),
    (IrisScraper('iris-kissfm', 3), 'KissFM'),
    (DmHub('104.6rtl.com', 'rtl'), 'rtl'),
    (DmHub('www.jam.fm', 'jam'), 'jamfm'),
    (DmHub('spreeradio.de', 'spree'), 'spreeradio'),
    (StarFm(), 'starfm'),
    (Rbb('radioberlin'), 'rbb'),
    (Rbb('antenne_brandenburg'), 'antenne_brandenburg'),
    (Energy(), 'energy_berlin'),
    (FluxFM(), 'fluxfm'),
    (RadioParadiso(), 'paradiso'),
    (RadioEins(), 'rbb_radio_eins'),
    (WdrCosmo(), 'wdr_cosmo'),
]


def main() -> None:
    for (scraper, name) in ALL_SCRAPERS:
        print(f'----- {name} -----')
        for record in scraper.fetch():
            print(record)


if __name__ == '__main__':
    main()
