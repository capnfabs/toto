from dmhub import DmHub
from iris import IrisScraper


def main():
    iris = IrisScraper('iris-brf', 5, 'Berliner Rundfunk')
    for record in iris.fetch():
        print(record)

    iris = IrisScraper('iris-rs2', 7, 'RS2')
    for record in iris.fetch():
        print(record)

    iris = IrisScraper('iris-kissfm', 3, 'KissFM')
    for record in iris.fetch():
        print(record)

    dm = DmHub('104.6rtl.com', 'rtl', 'rtl')
    for x in dm.fetch():
        print(x)

    dm = DmHub('www.jam.fm', 'jam', 'jamfm')
    for x in dm.fetch():
        print(x)

    dm = DmHub('spreeradio.de', 'spree', 'spreeradio')
    for x in dm.fetch():
        print(x)

if __name__ == '__main__':
    main()
