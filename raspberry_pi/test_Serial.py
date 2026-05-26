import serial

ser = serial.Serial("/dev/tty.usbmodem3101", 115200)

while True:
    line = ser.readline().decode(errors="ignore").strip()

    if line:
        print(line)