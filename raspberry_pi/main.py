import random

from display import GameDisplay
from controller_interface import IMUController
# from controller_interface import KeyboardController


def main():
    print("MoveJoy starting...")

    display = GameDisplay()

    # CHANGE THIS to your real serial port
    controller = IMUController(
    port="/dev/tty.usbmodem3101"
    )

    # For keyboard testing instead of IMU:
    # controller = KeyboardController()

    actions = ["LEFT", "RIGHT", "UP"]

    sequence_length = 5
    score = 0

    # Generate random sequence
    sequence = [
        random.choice(actions)
        for _ in range(sequence_length)
    ]

    # Intro screen
    display.show_message(
        "Get Ready!",
        duration=2
    )

    # Show full sequence
    sequence_text = "   ".join(sequence)

    display.show_message(
        sequence_text,
        duration=5
    )

    # Prompt user
    display.show_message(
        "Repeat the sequence",
        duration=2
    )

    # Read gestures one by one
    for i, expected_action in enumerate(sequence):

        display.show_message(
            f"Action {i + 1} of {sequence_length}",
            duration=1
        )

        user_action = controller.get_action(
            timeout=5
        )

        print("Expected:", expected_action)
        print("User:", user_action)

        if user_action == expected_action:
            score += 1

            display.show_message(
                "Correct!",
                duration=1
            )

        else:
            display.show_message(
                f"Wrong! {user_action}",
                duration=1
            )

    # Final score
    display.show_message(
        f"Score: {score}/{sequence_length}",
        duration=3
    )

    display.close()


if __name__ == "__main__":
    main()