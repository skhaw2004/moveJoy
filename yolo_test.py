"""
MoveJoy v2 — YOLO Multi-Person Pose Detection Test
---------------------------------------------------
This is a standalone test to check if YOLOv8 can:
  - Detect multiple people in frame simultaneously
  - Assign consistent tracking IDs to each person
  - Handle people clustering together

Controls:
  Q — quit
"""

import cv2
from ultralytics import YOLO

# Load the smallest/fastest pose model (downloads automatically on first run)
model = YOLO('yolov8n-pose.pt')

# Open laptop camera (change 0 to 1 if using an external camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("Camera opened. Press Q to quit.")
print("Watch for:")
print("  - Skeletons drawn on each person")
print("  - Tracking IDs shown above each person")
print("  - IDs staying consistent as people move")

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to read frame.")
        break

    # Run YOLO tracking (persist=True keeps IDs consistent across frames)
    results = model.track(frame, persist=True, verbose=False)

    # Draw skeletons + IDs on frame
    annotated = results[0].plot()

    # Show how many people are detected
    num_people = len(results[0].boxes) if results[0].boxes is not None else 0
    cv2.putText(annotated, f'People detected: {num_people}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('MoveJoy v2 - YOLO Pose Test (Q to quit)', annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Test ended.")
