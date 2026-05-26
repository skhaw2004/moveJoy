import random

from display import GameDisplay
from controller_interface import IMUController


def main():
    print("MoveJoy starting...")

    display = GameDisplay()

    # Change this to your actual serial port
    controller = IMUController(port="/dev/tty.usbmodem3101")

    actions = ["LEFT", "RIGHT", "UP"]
    sequence_length = 5
    score = 0

    sequence = [random.choice(actions) for _ in range(sequence_length)]

    display.show_message("Get Ready!", duration=2)
    display.show_sequence(sequence, duration=5)

    display.clear()
    display.show_message("Now repeat the sequence!", duration=2)

    for i, expected_action in enumerate(sequence, start=1):
        display.show_message(f"Move {i} of {sequence_length}")
        display.show_message("Do the action now")

        detected_action = controller.get_action()
        print(f"Expected: {expected_action}, Detected: {detected_action}")

        if detected_action == expected_action:
            score += 1
            display.show_message("Correct!", duration=1)
        else:
            display.show_message(f"Wrong! Expected {expected_action}", duration=1)

    display.show_message(f"Final Score: {score}/{sequence_length}", duration=3)
    display.clear()
    display.show_message("Game Over", duration=2)


if __name__ == "__main__":
    main()