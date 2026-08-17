#!/usr/bin/env python3
"""
StopSign.py (repo name: detect_live.py)

RECOVERED VERBATIM from the Raspberry Pi's SD card (rootfs, ext4), read
directly via DiskGenius after the card was pulled from the Pi. This is the
actual final script — not a reconstruction. It supersedes any earlier
reconstructed version.

Path on the Pi: /home/km499/yolo_tf_project/StopSign_Dataset/StopSign.py

Supports three modes from one script: a single image, batch processing a
directory of images, or a live camera loop that also drives the Arduino
over serial. Confirms the batch/CLI mode inferred-but-unverified in an
earlier reconstruction attempt was real.
"""

import os
import sys
import argparse
import time
import cv2
import numpy as np
import pickle
import tensorflow as tf
import serial
from picamera2 import Picamera2

# ── 1. Configuration ─────────────────────────────────────────────────────
MODEL_PATH    = "/home/km499/yolo_tf_project/StopSign_Dataset/stop_sign_model.keras"
MAPPING_PATH  = "/home/km499/yolo_tf_project/StopSign_Dataset/stop_sign_label_mapping.pkl"
SERIAL_PORT   = "/dev/ttyUSB0"   # adjust if different (e.g. "/dev/serial0")
BAUD_RATE     = 9600

# ── 2. Validate files ────────────────────────────────────────────────────
for path in (MODEL_PATH, MAPPING_PATH):
    if not os.path.exists(path):
        print(f"Error: file not found at {path}")
        sys.exit(1)

# ── 3. Load ML model & mapping ───────────────────────────────────────────
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded.")

with open(MAPPING_PATH, 'rb') as f:
    class_indices = pickle.load(f)
# invert mapping: index -> label
label_map = {v: k for k, v in class_indices.items()}
print("Label mapping:", label_map)

# ── 4. Initialize serial to Arduino ──────────────────────────────────────
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # allow Arduino to reset
    print(f"Serial opened on {SERIAL_PORT} at {BAUD_RATE}bps")
except Exception as e:
    print(f"Warning: could not open serial port {SERIAL_PORT}: {e}")
    ser = None

# ── 5. Parameters ─────────────────────────────────────────────────────────
INPUT_SIZE = (64, 64)
THRESHOLD  = 0.88  # sigmoid confidence threshold for positive

# ── 6. Preprocessing & prediction ────────────────────────────────────────
def preprocess(image):
    # image: BGR array
    img = cv2.resize(image, INPUT_SIZE)
    img = img.astype('float32') / 255.0
    return np.expand_dims(img, axis=0)


def predict_image(image, display=False, output_path=None):
    batch = preprocess(image)
    preds = model.predict(batch, verbose=0)
    conf = float(preds[0][0])
    idx = 1 if conf >= THRESHOLD else 0
    label = label_map[idx]
    text = f"{label}: {conf*100:.1f}%"
    print(text)

    # send to Arduino if available
    if ser:
        ser.write((text + '\n').encode('utf-8'))

    # annotate
    out = image.copy()
    cv2.putText(out, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2, cv2.LINE_AA)

    if display:
        cv2.imshow('Result', out)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if output_path:
        cv2.imwrite(output_path, out)

    return label, conf

# ── 7. Batch directory processing ────────────────────────────────────────
def process_directory(dir_path, display=False):
    exts = ('.jpg', '.jpeg', '.png')
    for fname in sorted(os.listdir(dir_path)):
        if not fname.lower().endswith(exts):
            continue
        full = os.path.join(dir_path, fname)
        img = cv2.imread(full)
        if img is None:
            print(f"Failed to load {full}")
            continue
        print(f"Processing {fname}")
        out_file = os.path.join(dir_path, f"result_{fname}")
        predict_image(img, display=display, output_path=out_file)

# ── 8. Live camera loop ──────────────────────────────────────────────────
def run_camera():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    time.sleep(1)
    print("Camera started. Press 'q' to quit.")
    while True:
        frame = picam2.capture_array()
        if frame is None:
            break
        # handle RGBA if any
        if frame.shape[-1] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        # get prediction and confidence
        label, conf = predict_image(frame)
        # overlay on live frame
        text = f"{label}: {conf*100:.1f}%"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow('Live Stop Sign', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    picam2.stop()

# ── 9. Main CLI ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stop Sign Classifier')
    parser.add_argument('-i', '--input', help='Image file or directory for batch mode')
    parser.add_argument('-d', '--display', action='store_true', help='Show annotated images')
    args = parser.parse_args()

    if args.input:
        if os.path.isdir(args.input):
            process_directory(args.input, display=args.display)
        elif os.path.isfile(args.input):
            img = cv2.imread(args.input)
            if img is None:
                print(f"Could not read {args.input}")
                sys.exit(1)
            predict_image(img, display=args.display)
        else:
            print(f"Invalid path: {args.input}")
    else:
        run_camera()
