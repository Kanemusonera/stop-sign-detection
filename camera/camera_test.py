"""
camera_test.py

Minimal Picamera2 live-feed test. Run this first when setting up on a new Pi —
if this doesn't show a window, nothing further will work.

WHY THIS FILE EXISTS
  cv2.VideoCapture(0) does not work with Camera Module 3 on a Raspberry Pi 5.
  It returns "Failed to grab frame" with no useful diagnostic. V4L2 and
  GStreamer/libcamerasrc pipelines were also tried and failed. Picamera2 is the
  supported path on Pi 5 and is what the whole project is built on.

  Legacy fixes found online (start_x=1, gpu_mem in config.txt) are for the old
  camera stack and are inert on Pi 5, which uses libcamera with dynamic CMA
  allocation.

ENVIRONMENT
  The virtualenv must be created with --system-site-packages, or picamera2 and
  python3-kms++ from /usr/lib/python3/dist-packages will not be importable:
      python3 -m venv --system-site-packages yoloenv

STATUS: verified. Produced a live feed after the alternatives above failed.
"""

import cv2
from picamera2 import Picamera2

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("Camera started. Press 'q' to quit.")

while True:
    frame = picam2.capture_array()

    # Camera Module 3 returns 4-channel XBGR under this configuration.
    # Converting from RGB rather than RGBA gives visibly wrong colours.
    if frame.shape[-1] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    cv2.imshow("Camera Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
picam2.stop()
