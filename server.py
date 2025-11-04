import serial
import time
import re
import sqlite3
from datetime import datetime
import requests

nr_id = 1
presence_sensor = 1
CO2_sensor = 2
# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('/dev/cu.usbserial-58EF0570731', 115200, timeout=1)

def send_to_server(ts, sensor_id, værdi ):
    url = "https://MichaelH.pythonanywhere.com/upload"
    payload = {
        "nr_id": nr_id,
        "ts": ts,#timestamp
        "sensor_id": sensor_id,#Rumid
        "værdi": værdi #er det ledigt?
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        print("Oploader:", r.status_code, r.text)#burde sende 200 = success at sende
    except Exception as e:
        print("Kunne ikke opload data", e)


def readarduino():
    global presence_sensor
    global CO2_sensor
    global nr_id

    """Reads a line from Arduino, logs it with timestamp, and returns status info"""
    if ser.in_waiting > 0:  # only read if data is available
        data = ser.readline().decode(errors='ignore').strip()
        datal = data.lower()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_line = None


        m = re.search(r"(stationary|moving) target: (\d+)cm energy:(\d+)", datal)
        if m:
            værdi = "occupied"
            sensor_id = presence_sensor
            _, dist, energy = m.groups()
            status_line = f"{ts} | sensor_id={sensor_id} | værdi={værdi} | distance={dist} | energy={energy}"
            send_to_server(nr_id, ts, sensor_id, værdi)

        elif "no target" in datal:
            værdi = "free"
            sensor_id = presence_sensor
            status_line = f"{ts} | sensor_id={sensor_id} | værdi={værdi} "
            send_to_server(nr_id, ts, sensor_id, værdi)
            nr_id += 1

        co2_match = re.search(r"co2[:= ]+(\d+)", datal)
        if co2_match:
            sensor_id = CO2_sensor
            værdi = int(co2_match.group(1))
            send_to_server(nr_id, ts, sensor_id, værdi)
            status_line = f"{ts} | room={sensor_id} | CO2={værdi} ppm"
            nr_id += 1

        # Print to console as well
        print(status_line)
        return status_line

if __name__ == '__main__':
    while True:
        status = readarduino()
        time.sleep(1)
