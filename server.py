import serial
import time

def readarduino():
    while True:
        data = ser.readline().decode().strip()
        if "stationarytarget" in data or "movingtarget" in data:
            return true
        elif "notarget" in data:
            return false

while True:
    status = readarduino

    time.sleep(1)

if __name__ == '__main__':
    True