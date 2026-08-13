"""
detect_live_v1_no_serial.py  (originally StopSign.py, pre-rebuild version)

RECOVERED VERBATIM. This is the live-detection script as it stood BEFORE the
28 April 2025 rebuild. Kept because it is the direct ancestor of the deployed
script and shows what changed.

SUPERSEDED — differs from the final version in three ways that matter:
  1. Loads stop_sign_label_encoder.pkl (sklearn LabelEncoder) rather than
     stop_sign_label_mapping.pkl (dict from flow_from_directory.class_indices)
  2. THRESHOLD = 0.5 rather than 0.88
  3. No serial output at all — it cannot drive the Arduino

It also uses the single-class convention (pos_label / "no_" + pos_label)
from the earlier dataset, rather than the explicit non_stop_sign / stop_sign
pair used after the rebuild.

STATUS: ran and displayed a live overlay. Never drove the vehicle.
"""

import os
import time
import cv2
import numpy as np
import pickle
import tensorflow as tf
from picamera2 import Picamera2

# ── 1. Paths ───────────────────────────────────────────────────────────────
MODEL_PATH   = "/home/km499/yolo_tf_project/StopSign_Dataset/stop_sign_model.h5"
ENCODER_PATH = "/home/km499/yolo_tf_project/StopSign_Dataset/stop_sign_label_encoder.pkl"

for p in (MODEL_PATH, ENCODER_PATH):
    if not os.path.exists(p):
        print(f"Error: file not found at {p}")
        exit(1)

# ── 2. Load model & label encoder ──────────────────────────────────────────
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded.")

with open(ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)
print("Label encoder loaded. Classes:", label_encoder.classes_)

# Single-class setup
pos_label = label_encoder.classes_[0]
neg_label = f"no_{pos_label}"
THRESHOLD = 0.5  # adjust as needed
print(f"Using threshold={THRESHOLD}")

# ── 3. Camera setup ────────────────────────────────────────────────────────
print("Initializing Picamera2...")
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(1)
print("Picamera2 started.")

# ── 4. Inference loop ──────────────────────────────────────────────────────
INPUT_SIZE = (64, 64)
WINDOW_NAME = "Stop Sign Detection"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
print("Starting live detection. Press 'q' to quit.")

while True:
    frame = picam2.capture_array()
    if frame is None:
        print("Failed to capture frame")
        break

    # Handle possible RGBA
    if frame.shape[-1] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    resized_frame = cv2.resize(frame, INPUT_SIZE)
    normalized_frame = resized_frame.astype("float32") / 255.0
    input_batch = np.expand_dims(normalized_frame, axis=0)

    preds = model.predict(input_batch, verbose=0)
    conf = preds[0][0]
    label = pos_label if conf >= THRESHOLD else neg_label
    overlay_text = f"{label}: {conf*100:.2f}%"

    cv2.putText(frame, overlay_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2)
    cv2.imshow(WINDOW_NAME, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.imwrite("stop_sign_frame.png", frame)
        print("Exiting. Saved stop_sign_frame.png")
        break

# ── 5. Cleanup ─────────────────────────────────────────────────────────────
cv2.destroyAllWindows()
picam2.stop()
