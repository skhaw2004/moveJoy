# controller_interface.py

import time
import serial


class KeyboardController:

    def get_action(self):

        action = input(
            "Type action (LEFT/RIGHT/UP): "
        )

        return action.strip().upper()


class IMUController:

    VALID_ACTIONS = {
        "LEFT",
        "RIGHT",
        "UP"
    }

    def __init__(
        self,
        port,
        baudrate=115200,
        timeout=0.1
    ):

        self.ser = serial.Serial(
            port,
            baudrate=baudrate,
            timeout=timeout
        )

        # Give ESP32 time to reset
        time.sleep(2)

        # Clear startup junk
        self.ser.reset_input_buffer()

    def get_action(self, timeout=5):

        end_time = time.time() + timeout

        while time.time() < end_time:

            raw = self.ser.readline()

            if not raw:
                continue

            line = raw.decode(
                "utf-8",
                errors="ignore"
            ).strip().upper()

            if not line:
                continue

            print("Serial:", line)

            # If ESP32 prints exactly LEFT/RIGHT/UP
            if line in self.VALID_ACTIONS:
                return line

            # If ESP32 prints:
            # "Gesture detected: LEFT"
            if "GESTURE DETECTED:" in line:

                gesture = line.split(
                    ":",
                    1
                )[1].strip()

                if gesture in self.VALID_ACTIONS:
                    return gesture

        return None