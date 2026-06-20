# MoveJoy

A gamified memory and rhythm game with motion gesture control and BLE controller support, designed for elderly cognitive monitoring.

---

## Requirements

### Software
- Node.js (v18+)
- Python 3.9+
- Google Chrome (for Web Bluetooth support)
- PlatformIO (for flashing the ESP32 controller)

### Python packages
```
pip install -r requirements.txt
```

### Node packages
```
cd game
npm install
```

---

## Hardware

- Webcam (connected to the machine running the game)
- Seeed Studio XIAO ESP32S3 with 5 buttons and a vibration motor
- LiPo battery or USB power source for the ESP32

---

## Setup

### 1. Flash the controller

Open the `controller/` folder in PlatformIO (VS Code with PlatformIO extension) and upload `src/main.cpp` to the XIAO ESP32S3. After flashing, the controller can be powered by battery — no USB needed to run.

### 2. Start the gesture server

From the project root:
```
python3 gesture_server.py
```

This starts the webcam, loads the YOLO pose model and gesture classifier, and opens a WebSocket on port 8765. Leave this running in the background.

> On first run, `yolov8n-pose.pt` will be downloaded automatically (~6MB). Requires internet for this one-time download only.

### 3. Start the game server

```
cd game
node --experimental-sqlite server.js
```

The game is now running at `http://localhost:3000`.

### 4. Open the game

Open Chrome and go to `http://localhost:3000`.

> Chrome is required — Web Bluetooth (for the controller) only works in Chrome.

---

## Connecting the controller

1. Power on the ESP32 controller.
2. On the game home screen, click **CONNECT**.
3. Select **MoveJoy Controller** from the Bluetooth picker.
4. The button will change to **CONNECTED**.

After connecting once, the controller stays connected across page refreshes within the same browser session.

---

## Admin dashboard

Go to `http://localhost:3000/admin` to view the cognitive monitoring dashboard — per-user accuracy trends and MCI risk flagging.

---

## Project structure

```
moveJoy_v2/
├── game/
│   ├── index.html          # main game (all screens)
│   ├── server.js           # Express REST API server
│   ├── db.js               # SQLite database logic
│   ├── admin.html          # clinician dashboard
│   ├── assets/             # images and icons
│   ├── game_data.db        # player data (auto-created)
│   └── package.json
├── controller/
│   └── src/main.cpp        # ESP32 BLE firmware (PlatformIO)
├── gesture_server.py       # YOLO + Keras gesture WebSocket server
├── gesture_model.keras     # trained gesture classifier
├── gesture_labels.json     # gesture class labels
├── yolov8n-pose.pt         # YOLO pose model
├── collect_data.py         # tool: collect gesture training data
├── train_model.py          # tool: retrain gesture classifier
├── test_gesture.py         # tool: test gesture model live
└── requirements.txt        # Python dependencies
```
