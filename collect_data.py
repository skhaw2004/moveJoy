"""
MoveJoy v2 — Gesture Data Collection
--------------------------------------
Collects YOLO keypoints for training a gesture classifier.

Gestures to collect: UP, LEFT, RIGHT, IDLE

Controls:
  Click and hold a button to record that gesture
  Release mouse to stop recording
  Q — quit and save
"""

import cv2
import csv
import os
import time
from ultralytics import YOLO

# ── Config ──────────────────────────────────────────────────────────────────
OUTPUT_CSV  = 'gesture_data.csv'
MODEL_PATH  = 'yolov8n-pose.pt'
# ────────────────────────────────────────────────────────────────────────────

model = YOLO(MODEL_PATH)
cap   = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open camera.")
    exit()

# Load existing data if file already exists
existing_rows = 0
file_exists = os.path.exists(OUTPUT_CSV)
if file_exists:
    with open(OUTPUT_CSV, 'r') as f:
        existing_rows = sum(1 for _ in f) - 1
    print(f"Existing data found: {existing_rows} samples")

csv_file = open(OUTPUT_CSV, 'a', newline='')
writer   = csv.writer(csv_file)

if not file_exists:
    header = ['label']
    for i in range(17):
        header += [f'kp{i}_x', f'kp{i}_y', f'kp{i}_conf']
    writer.writerow(header)

# ── Button layout ────────────────────────────────────────────────────────────
BUTTONS = [
    { 'label': 'up',    'display': '⬆  UP',    'color': (50, 180, 50)  },
    { 'label': 'left',  'display': '⬅  LEFT',  'color': (50, 130, 220) },
    { 'label': 'right', 'display': '➡  RIGHT', 'color': (220, 100, 50) },
    { 'label': 'idle',  'display': '○  IDLE',  'color': (130, 130, 130)},
]
BTN_W, BTN_H = 130, 50
BTN_Y        = 10
BTN_GAP      = 10

# State
recording       = False
current_label   = None
mouse_held      = False
sample_count    = 0
total_collected = { b['label']: 0 for b in BUTTONS }
keypoints_row   = None


def get_button_rects(frame_w):
    total = len(BUTTONS) * BTN_W + (len(BUTTONS) - 1) * BTN_GAP
    start_x = (frame_w - total) // 2
    rects = []
    for i in range(len(BUTTONS)):
        x = start_x + i * (BTN_W + BTN_GAP)
        rects.append((x, BTN_Y, x + BTN_W, BTN_Y + BTN_H))
    return rects


def point_in_rect(px, py, rect):
    x1, y1, x2, y2 = rect
    return x1 <= px <= x2 and y1 <= py <= y2


def mouse_callback(event, x, y, flags, param):
    global recording, current_label, mouse_held, sample_count
    rects = get_button_rects(param['frame_w'])

    if event == cv2.EVENT_LBUTTONDOWN:
        for i, rect in enumerate(rects):
            if point_in_rect(x, y, rect):
                current_label = BUTTONS[i]['label']
                recording     = True
                mouse_held    = True
                sample_count  = 0
                print(f"Recording: {current_label.upper()} — release mouse to stop")
                break

    elif event == cv2.EVENT_LBUTTONUP:
        if mouse_held and recording:
            print(f"Stopped. Collected {sample_count} samples for {current_label.upper()}")
        mouse_held = False
        recording  = False


frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
cv2.namedWindow('MoveJoy v2 - Data Collection (Q to quit)')
cv2.setMouseCallback('MoveJoy v2 - Data Collection (Q to quit)',
                     mouse_callback, {'frame_w': frame_w})

print("\n=== GESTURE DATA COLLECTION ===")
print("Click and hold a button to record — release to stop")
print("Press Q to quit and save\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, persist=True, verbose=False)
    annotated = frame.copy()

    if results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
        kps = results[0].keypoints.data[0]
        annotated = results[0].plot()

        h, w = frame.shape[:2]
        row = []
        for kp in kps:
            row += [float(kp[0]) / w, float(kp[1]) / h, float(kp[2])]
        keypoints_row = row

        if recording and current_label and keypoints_row:
            writer.writerow([current_label] + keypoints_row)
            sample_count += 1
            total_collected[current_label] = total_collected.get(current_label, 0) + 1
    else:
        keypoints_row = None

    # ── Draw buttons ─────────────────────────────────────────────────────────
    frame_w = annotated.shape[1]
    rects   = get_button_rects(frame_w)

    for i, btn in enumerate(BUTTONS):
        x1, y1, x2, y2 = rects[i]
        is_active = recording and current_label == btn['label']
        color     = btn['color']
        bg_color  = tuple(min(255, int(c * 1.4)) for c in color) if is_active else (40, 40, 40)
        border    = color if is_active else (100, 100, 100)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), bg_color, -1)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), border, 2)
        cv2.putText(annotated, btn['display'], (x1 + 10, y1 + 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # ── Status bar ───────────────────────────────────────────────────────────
    bar_y = annotated.shape[0] - 70
    cv2.rectangle(annotated, (0, bar_y), (annotated.shape[1], annotated.shape[0]), (30, 30, 30), -1)

    if recording:
        status = f"RECORDING: {current_label.upper()}  —  {sample_count} samples this burst"
        cv2.putText(annotated, status, (10, bar_y + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 80, 255), 2)
        if int(time.time() * 2) % 2 == 0:
            cv2.circle(annotated, (annotated.shape[1] - 20, bar_y + 20), 10, (0, 0, 255), -1)
    else:
        cv2.putText(annotated, "Click and hold a button above to record",
                    (10, bar_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 80), 2)

    counts_text = "   ".join([f"{b['label'].upper()}: {total_collected[b['label']]}" for b in BUTTONS])
    cv2.putText(annotated, counts_text, (10, bar_y + 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

    cv2.imshow('MoveJoy v2 - Data Collection (Q to quit)', annotated)

    key = cv2.waitKey(1) & 0xFF
    if key != 255 and chr(key).lower() == 'q':
        break

cap.release()
csv_file.close()
cv2.destroyAllWindows()

print("\n=== COLLECTION COMPLETE ===")
print(f"Saved to: {OUTPUT_CSV}")
for b in BUTTONS:
    print(f"  {b['label'].upper()}: {total_collected[b['label']]} samples")
print(f"  Total this session: {sum(total_collected.values())} samples")
if existing_rows > 0:
    print(f"  Grand total (including previous): {existing_rows + sum(total_collected.values())} samples")
