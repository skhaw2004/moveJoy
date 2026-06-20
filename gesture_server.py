"""
MoveJoy v2 — Gesture WebSocket Server
---------------------------------------
Runs YOLO multi-person tracking + trained gesture classifier.
Broadcasts gesture events to the browser game via WebSocket.

Architecture:
  - Camera/YOLO runs in a background thread
  - WebSocket server runs in asyncio main thread
  - Gestures passed between threads via asyncio.Queue

Messages sent to browser:
  {"type": "gesture", "gesture": "UP"}
  {"type": "gesture", "gesture": "LEFT"}
  {"type": "gesture", "gesture": "RIGHT"}
  {"type": "status", "connected": true}

Usage:
  python3 gesture_server.py
Then open the game in the browser.
"""

import asyncio
import json
import time
import threading
import cv2
import numpy as np
import tensorflow as tf
import websockets
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────────────
YOLO_MODEL        = 'yolov8n-pose.pt'
GESTURE_MODEL     = 'gesture_model.keras'
GESTURE_LABELS    = 'gesture_labels.json'
WS_HOST           = 'localhost'
WS_PORT           = 8765
CONFIDENCE_THRESH = 0.7
MIN_HOLD_FRAMES   = 2
GESTURE_COOLDOWN  = 0.5   # seconds
# ─────────────────────────────────────────────────────────────────────────────

print("Loading models...")
yolo       = YOLO(YOLO_MODEL)
classifier = tf.keras.models.load_model(GESTURE_MODEL)
with open(GESTURE_LABELS) as f:
    label_map = json.load(f)
print("Models loaded.\n")

# Shared state
connected_clients   = set()
gesture_queue       = None   # asyncio.Queue, created in main thread
main_event_loop     = None
camera_reset_event  = threading.Event()  # set when browser reconnects to re-register player


# ── Camera thread ─────────────────────────────────────────────────────────────

def camera_thread():
    """Runs YOLO + classifier in a background thread. Puts gestures into queue."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    main_player_id    = None
    gesture_candidate = None
    candidate_frames  = 0
    last_fired        = None
    last_fired_time   = 0
    idle_frames       = 0
    IDLE_RESET_FRAMES = 6   # consecutive idle frames before allowing same gesture to repeat

    print("[Camera] Thread started")

    frame_count = 0

    while True:
        # Reset player registration when browser reconnects
        if camera_reset_event.is_set():
            camera_reset_event.clear()
            main_player_id    = None
            gesture_candidate = None
            candidate_frames  = 0
            last_fired        = None
            last_fired_time   = 0
            idle_frames       = 0
            print("[Camera] Player reset — waiting to register new player")

        try:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame_count += 1
            h, w = frame.shape[:2]

            # Reset YOLO tracker every 500 frames to prevent memory buildup
            if frame_count % 500 == 0:
                print(f"[Camera] Resetting tracker (frame {frame_count})")
                yolo.predictor = None

            results = yolo.track(frame, persist=True, verbose=False)
            boxes     = results[0].boxes
            keypoints = results[0].keypoints

            if boxes is None or keypoints is None:
                continue

            # Auto-register first detected person
            if main_player_id is None and len(boxes) > 0:
                first_id = boxes[0].id
                if first_id is not None:
                    main_player_id = int(first_id[0])
                    print(f"[Camera] Main player registered: ID {main_player_id}")

            # Find main player
            for i, box in enumerate(boxes):
                try:
                    track_id = int(box.id[0]) if box.id is not None else None
                except Exception:
                    continue

                if track_id != main_player_id:
                    continue
                if i >= len(keypoints.data):
                    continue

                # Extract + normalise keypoints
                kps = keypoints.data[i]
                row = []
                for kp in kps:
                    row += [float(kp[0]) / w, float(kp[1]) / h, float(kp[2])]

                input_data = np.array([row], dtype=np.float32)
                prediction = classifier(input_data, training=False).numpy()[0]
                class_idx  = int(np.argmax(prediction))
                confidence = float(prediction[class_idx])
                gesture    = label_map[str(class_idx)].upper()

                now = time.time()
                cooldown_elapsed = (now - last_fired_time) >= GESTURE_COOLDOWN

                if gesture == 'IDLE' or confidence < CONFIDENCE_THRESH:
                    gesture_candidate = None
                    candidate_frames  = 0
                    idle_frames += 1
                    if idle_frames >= IDLE_RESET_FRAMES:
                        last_fired = None
                else:
                    idle_frames = 0
                    if gesture == gesture_candidate:
                        candidate_frames += 1
                    else:
                        gesture_candidate = gesture
                        candidate_frames  = 1

                    if (candidate_frames >= MIN_HOLD_FRAMES
                            and gesture != last_fired
                            and cooldown_elapsed):
                        print(f"[Gesture] {gesture} ({confidence:.2f})")
                        last_fired      = gesture
                        last_fired_time = now
                        if gesture_queue and main_event_loop:
                            main_event_loop.call_soon_threadsafe(
                                gesture_queue.put_nowait,
                                {"type": "gesture", "gesture": gesture}
                            )

                break  # only process main player

        except Exception as e:
            print(f"[Camera] Error: {e}")
            time.sleep(0.05)
            continue

    cap.release()


# ── WebSocket server ───────────────────────────────────────────────────────────

async def broadcast(message: dict):
    if connected_clients:
        data = json.dumps(message)
        await asyncio.gather(
            *[ws.send(data) for ws in list(connected_clients)],
            return_exceptions=True
        )


async def handle_client(websocket):
    connected_clients.add(websocket)
    print(f"[WS] Browser connected. Clients: {len(connected_clients)}")
    camera_reset_event.set()  # new page load — re-register player
    await websocket.send(json.dumps({"type": "status", "connected": True}))
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong"}))
                elif data.get("type") == "register_player":
                    camera_reset_event.set()
                    print("[Camera] Player registration requested by browser")
            except Exception:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Browser disconnected. Clients: {len(connected_clients)}")


async def queue_broadcaster():
    """Reads gestures from queue and broadcasts to all connected clients."""
    while True:
        msg = await gesture_queue.get()
        await broadcast(msg)


async def main():
    global gesture_queue, main_event_loop
    gesture_queue   = asyncio.Queue()
    main_event_loop = asyncio.get_event_loop()

    # Start camera thread
    t = threading.Thread(target=camera_thread, daemon=True)
    t.start()

    # Start broadcaster
    asyncio.create_task(queue_broadcaster())

    async with websockets.serve(handle_client, WS_HOST, WS_PORT):
        print(f"[WS] Server ready on ws://{WS_HOST}:{WS_PORT}")
        print(f"[WS] Open the game in your browser\n")
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
