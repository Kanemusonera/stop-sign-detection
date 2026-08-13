"""
capture_still.py

Captures a single frame and writes it to disk. Used to grab test images for
offline model evaluation without needing the full detection loop running.

Press 'q' to capture and exit. The saved file feeds inference/test_static.py.

STATUS: partial evidence. No direct confirmation of this exact script, but its
output file was consumed successfully by the static test downstream.
"""

import cv2
from picamera2 import Picamera2

OUTPUT_PATH = "test_frame.png"

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print(f"Press 'q' to capture and save to {OUTPUT_PATH}")

while True:
    frame = picam2.capture_array()

    if frame.shape[-1] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    cv2.imshow("Capture", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite(OUTPUT_PATH, frame)
        print(f"Saved {OUTPUT_PATH}")
        break

cv2.destroyAllWindows()
picam2.stop()
