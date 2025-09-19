import serial
import time
import re
from datetime import datetime

# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('COM4', 115200, timeout=1)

def readarduino():
    """Reads a line from Arduino, logs it with timestamp, and returns status info"""
    while True:
        if ser.in_waiting > 0:  # only read if data is available
            data = ser.readline().decode(errors='ignore').strip()
            datal = data.lower()
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_line = None
            if "stationary target" in datal:
                # Extract distance and energy with regex
                m = re.search(r"stationary target: (\d+)cm energy:(\d+)", datal)
                if m:
                    dist, energy = m.groups()
                    status_line = f"{ts} | stationary | distance={dist} | energy={energy}"
                else:
                    status_line = f"{ts} | stationary | raw={data}"

            elif "moving target" in datal:
                m = re.search(r"moving target: (\d+)cm energy:(\d+)", datal)
                if m:
                    dist, energy = m.groups()
                    status_line = f"{ts} | moving | distance={dist} | energy={energy}"
                else:
                    status_line = f"{ts} | moving | raw={data}"

            elif "no target" in datal:
                status_line = f"{ts} | no target"

            else:
                # vi får nogle gange data som er irrelevant, så vi ignorer dem.
                status_line = f"{ts} | unknown | raw={data}"
            with open("database.txt", "a", encoding="utf-8") as f:
                f.write(status_line + "\n")
            print(status_line)

            return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
