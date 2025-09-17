import serial
import time

# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('COM4', 115200, timeout=1)

def readarduino():
    """Reads a line from Arduino and returns True if target detected, False otherwise"""
    while True:
        if ser.in_waiting > 0:  # only read if data is available
            data = ser.readline().decode(errors='ignore').strip().lower()
            if "stationary target" in data or "moving target" in data:
                print("1 or more targets have been found (target detected)")
                return True
            elif "no target" in data:
                print("no target")
                return False

if __name__ == '__main__':
    while True:
        status = readarduino()
        print("Status:", status)
        time.sleep(1)
