import random
from display import GameDisplay
from controller_interface import MockController

def main():
    print("NEW MAIN FILE RUNNING")

    display = GameDisplay()
    controller = MockController()

    actions = ["LEFT", "RIGHT", "UP"]
    sequence_length = 5
    score = 0

    # Generate full sequence
    sequence = [random.choice(actions) for _ in range(sequence_length)]

    display.show_message("Get Ready!", duration=2)

    # Convert sequence into one string
    sequence_text = "   ".join(sequence)

    # Show ALL actions together for 5 seconds
    display.show_message(sequence_text, duration=5)

    # Hide sequence
    display.show_message("Now repeat the sequence", duration=2)

    # User inputs answers one by one
    for i, expected_action in enumerate(sequence):

        display.show_message(
            f"Input action {i + 1} of {sequence_length}",
            duration=1
        )

        user_action = controller.get_action()

        if user_action == expected_action:
            score += 1

    # Final score
    display.show_message(
        f"Final Score: {score}/{sequence_length}",
        duration=3
    )

    display.close()

if __name__ == "__main__":
    main()