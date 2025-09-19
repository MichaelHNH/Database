import serial
import time

# Open the serial connection (adjust COM port and baudrate if needed)
ser = serial.Serial('COM4', 115200, timeout=1)

def readarduino():
    """Reads a line from Arduino and returns True if target detected, False otherwise"""
    while True:
        if ser.in_waiting > 0: # only read if data is available
            data = ser.readline().decode(errors='ignore').strip()
            print("RAW:", data)  # vi har nu et debug print så vi kan tjekke om vi faktisk får data. hjælper med at se om programmet kører ordenligt ved at printe den "rå" data.
            if "Stationary target" in data or "Moving target" in data: # fandt fejlen, den leder efter noget som var for specifkt, så den skal bare lede efter keywords
                print("1 or more targets have been found (target detected)")
                print("Raw data:", data) # printer den data vi får fra sensoren her.
        return True
            elif "no target" in data:
                print("no target")
                return False


if __name__ == '__main__':
    while True:
        status = readarduino()
        print("Status:", status)
        time.sleep(1)
