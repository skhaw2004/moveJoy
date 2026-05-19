# controller_interface.py

class MockController:

    def get_action(self):
        action = input(
            "Simulate controller action (LEFT/RIGHT/UP): "
        )

        return action.strip().upper()