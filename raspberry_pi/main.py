# main.py
from display import GameDisplay

def main():
    display = GameDisplay()

    actions = ["LEFT", "RIGHT", "UP"]

    display.show_message("Memorise the sequence")
    for action in actions:
        display.show_action(action, duration=1.5)
        display.show_message("")

    display.show_message("Now perform the actions")
    display.show_message("Waiting for controller input...")

    display.wait_for_key()
    display.show_message("Correct!")

    display.close()

if __name__ == "__main__":
    main()