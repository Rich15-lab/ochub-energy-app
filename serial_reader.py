import serial
import json
import time

SERIAL_PORT = '/dev/ttyUSB0'  # or COM3 on Windows (update this)
BAUD_RATE = 9600
DATA_FILE = 'sensor_data.json'

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # Wait for ESP32 to boot

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            parts = line.split(",")
            if len(parts) == 3:
                voltage = float(parts[0])
                intensity = float(parts[1])
                duration = float(parts[2])
                with open(DATA_FILE, 'w') as f:
                    json.dump({
                        "voltage": voltage,
                        "intensity": intensity,
                        "duration": duration
                    }, f)
                print(f"Logged: {voltage}, {intensity}, {duration}")
    except Exception as e:
        print("Error:", e)
