# moveJoy
1. Title

MoveJoy

2. Team Name and Members

Team Name: Suancai Yu + 2 Jiaozi

Members:

Jadyn Choo Jia En (A0321244U)
Jereen Cheng (A0321991B)
Lee Yan Ying (A0320584H)
Khaw Zi Xiang Stuart (A0322454L)

3. App Description
Project Goals

MoveJoy is a gamified cognitive monitoring system designed for elderly users who may be at risk of Mild Cognitive Impairment (MCI). The system displays a sequence of actions on a projected screen, which users must memorise and replicate using motion-tracked handheld controllers. The application analyses the user’s response accuracy, sequencing, and timing performance over repeated sessions to identify possible cognitive decline trends.

Hardware
Raspberry Pi (main processing unit)
Seeed Studio XIAO ESP32S3 (controller microcontroller)
LSM6DS3 IMU sensor (motion tracking)
Projector (game display output)
Speaker (audio feedback)
Vibration motor / haptic feedback module
USB power supply / wall power adapter

Software Setup
Raspberry Pi Side
Python
Pygame (game display and UI)
SQLite (local database storage)

Controller Side
PlatformIO
Arduino framework
C++ firmware for ESP32S3

Development Tools
Visual Studio Code
GitHub for version control

Usage
The user starts the MoveJoy game system.
A sequence of actions is displayed on the projected screen.
The user memorises the displayed actions.
The user performs the actions using the motion-tracked controller or wristband.
Motion data from the IMU sensor is sent to the Raspberry Pi for processing.
The system checks whether the actions were performed correctly and in the correct order.
Scores and performance metrics are stored locally for long-term trend analysis.
Caregivers or healthcare professionals may review the collected performance trends to identify potential signs of cognitive decline.
