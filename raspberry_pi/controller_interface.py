import time
import serial


class IMUController:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        time.sleep(2)  # let the MCU reset
        self.ser.reset_input_buffer()

    def get_action(self):
        while True:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            # Expected MCU output:
            # DATA,LEFT,0.000000,2.829885,...
            parts = line.split(",")

            if len(parts) >= 2 and parts[0] == "DATA":
                gesture = parts[1].strip().upper()

                if gesture in {"LEFT", "RIGHT", "UP"}:
                    return gesture