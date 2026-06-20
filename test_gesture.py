"""
MoveJoy v2 — Live Gesture Detection Test
------------------------------------------
Uses YOLO for multi-person tracking + trained classifier for gesture recognition.

Controls:
  R — register the currently detected person as main player
  Q — quit
"""

import cv2
import json
import time
import numpy as np
import tensorflow as tf
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────────────
YOLO_MODEL      = 'yolov8n-pose.pt'
GESTURE_MODEL   = 'gesture_model.keras'
GESTURE_LABELS  = 'gesture_labels.json'
CONFIDENCE_THRESH = 0.7   # minimum confidence to display a gesture
# ─────────────────────────────────────────────────────────────────────────────

# Load models
print("Loading models...")
yolo      = YOLO(YOLO_MODEL)
classifier = tf.keras.models.load_model(GESTURE_MODEL)
with open(GESTURE_LABELS) as f:
    label_map = json.load(f)  # { "0": "idle", "1": "left", ... }

print("Models loaded.")
print("\n=== LIVE GESTURE TEST ===")
print("R — register main player")
print("Q — quit\n")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Could not open camera.")
    exit()

# State
main_player_id    = None   # YOLO tracking ID of registered player
current_gesture   = "—"
gesture_conf      = 0.0
last_detected_time = 0
FREEZE_TIMEOUT    = 2.0   # seconds without detection before auto-reregister

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    results = yolo.track(frame, persist=True, verbose=False)
    annotated = results[0].plot()

    boxes     = results[0].boxes
    keypoints = results[0].keypoints

    if boxes is not None and keypoints is not None:
        for i, box in enumerate(boxes):
            # Get tracking ID
            track_id = int(box.id[0]) if box.id is not None else None
            if track_id is None:
                continue

            # Highlight main player box in a different colour
            is_main = (track_id == main_player_id)
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if is_main:
                last_detected_time = time.time()
                # Green box for main player
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 80), 3)
                cv2.putText(annotated, f"MAIN PLAYER (ID {track_id})",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 80), 2)

                # Classify gesture for main player
                if i < len(keypoints.data):
                    kps = keypoints.data[i]  # shape [17, 3]
                    row = []
                    for kp in kps:
                        row += [float(kp[0]) / w, float(kp[1]) / h, float(kp[2])]

                    input_data = np.array([row], dtype=np.float32)
                    prediction = classifier(input_data, training=False).numpy()[0]
                    class_idx  = int(np.argmax(prediction))
                    confidence = float(prediction[class_idx])
                    gesture    = label_map[str(class_idx)].upper()

                    if confidence >= CONFIDENCE_THRESH:
                        current_gesture = gesture
                        gesture_conf    = confidence
                    else:
                        current_gesture = "—"
                        gesture_conf    = confidence
            else:
                # Grey label for other players
                cv2.putText(annotated, f"ID {track_id}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    # ── Auto-reregister if frozen ───────────────────────────────────────────
    if (main_player_id is not None
            and time.time() - last_detected_time > FREEZE_TIMEOUT
            and boxes is not None and len(boxes) > 0):
        first_id = boxes[0].id
        if first_id is not None:
            main_player_id     = int(first_id[0])
            last_detected_time = time.time()
            print(f"[Auto] Re-registered player: ID {main_player_id}")

    # ── Overlay UI ─────────────────────────────────────────────────────────
    cv2.rectangle(annotated, (0, 0), (w, 100), (30, 30, 30), -1)

    if main_player_id is None:
        cv2.putText(annotated, "No main player registered — press R",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
    else:
        cv2.putText(annotated, f"Gesture: {current_gesture}",
                    (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 80), 3)
        cv2.putText(annotated, f"Confidence: {gesture_conf * 100:.1f}%",
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

    cv2.putText(annotated, "R=Register  Q=Quit",
                (w - 220, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

    cv2.imshow('MoveJoy v2 - Gesture Test (Q to quit)', annotated)

    key = cv2.waitKey(1) & 0xFF
    key_char = chr(key).lower() if key != 255 else ''

    if key_char == 'r':
        # Register the first detected person as main player
        if boxes is not None and len(boxes) > 0:
            first_id = boxes[0].id
            if first_id is not None:
                main_player_id  = int(first_id[0])
                current_gesture = "—"
                print(f"Main player registered: ID {main_player_id}")
            else:
                print("Could not register — no tracking ID yet. Try again.")
        else:
            print("No person detected. Step into frame first.")

    elif key_char == 'q':
        break

cap.release()
cv2.destroyAllWindows()
print("Test ended.")
