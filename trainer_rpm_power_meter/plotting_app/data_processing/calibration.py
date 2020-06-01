#!/usr/bin/env python3

from wifi_client import WifiClient
from time import sleep
from threading import Thread


def main():
    wc = WifiClient()
    # write calibration code here
    wc.connect()
    try:
        input("press <enter> to start")
        worker = Thread(target=wc.poll)
        worker.daemon = True
        worker.start()
        fname = 'data.txt'
        file_ = open(fname, 'w')
        while True:
            sleep(1)
            print(wc.rpm)
            print(wc.rpm, file=file_)
    except KeyboardInterrupt:
        file_.close()


if __name__ == "__main__":
    main()
