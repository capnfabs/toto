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

if __name__ == '__main__':
    main()
