from display import GameDisplay
from controller_interface import MockController
import random

def main():
    print("NEW MAIN FILE RUNNING")

    display = GameDisplay()
    controller = MockController()

    actions = ["LEFT", "RIGHT", "UP"]
    score = 0
    total_rounds = 5

    display.show_message("Get Ready!", duration=2)

    for round_number in range(total_rounds):
        target_action = random.choice(actions)

        display.show_message(f"Round {round_number + 1} of {total_rounds}", duration=1)

        display.show_action(target_action, duration=2)

        display.show_message("Perform the action", duration=1)

        user_action = controller.get_action()

        if user_action == target_action:
            score += 1
            display.show_message("Correct!", duration=1)
        else:
            display.show_message(f"Wrong! Expected {target_action}", duration=1)

    display.show_message(f"Final Score: {score}/{total_rounds}", duration=3)
    display.close()

if __name__ == "__main__":
    main()