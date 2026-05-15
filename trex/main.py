import cv2
import numpy as np
import mss
import pyautogui
import time

BASE_ZONE = {"x": 743, "y": 300, "w": 100, "h": 42} 
RECORD_ZONE = {"top": 170, "left": 600, "width": 900, "height": 200}

THRESHOLD = 20
JUMP_COOLDOWN = 0.6
SHIFT_SPEED = 0.7
MAX_SHIFT = 150

sct = mss.mss()
test_img = np.array(sct.grab(RECORD_ZONE))
frame_h, frame_w = test_img.shape[:2]
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('dino_attempt.avi', fourcc, 20.0, (frame_w, frame_h))

print("запуск через 2 секунды..")
time.sleep(2)
pyautogui.press('space')

start_time = time.time()
last_jump = 0

try:
    while True:
        now = time.time()
        elapsed = now - start_time
        screenshot = sct.grab(RECORD_ZONE)
        full_img = np.array(screenshot)
        frame = cv2.cvtColor(full_img, cv2.COLOR_BGRA2BGR)
        current_shift = min(int(elapsed * SHIFT_SPEED), MAX_SHIFT)
        roi_x1 = (BASE_ZONE["x"] - RECORD_ZONE["left"]) + current_shift
        roi_y1 = (BASE_ZONE["y"] - RECORD_ZONE["top"])
        roi_x2 = roi_x1 + BASE_ZONE["w"]
        roi_y2 = roi_y1 + BASE_ZONE["h"]
        roi = frame[max(0, roi_y1):min(frame_h, roi_y2), 
                    max(0, roi_x1):min(frame_w, roi_x2)]
        if roi.size > 0:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            dark_pixels = int(np.sum(gray < 100))
        else:
            dark_pixels = 0
        if dark_pixels >= THRESHOLD and (now - last_jump) > JUMP_COOLDOWN:
            pyautogui.press('space')
            last_jump = now
            cv2.putText(frame, "JUMP!", (roi_x1, roi_y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        out.write(frame)
        cv2.imshow("й выход", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    out.release()
    cv2.destroyAllWindows()
    print("\nФайл сохранен как: dino_attempt.avi")
