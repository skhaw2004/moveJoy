# MoveJoy

## 1. Title

**MoveJoy**  
Gamified Motion-Based Cognitive Monitoring System

---

## 2. Team Name and Members

### Team Name
Suancai Yu + 2 Jiaozi

### Members
- Jadyn Choo Jia En (A0321244U)
- Jereen Cheng (A0321991B)
- Lee Yan Ying (A0320584H)
- Khaw Zi Xiang Stuart (A0322454L)

---

## 3. App Description

### Project Goals

MoveJoy is a gamified cognitive monitoring system designed for elderly users who may be at risk of Mild Cognitive Impairment (MCI).

The system displays a sequence of actions on a projected screen, which users must memorise and replicate using motion-tracked handheld controllers or wristbands.

The application analyses the user’s response accuracy, sequencing, and timing performance over repeated sessions to identify possible cognitive decline trends.

---

### Hardware

- Raspberry Pi (main processing unit)
- Seeed Studio XIAO ESP32S3 (controller microcontroller)
- LSM6DS3 IMU sensor (motion tracking)
- Projector (game display output)
- Speaker (audio feedback)
- Vibration motor / haptic feedback module
- USB power supply / wall power adapter

---

### Software Setup

#### Raspberry Pi Side
- Python
- Pygame (game display and UI)
- SQLite (local database storage)

#### Controller Side
- PlatformIO
- Arduino framework
- C++ firmware for ESP32S3

#### Development Tools
- Visual Studio Code
- GitHub for version control

---

### Usage

1. The user starts the MoveJoy game system.
2. A sequence of actions is displayed on the projected screen.
3. The user memorises the displayed actions.
4. The user performs the actions using the motion-tracked controller or wristband.
5. Motion data from the IMU sensor is sent to the Raspberry Pi for processing.
6. The system checks whether the actions were performed correctly and in the correct order.
7. Scores and performance metrics are stored locally for long-term trend analysis.
8. Caregivers or healthcare professionals may review the collected performance trends to identify potential signs of cognitive decline.

---

## Current Development Status

### Completed
- Initial repository setup
- PlatformIO ESP32 project setup
- Python game prototype
- Pygame display system
- Mock controller interface
- Basic action checking logic

### In Progress
- IMU gesture detection
- ESP32 to Raspberry Pi communication
- SQLite database integration
- Scoring and analytics system

---

## Repository Structure

```text
moveJoy/
│
├── esp32_controller/
│
├── raspberry_pi/
│   ├── main.py
│   ├── display.py
│   ├── controller_interface.py
│   ├── game.py
│   ├── scoring.py
│   └── database.py
│
├── docs/
│
└── README.md
```
