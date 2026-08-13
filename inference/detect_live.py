"""
detect_live.py  (deployed as StopSign.py)

Live stop-sign detection on the Raspberry Pi 5. Classifies each camera frame
and writes the result to the Arduino over USB serial, which decides whether to
brake. This is the Pi half of the system demonstrated on 29 April 2025.

═══════════════════════════════════════════════════════════════════════════════
  ⚠  RECONSTRUCTION — NOT RECOVERED VERBATIM
═══════════════════════════════════════════════════════════════════════════════
The original was delivered as a ChatGPT canvas document. Canvas contents are
not included in ChatGPT data exports (only chat messages are), so the exact
final source could not be retrieved.

This file is rebuilt from four independent sources, not from memory:
  1. The verbatim pre-rebuild version, recovered in full
     (see ../experiments/detect_live_v1_no_serial.py) — supplies the structure
  2. The verbatim serial patch from the development log, 28 Apr 23:19
  3. The verbatim predict_image() body from the same message
  4. The actual terminal output of the original running, 28 Apr 23:22 —
     used to verify the print statements below match what the real script
     emitted, line for line

Known-correct against the original's observed stdout:
    Loading model...
    Model loaded.
    Label mapping: {0: 'non_stop_sign', 1: 'stop_sign'}
    Serial opened on /dev/ttyUSB0 at 9600bps
    Camera started. Press 'q' to quit.
    non_stop_sign: 33.8%

What is NOT verified: exact function decomposition, comment text, and argument
handling (the original supported an --input batch mode that is omitted here).
Behaviour should be equivalent; byte-for-byte identity is not claimed.

If the Pi's filesystem is still accessible, the original at
~/yolo_tf_project/StopSign_Dataset/StopSign.py supersedes this file.
═══════════════════════════════════════════════════════════════════════════════

HARDWARE / PATH DEPENDENCIES
  MODEL_PATH, MAPPING_PATH   absolute paths on the original Pi — change these
  SERIAL_PORT                /dev/ttyUSB0 with the Arduino on USB
  Camera Module 3 via Picamera2; the venv needs --system-site-packages

THRESHOLD = 0.88 is not arbitrary. Confusing negatives (a green stop sign, a
red GO sign, a 30mph sign) scored high because the model keys partly on the
colour red. A real stop sign reaches ~90% at roughly 30cm from the camera while
those distractors stay below 86%, so the threshold sits inside that measured
gap. The Arduino applies a second, independent threshold of 86% to a 5-frame
rolling mean. See PROVENANCE.md.
"""

import os
import time
import pickle

import cv2
import numpy as np
import serial
import tensorflow as tf
from picamera2 import Picamera2

# ── 1. Paths ───────────────────────────────────────────────────────────────
MODEL_PATH   = "/home/km499/ObjectDetection/stop_sign/stop_sign_model.h5"      # CHANGE ME
MAPPING_PATH = "/home/km499/ObjectDetection/stop_sign/stop_sign_label_mapping.pkl"  # CHANGE ME

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE   = 9600

INPUT_SIZE  = (64, 64)
THRESHOLD   = 0.88          # see docstring — sits inside a measured margin
WINDOW_NAME = "Stop Sign Detection"

for p in (MODEL_PATH, MAPPING_PATH):
    if not os.path.exists(p):
        print(f"Error: file not found at {p}")
        exit(1)

# ── 2. Load model & label mapping ──────────────────────────────────────────
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded.")

# The mapping is loaded rather than hardcoded so the script cannot silently
# disagree with the model about which index means "stop_sign". An earlier
# iteration of this project had exactly that bug: the classes were inverted
# between training and inference and the car stopped at everything except
# stop signs.
with open(MAPPING_PATH, "rb") as f:
    class_indices = pickle.load(f)          # {'non_stop_sign': 0, 'stop_sign': 1}

label_map = {v: k for k, v in class_indices.items()}
print("Label mapping:", label_map)

# ── 3. Serial to Arduino ───────────────────────────────────────────────────
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)   # the Arduino resets when the port opens; wait for it
print(f"Serial opened on {SERIAL_PORT} at {BAUD_RATE}bps")

# ── 4. Camera ──────────────────────────────────────────────────────────────
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(1)


def preprocess(frame):
    """Resize, rescale to [0,1], add batch dimension."""
    resized = cv2.resize(frame, INPUT_SIZE)
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=0)


def predict_frame(frame):
    """Classify one frame, print it, and send it to the Arduino.

    Returns (label, confidence) so the caller can draw the same values that
    were transmitted — an earlier revision returned None for confidence and
    crashed on the overlay.
    """
    batch = preprocess(frame)
    preds = model.predict(batch, verbose=0)
    conf = float(preds[0][0])

    idx = 1 if conf >= THRESHOLD else 0
    label = label_map[idx]

    text = f"{label}: {conf*100:.1f}%"
    print(text)

    # The Arduino parses exactly this format: "<label>: <confidence>%"
    ser.write((text + "\n").encode("utf-8"))

    return label, conf


def run_camera():
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    print("Camera started. Press 'q' to quit.")

    while True:
        frame = picam2.capture_array()
        if frame is None:
            print("Failed to capture frame")
            break

        # Camera Module 3 returns 4-channel XBGR under this configuration
        if frame.shape[-1] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        label, conf = predict_frame(frame)

        overlay_text = f"{label}: {conf*100:.1f}%"
        cv2.putText(frame, overlay_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2)
        cv2.imshow(WINDOW_NAME, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            cv2.imwrite("stop_sign_frame.png", frame)
            print("Exiting. Saved stop_sign_frame.png")
            break


if __name__ == "__main__":
    try:
        run_camera()
    finally:
        cv2.destroyAllWindows()
        picam2.stop()
        ser.close()
