"""
NewTrain_Cnn.py (repo name: train_cnn.py)

RECOVERED VERBATIM from the Raspberry Pi's SD card (rootfs, ext4), read
directly via DiskGenius after the card was pulled from the Pi. This is the
actual final training script — not a reconstruction — and it is the one
that produced the model loaded by the real inference/detect_live.py.

Path on the Pi: /home/km499/ObjectDetection/stop_sign/NewTrain_Cnn.py

Saves stop_sign_model.keras and stop_sign_label_mapping.pkl, matching
exactly what detect_live.py expects. This confirms the two files are
consistent with each other, which an earlier reconstructed train_cnn.py
(which saved .h5) was not.
"""

import os
import pickle
import tensorflow as tf
from tensorflow.keras import Input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# ── 1. Paths ───────────────────────────────────────────────────────────────
BASE_DIR  = "/home/km499/ObjectDetection/stop_sign"
TRAIN_DIR = os.path.join(BASE_DIR, "train")
VALID_DIR = os.path.join(BASE_DIR, "valid")
TEST_DIR  = os.path.join(BASE_DIR, "test")

# ── 2. Parameters ─────────────────────────────────────────────────────────
TARGET_SIZE = (64, 64)
BATCH_SIZE  = 32
EPOCHS      = 50

# ── 3. Data generators ────────────────────────────────────────────────────
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

# Binary classes: non_stop_sign = 0, stop_sign = 1
classes = ["non_stop_sign", "stop_sign"]

train_gen = train_aug.flow_from_directory(
    TRAIN_DIR,
    target_size=TARGET_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
    classes=classes
)

valid_gen = val_test_aug.flow_from_directory(
    VALID_DIR,
    target_size=TARGET_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
    classes=classes
)

test_gen = val_test_aug.flow_from_directory(
    TEST_DIR,
    target_size=TARGET_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
    shuffle=False,
    classes=classes
)

# ── 4. Persist label mapping ──────────────────────────────────────────────
with open("stop_sign_label_mapping.pkl", "wb") as f:
    pickle.dump(train_gen.class_indices, f)
print("Class indices:", train_gen.class_indices)

# ── 5. Build CNN model ────────────────────────────────────────────────────
model = Sequential([
    Input(shape=(*TARGET_SIZE, 3)),
    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),

    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),

    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),

    Dense(1, activation='sigmoid')
])
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)
model.summary()

# ── 6. Callbacks ───────────────────────────────────────────────────────────
checkpoint = ModelCheckpoint(
    "stop_sign_model.keras",
    monitor='val_loss',
    save_best_only=True,
    verbose=1
)
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,
    verbose=1
)

# ── 7. Train ───────────────────────────────────────────────────────────────
history = model.fit(
    train_gen,
    validation_data=valid_gen,
    epochs=EPOCHS,
    callbacks=[checkpoint, early_stop]
)

# ── 8. Evaluate on test set ────────────────────────────────────────────────
test_loss, test_acc = model.evaluate(
    test_gen
)
print(f"Test accuracy: {test_acc * 100:.2f}%")
