import random
import time

actions = ["HEART", "STAR", "SIUsT"]

sequence = random.sample(actions, 3)

print("Memorise this sequence:")
print(" -> ".join(sequence))

time.sleep(3)

print("\n" * 20)
user_input = input("Enter the sequence separated by spaces: ").strip().upper().split()

if user_input == sequence:
    print("Correct!")
else:
    print("Wrong!")
    print("Expected:", sequence)
    print("Got:", user_input)