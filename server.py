import serial
import time
import re
import sqlite3
from datetime import datetime
import requests

# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('/dev/cu.usbserial-58EF0570731', 115200, timeout=1)
def send_to_server(ts, room_id, ledighed=None, co2ppm=None):
    url = "https://MichaelH.pythonanywhere.com/upload"
    payload = {
        "ts": ts,#timestamp
        "room_id": room_id,#Rumid
        "ledighed": ledighed,#er det ledigt?
        "co2ppm": co2ppm #co2?
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        print("Oploader:", r.status_code, r.text)#burde sende 200 = success at sende
    except Exception as e:
        print("Kunne ikke opload data", e)


def readarduino():
    """Reads a line from Arduino, logs it with timestamp, and returns status info"""
    if ser.in_waiting > 0:  # only read if data is available
        data = ser.readline().decode(errors='ignore').strip()
        datal = data.lower()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_line = None
        room_id = 2  # adjust if multiple rooms/sensors
        m = re.search(r"(stationary|moving) target: (\d+)cm energy:(\d+)", datal)
        if m:
            _, dist, energy = m.groups()
            status_line = f"{ts} | room={room_id} | occupied | distance={dist} | energy={energy}"
            send_to_server(ts, room_id, ledighed="occupied")


        elif "no target" in datal:
            status_line = f"{ts} | room={room_id} | free"
            send_to_server(ts, room_id, ledighed="free")

        co2_match = re.search(r"co2[:= ]+(\d+)", datal)
        if co2_match:
            co2ppm = int(co2_match.group(1))
            send_to_server(ts, room_id, co2ppm=co2ppm)
            status_line = f"{ts} | room={room_id} | CO2={co2ppm} ppm"

        # Print to console as well
        print(status_line)
        return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
