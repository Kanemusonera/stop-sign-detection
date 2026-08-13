"""
test_static.py

Runs the trained model against a saved still image instead of the live camera.
Useful for checking the model and the class mapping without the camera, the
Arduino, or the serial link in the way.

STATUS: verified. Recorded output from the report-era model:
    Raw predictions: [[0.49762672 0.50237334]]
    Predicted label: 1 (50.24% confidence)

That result is worth keeping in mind: a near coin-flip on a real frame, from a
model reporting high validation accuracy. It was one of the first concrete
signs that the model had learned the training distribution rather than the
task. See PROVENANCE.md.

NOTE ON MODEL FORMAT
  The deployed (post-rebuild) model is a BINARY sigmoid classifier: predict()
  returns a single value in [0,1]. The earlier model was 2-class softmax and
  returned a pair. This script handles both, since both appear in the project
  history.
"""

import os
import pickle
import sys

import cv2
import numpy as np
import tensorflow as tf

MODEL_PATH   = "/home/km499/ObjectDetection/stop_sign/stop_sign_model.h5"            # CHANGE ME
MAPPING_PATH = "/home/km499/ObjectDetection/stop_sign/stop_sign_label_mapping.pkl"   # CHANGE ME
IMAGE_PATH   = sys.argv[1] if len(sys.argv) > 1 else "test_frame.png"

INPUT_SIZE = (64, 64)
THRESHOLD  = 0.88

for p in (MODEL_PATH, MAPPING_PATH, IMAGE_PATH):
    if not os.path.exists(p):
        print(f"Error: file not found at {p}")
        sys.exit(1)

model = tf.keras.models.load_model(MODEL_PATH)

with open(MAPPING_PATH, "rb") as f:
    class_indices = pickle.load(f)
label_map = {v: k for k, v in class_indices.items()}
print("Label mapping:", label_map)

image = cv2.imread(IMAGE_PATH)
resized = cv2.resize(image, INPUT_SIZE)
normalized = resized.astype("float32") / 255.0
batch = np.expand_dims(normalized, axis=0)

preds = model.predict(batch, verbose=0)
print("Raw predictions:", preds)

if preds.shape[-1] == 1:
    # Binary sigmoid (deployed model)
    conf = float(preds[0][0])
    idx = 1 if conf >= THRESHOLD else 0
    reported = conf if idx == 1 else 1.0 - conf
else:
    # 2-class softmax (earlier model)
    idx = int(np.argmax(preds[0]))
    reported = float(preds[0][idx])

print(f"Predicted label: {label_map[idx]} ({reported*100:.2f}% confidence)")
