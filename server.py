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
    room_id TEXT, ledighed TEXT)')


def readarduino():
    """Reads a line from Arduino, logs it with timestamp, and returns status info"""
    if ser.in_waiting > 0:  # only read if data is available
        data = ser.readline().decode(errors='ignore').strip()
        datal = data.lower()

        # Current timestamp
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_line = None

        # Match both stationary and moving targets
        m = re.search(r"(stationary|moving) target: (\d+)cm energy:(\d+)", datal)
        room_id = 1  # 1 = rum 1, det skal være der hvor senssoren er

        if m:
            _, dist, energy = m.groups()
            status_line = f"{ts} | room={room_id} | occupied | distance={dist} | energy={energy}"  # Måske mange ligegyldige variabler?
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute("INSERT INTO LEDIGHED \
                (ts,room_id,ledighed) VALUES (?,?,?)",
                               (ts, room_id, "ocupied"))
                users.commit()

        elif "no target" in datal:
            status_line = f"{ts} | room={room_id} | free"
            with sqlite3.connect("database.db") as users:
                cursor = users.cursor()
                cursor.execute("INSERT INTO LEDIGHED \
                (ts,room_id,ledighed) VALUES (?,?,?)",
                               (ts, room_id, "free"))
                users.commit()

        else:
            # Ignore unrelated lines, but still log them
            status_line = f"{ts} | unknown | raw={data}"

        return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
