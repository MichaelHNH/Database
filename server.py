import serial
import time
import re
import sqlite3
from datetime import datetime

# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('COM4', 115200, timeout=1)
connect = sqlite3.connect('database.db')
connect.execute(
    'CREATE TABLE IF NOT EXISTS LEDIGHED (ts TEXT, \
    room_id TEXT, ledighed TEXT)'
)
connect.execute(
    'CREATE TABLE IF NOT EXISTS CO2DATA (ts TEXT, \
    room_id TEXT, co2ppm INTEGER)'
)


def readarduino():
    """Reads a line from Arduino, logs it with timestamp, and returns status info"""
    if ser.in_waiting > 0:  # only read if data is available
        data = ser.readline().decode(errors='ignore').strip()
        datal = data.lower()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_line = None
        room_id = 1  # adjust if multiple rooms/sensors
        m = re.search(r"(stationary|moving) target: (\d+)cm energy:(\d+)", datal)
        if m:
            _, dist, energy = m.groups()
            status_line = f"{ts} | room={room_id} | occupied | distance={dist} | energy={energy}"
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute(
                    "INSERT INTO LEDIGHED (ts,room_id,ledighed) VALUES (?,?,?)",
                    (ts, room_id, "occupied")
                )
                users.commit()

        elif "no target" in datal:
            status_line = f"{ts} | room={room_id} | free"
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute(
                    "INSERT INTO LEDIGHED (ts,room_id,ledighed) VALUES (?,?,?)",
                    (ts, room_id, "free")
                )
                users.commit()

        co2_match = re.search(r"co2[:= ]+(\d+)", datal)
        if co2_match:
            co2ppm = int(co2_match.group(1))
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute(
                    "INSERT INTO CO2DATA (ts,room_id,co2ppm) VALUES (?,?,?)",
                    (ts, room_id, co2ppm)
                )
                users.commit()
            status_line = f"{ts} | room={room_id} | CO2={co2ppm} ppm"

        # --- Unknown line fallback ---
        if status_line is None:
            status_line = f"{ts} | unknown | raw={data}"

        with open("database.txt", "a", encoding="utf-8") as f:
            f.write(status_line + "\n")

        # Print to console as well
        print(status_line)
        return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
