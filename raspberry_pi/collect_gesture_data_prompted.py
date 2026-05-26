import csv
import time
from pathlib import Path

import serial

PORT = "/dev/tty.usbmodem3101"   # change if needed
BAUDRATE = 115200
SAMPLES_PER_GESTURE = 20

GESTURES = ["LEFT", "RIGHT", "UP"]
OUTPUT_FILE = Path(__file__).with_name("gesture_data.csv")


def wait_for_data_line(ser):
    while True:
        raw = ser.readline()
        if not raw:
            continue

        line = raw.decode("utf-8", errors="ignore").strip()
        if line.startswith("DATA,"):
            return line


def parse_data_line(line):
    parts = line.split(",")
    # DATA,gesture,sumLX,sumLY,peakLX,peakLY,peakMag,windowMs
    if len(parts) != 8:
        return None

    return {
        "detected_label": parts[1],
        "sumLX": float(parts[2]),
        "sumLY": float(parts[3]),
        "peakLX": float(parts[4]),
        "peakLY": float(parts[5]),
        "peakMag": float(parts[6]),
        "windowMs": int(parts[7]),
    }


def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
    time.sleep(2)
    ser.reset_input_buffer()

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "intended_label",
            "detected_label",
            "sumLX",
            "sumLY",
            "peakLX",
            "peakLY",
            "peakMag",
            "windowMs",
        ])

        print("\nHold the IMU still when asked.")
        print("Do one clean gesture each time.\n")

        for label in GESTURES:
            for i in range(SAMPLES_PER_GESTURE):
                input(f"Prepare for {label} #{i + 1}. Press Enter, then do the gesture: ")
                ser.reset_input_buffer()

                print(f"Recording {label} #{i + 1} ...")

                line = wait_for_data_line(ser)
                data = parse_data_line(line)

                if data is None:
                    print("Skipped unreadable line:", line)
                    continue

                writer.writerow([
                    label,
                    data["detected_label"],
                    data["sumLX"],
                    data["sumLY"],
                    data["peakLX"],
                    data["peakLY"],
                    data["peakMag"],
                    data["windowMs"],
                ])
                f.flush()

                print(
                    f"Saved intended={label}, detected={data['detected_label']}"
                )

    print(f"\nDone. CSV saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()