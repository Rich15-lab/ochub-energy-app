import serial
import json
import time

# 👇 CHANGE THIS to match your ESP32 serial port
SERIAL_PORT = "/dev/cu.usbserial-0001"
BAUD_RATE = 115200

def get_mock_energy_data(raw_value):
    voltage = round((raw_value / 1023.0) * 3.3, 2)  # Convert to 0–3.3V range
    intensity = round((raw_value / 1023.0) * 10, 1)  # 0–10 scale
    duration = round(0.5 + (raw_value % 200) / 100.0, 2)  # 0.5–2.5 sec range
    return {
        "voltage": voltage,
        "intensity": intensity,
        "duration": duration
    }

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Connected to {SERIAL_PORT}")

        while True:
            line = ser.readline().decode().strip()
            if line.startswith("Piezo value:"):
                raw = int(line.split(":")[1].strip())
                data = get_mock_energy_data(raw)

                with open("sensor_data.json", "w") as f:
                    json.dump(data, f)

                print(f"📡 Saved: {data}")

            time.sleep(0.1)

    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
