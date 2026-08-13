"""
train_cnn.py

Trains the binary stop-sign classifier demonstrated at the EG3005 presentation
(29 April 2025). Supersedes the two-class softmax model described in the final
report, which was trained on a different, more biased dataset.

SOURCE: Recovered verbatim from the development log, 28 April 2025 22:00.
Two runs of this script are recorded, both reaching 90.62% test accuracy
(validation peaked at 95.31% and 97.52% respectively).

HARDWARE / PATH DEPENDENCIES
  BASE points at an absolute path on the original Pi. Change it before running.
  Expected layout, with negatives collected via Roboflow:
      stop_sign/
        train/   non_stop_sign/  stop_sign/
        valid/   non_stop_sign/  stop_sign/
        test/    non_stop_sign/  stop_sign/

CLASS MAPPING
  Explicitly pinned to ["non_stop_sign", "stop_sign"], giving
  {'non_stop_sign': 0, 'stop_sign': 1}. This is INVERTED relative to the
  report-era model, where class 0 meant stop. The mapping is pickled so the
  inference script cannot silently disagree with the model — the earlier
  version of this project had exactly that bug.
"""

import os
import pickle
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# ── 1. Paths ────────────────────────────────────────────────────────────────
BASE = "/home/km499/ObjectDetection/stop_sign"   # CHANGE ME
TRAIN_DIR = os.path.join(BASE, "train")
VALID_DIR = os.path.join(BASE, "valid")
TEST_DIR  = os.path.join(BASE, "test")

# ── 2. Data generators ──────────────────────────────────────────────────────
# Augmentation matters more than usual here: the report-era model learned to
# detect the colour red rather than sign shape, partly because the training
# images were shot in one indoor environment. Brightness and geometric jitter
# plus hard negatives are the mitigation.
train_aug = ImageDataGenerator(
    rescale=1./255,
    rotation_range=15,
    width_shift_range=0.1,
    height_shift_range=0.1,
    brightness_range=(0.6, 1.4),
    shear_range=0.1,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode="reflect"
)
val_test_aug = ImageDataGenerator(rescale=1./255)

BATCH_SIZE = 32
TARGET_SIZE = (64, 64)

train_gen = train_aug.flow_from_directory(
    TRAIN_DIR, target_size=TARGET_SIZE, batch_size=BATCH_SIZE,
    class_mode="binary", classes=["non_stop_sign", "stop_sign"]
)
valid_gen = val_test_aug.flow_from_directory(
    VALID_DIR, target_size=TARGET_SIZE, batch_size=BATCH_SIZE,
    class_mode="binary", classes=["non_stop_sign", "stop_sign"]
)
test_gen = val_test_aug.flow_from_directory(
    TEST_DIR, target_size=TARGET_SIZE, batch_size=BATCH_SIZE,
    class_mode="binary", shuffle=False, classes=["non_stop_sign", "stop_sign"]
)

# Save the mapping so the inference script knows which index is "stop_sign"
with open("stop_sign_label_mapping.pkl", "wb") as f:
    pickle.dump(train_gen.class_indices, f)
print("Class indices:", train_gen.class_indices)   # {'non_stop_sign': 0, 'stop_sign': 1}

# ── 3. CNN ──────────────────────────────────────────────────────────────────
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(*TARGET_SIZE, 3)),
    MaxPooling2D(),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

# ── 4. Callbacks ────────────────────────────────────────────────────────────
callbacks = [
    ModelCheckpoint("stop_sign_model.h5", save_best_only=True, monitor="val_loss", verbose=1),
    EarlyStopping(monitor="val_loss", patience=5, verbose=1)
]

# ── 5. Train ────────────────────────────────────────────────────────────────
history = model.fit(
    train_gen,
    steps_per_epoch=train_gen.samples // BATCH_SIZE,
    validation_data=valid_gen,
    validation_steps=valid_gen.samples // BATCH_SIZE,
    epochs=50,
    callbacks=callbacks
)

test_loss, test_acc = model.evaluate(test_gen, steps=test_gen.samples // BATCH_SIZE)
print(f"Test accuracy: {test_acc*100:.2f}%")
