#!/usr/bin/env python3
import serial

from .fport import FportParser, FportMessageControl

if __name__ == '__main__':
    def handler(message):
        if type(message) is FportMessageControl:
            #print("Handled:", message)
        pass
    parser = FportParser(handler)
    if False:
        f = open("./fport.log", 'rb')
        while f.readable():
            d = array.array('B')
            d.fromfile(f, 30)
            parser.parse(d)

            # print(parser.buffer)
    else:
        try:
            with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
                while True:
                    s = ser.read()
                    parser.parse(s)
        finally:
            ui.close()