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

            # Current timestamp
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            status_line = None

            # Match both stationary and moving targets
            m = re.search(r"(stationary|moving) target: (\d+)cm energy:(\d+)", datal)
            if m:
                _, dist, energy = m.groups()
                status_line = f"{ts} | target | distance={dist} | energy={energy}"

            elif "no target" in datal:
                status_line = f"{ts} | no target"

            else:
                # Ignore unrelated lines, but still log them
                status_line = f"{ts} | unknown | raw={data}"

            # Save to file
            with open("database.txt", "a", encoding="utf-8") as f:
                f.write(status_line + "\n")

            # Print to console as well
            print(status_line)

            return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
