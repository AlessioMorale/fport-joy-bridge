#!/usr/bin/env python3
from evdev import UInput, UInputError, ecodes, AbsInfo
from evdev import util
from fport import FportParser, FportMessageControl
import serial

from time import sleep
if __name__ == '__main__':
    device = None

    def handler(message):
        if type(message) is FportMessageControl:
            print("Handled:", message)
        pass
        if False:
            counter = counter + 1
            device.write(ecodes.EV_ABS, ecodes.ABS_X, counter % 255)
            device.syn()
    try:
        description = 'TstAM'
        default_props = AbsInfo(value=0, min=0, max=2048, fuzz=0, flat=0, resolution=0)
        events = {ecodes.EV_ABS: [
            (ecodes.ABS_X, default_props),
            (ecodes.ABS_Y, default_props),
            (ecodes.ABS_Z, default_props),
            (ecodes.ABS_RZ, default_props)
        ], ecodes.EV_KEY:[], ecodes.EV_REL: []}

        device = UInput(events=events)
        counter = 0
        parser = FportParser(handler)
        ui = UInput()
        with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
            while True:
                s = ser.read(100)
                parser.parse(s)
    finally:
        device.close()
        pass