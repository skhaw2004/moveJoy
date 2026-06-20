import cv2

for i in [0, 1]:
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(f'cam_test_index_{i}.jpg', frame)
            print(f'saved cam_test_index_{i}.jpg')
    cap.release()
