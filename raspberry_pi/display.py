import time
import tkinter as tk


class GameDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MoveJoy")
        self.root.geometry("800x500")
        self.root.configure(bg="white")

        self.label = tk.Label(
            self.root,
            text="",
            font=("Arial", 32, "bold"),
            bg="white",
            fg="black",
            wraplength=760,
            justify="center",
        )
        self.label.pack(expand=True, fill="both")
        self.root.update()

    def _refresh(self):
        self.root.update_idletasks()
        self.root.update()

    def _sleep_with_updates(self, seconds):
        end_time = time.time() + seconds
        while time.time() < end_time:
            self._refresh()
            time.sleep(0.01)

    def show_message(self, text, duration=0):
        self.label.config(text=text, font=("Arial", 32, "bold"))
        self._refresh()

        if duration > 0:
            self._sleep_with_updates(duration)

    def show_sequence(self, sequence, duration=5):
        text = "   ".join(sequence)
        self.label.config(text=text, font=("Arial", 36, "bold"))
        self._refresh()
        self._sleep_with_updates(duration)

    def clear(self):
        self.label.config(text="")
        self._refresh()