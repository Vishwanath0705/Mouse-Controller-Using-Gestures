import cv2
import math
import numpy as np
import time
import HandDetector as htm
import pyautogui, autopy
import subprocess

# Camera settings
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

# Create hand detector object
detector = htm.handDetector(detectionCon=0.85, trackCon=0.8)

# Volume settings
hmin = 50
hmax = 200
volBar = 400
volPer = 0
vol = 0
color = (0, 215, 255)

# Finger tip IDs for gestures
tipIds = [4, 8, 12, 16, 20]
mode = ''
active = 0

# Disable PyAutoGUI's fail-safe feature
pyautogui.FAILSAFE = False


# Function to set volume on Linux
def set_volume_linux(percent):
    percent = max(0, min(100, int(percent)))
    subprocess.call(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{percent}%'])


# Function to display text on the image
def putText(mode, loc=(250, 450), color=(0, 255, 255)):
    cv2.putText(img, str(mode), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL, 3, color, 3)


# Main loop
while True:
    success, img = cap.read()
    if not success:
        print("Failed to read")
        break

    # Find hands and landmarks
    img = detector.findHands(img)
    lmlist = detector.findPosition(img, draw=False)

    # Check if hand landmarks are detected (lmlist should not be empty)
    if len(lmlist) != 0:
        print(lmlist)  # Print landmarks for debugging

        fingers = []

        # Check if the thumb (tipIds[0]) is extended
        if lmlist[tipIds[0]][1] > lmlist[tipIds[0 - 1]][1]:  # Checking if thumb is extended
            if lmlist[tipIds[0]][1] >= lmlist[tipIds[0] - 1][1]:  # Comparing thumb position for extension
                fingers.append(1)  # Thumb extended
            else:
                fingers.append(0)  # Thumb not extended
        elif lmlist[tipIds[0]][1] < lmlist[tipIds[0 - 1]][1]:  # Check thumb is in resting position
            if lmlist[tipIds[0]][1] <= lmlist[tipIds[0] - 1][1]:
                fingers.append(1)  # Thumb extended
            else:
                fingers.append(0)  #

        # Check other fingers (index 1 to 4)
        for id in range(1, 5):
            if lmlist[tipIds[id]][2] < lmlist[tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        # Mode logic based on finger positions
        if (fingers == [0, 0, 0, 0, 0]) & (active == 0):
            mode = 'N'
        elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) & (active == 0):
            mode = 'Scroll'
            active = 1
        elif (fingers == [1, 1, 0, 0, 0]) & (active == 0):
            mode = 'Volume'
            active = 1
        elif (fingers == [1, 1, 1, 1, 1]) & (active == 0):
            mode = 'Cursor'
            active = 1

    ######### SCROLL #########
    if mode == "Scroll":
        active = 1
        putText(mode)
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        if len(lmlist) != 0:
            if fingers == [0, 1, 0, 0, 0]:
                putText(mode="U", loc=(200, 455), color=(0, 255, 0))
                pyautogui.scroll(300)
            if fingers == [0, 1, 1, 0, 0]:
                putText(mode='D', loc=(200, 455), color=(0, 0, 255))
                pyautogui.scroll(-300)
            elif fingers == [0, 0, 0, 0, 0]:
                active = 0
                mode = 'N'

    ########## VOLUME #########
    if mode == "Volume":
        putText(mode)
        if len(lmlist) != 0:
            if fingers[-1] == 1:
                active = 0
                mode = "N"
            else:
                x1, y1 = lmlist[4][1], lmlist[4][2]
                x2, y2 = lmlist[8][1], lmlist[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                cv2.circle(img, (x1, y1), 10, color, cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, color, cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), color, 3)
                cv2.circle(img, (cx, cy), 10, color, cv2.FILLED)

                length = math.hypot(x2 - x1, y2 - y1)

                volPer = np.interp(length, [hmin, hmax], [0, 100])
                set_volume_linux(volPer)

                volBar = np.interp(volPer, [0, 100], [400, 150])
                cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
                cv2.rectangle(img, (30, int(volBar)), (55, 400), (215, 255, 127), cv2.FILLED)
                cv2.putText(img, f'{int(volPer)}%', (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)

    ####### CURSOR #########
    if mode == "Cursor":
        active = 1
        putText(mode)
        cv2.rectangle(img, (110, 20), (620, 350), (255, 255, 255), 3)

        if fingers[1:] == [0, 0, 0, 0]:
            active = 0
            mode = "N"
        else:
            if len(lmlist) != 0:
                x1, y1 = lmlist[8][1], lmlist[8][2]
                x2, y2 = lmlist[4][1], lmlist[4][2]

                # Calculate distance between thumb and index finger
                length = math.hypot(x2 - x1, y2 - y1)

                # Check if distance is less than threshold for click
                if length < 25:
                    pyautogui.click()

                # Map the cursor movement to the screen
                w, h = autopy.screen.size()
                X = int(np.interp(x1, [110, 620], [0, w - 1]))
                Y = int(np.interp(y1, [20, 350], [0, h - 1]))
                cv2.circle(img, (lmlist[8][1], lmlist[8][2]), 7, (255, 255, 255), cv2.FILLED)
                cv2.circle(img, (lmlist[4][1], lmlist[4][2]), 10, (0, 255, 0), cv2.FILLED)

                # Refine the coordinates to ensure smooth mouse movement
                if X % 2 != 0:
                    X = X - X % 2
                if Y % 2 != 0:
                    Y = Y - Y % 2

                autopy.mouse.move(X, Y)

    cTime = time.time()
    fps = 1 / ((cTime + 0.01) - pTime)
    pTime = cTime

    cv2.putText(img, f'FPS:{int(fps)}', (480, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
    cv2.imshow('Hand LiveFeed', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break