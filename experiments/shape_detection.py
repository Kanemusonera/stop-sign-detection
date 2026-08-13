"""
shape_detection.py

Classical OpenCV contour-based shape detection: threshold, find contours,
approximate each to a polygon, and name it by vertex count. Runs live on the
Pi camera at 10-15 FPS.

WHY THIS IS IN experiments/
  This was the first approach to sign recognition, before any machine learning.
  It is fast and completely interpretable, but it detects *shapes*, not signs —
  it cannot tell a stop sign from any other octagon, and it degrades badly with
  lighting change, partial occlusion and viewing angle. Those limits are what
  motivated moving to a learned classifier.

  Worth keeping: it is the honest baseline the CNN has to beat, and at 10-15
  FPS it is faster than the deployed model.

STATUS: verified. Confirmed detecting rectangles, pentagons, hexagons and
circles from the live camera feed.
"""

import cv2
import numpy as np
from picamera2 import Picamera2

MIN_AREA = 500          # ignore specks and sensor noise
EPSILON_FACTOR = 0.04   # polygon approximation tolerance, fraction of perimeter


def classify_shape(approx):
    """Name a polygon by its vertex count."""
    vertices = len(approx)

    if vertices == 3:
        return "Triangle"
    if vertices == 4:
        # Distinguish square from rectangle by aspect ratio
        x, y, w, h = cv2.boundingRect(approx)
        ratio = w / float(h)
        return "Square" if 0.95 <= ratio <= 1.05 else "Rectangle"
    if vertices == 5:
        return "Pentagon"
    if vertices == 6:
        return "Hexagon"
    if vertices == 8:
        return "Octagon"
    return "Circle"


picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("Shape detection running. Press 'q' to quit.")

while True:
    frame = picam2.capture_array()

    if frame.shape[-1] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)

    # RETR_EXTERNAL discards nested contours, which otherwise produce a
    # duplicate detection for the inner and outer edge of every shape.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_AREA:
            continue

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, EPSILON_FACTOR * perimeter, True)

        shape = classify_shape(approx)

        cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)

        M = cv2.moments(approx)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.putText(frame, shape, (cx - 30, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imshow("Shape Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
picam2.stop()
