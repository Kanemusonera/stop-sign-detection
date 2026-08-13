"""
mobilenet_classifier.py  (originally stop_sign_classifier.py)

MobileNetV2 transfer-learning approach to stop-sign classification.
SUPERSEDED — never executed on hardware. Kept for context.

Why it was abandoned: 224x224 input with a MobileNetV2 backbone was too heavy
for real-time inference on the Pi 5. The deployed system used a small custom
CNN at 64x64 instead (see ../train_cnn.py), trading capacity for throughput.

Note this is a MULTI-CLASS softmax classifier saving stop_sign_model.keras and
stop_sign_classes.txt. The deployed model is a BINARY sigmoid classifier saving
stop_sign_model.h5 and stop_sign_label_mapping.pkl. Different artefacts, not
interchangeable.

STATUS: written, never run. No training output exists for this script.
"""

import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import argparse
import os


# Train a model using transfer learning
def train_model(dataset_path, epochs=10, batch_size=16):
    img_size = (224, 224)

    train_ds = tf.keras.preprocessing.image_dataset_from_directory(
        dataset_path, validation_split=0.2, subset="training", seed=123,
        image_size=img_size, batch_size=batch_size
    )

    val_ds = tf.keras.preprocessing.image_dataset_from_directory(
        dataset_path, validation_split=0.2, subset="validation", seed=123,
        image_size=img_size, batch_size=batch_size)

    class_names = train_ds.class_names

    # Save class names
    with open("stop_sign_classes.txt", "w") as f:
        for name in class_names:
            f.write(name + "\n")

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=img_size + (3,), include_top=False, weights="imagenet")
    base_model.trainable = False

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(len(class_names), activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    model.fit(train_ds, validation_data=val_ds, epochs=epochs)

    model.save("stop_sign_model.keras")
    print("Model training complete. Saved as stop_sign_model.keras")


# Prediction function with confidence threshold
def predict_image(model_path, image_path, threshold=0.6):
    from tensorflow.keras.preprocessing import image

    model = tf.keras.models.load_model(model_path)

    with open("stop_sign_classes.txt", "r") as f:
        class_names = [line.strip() for line in f]

    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(
        np.expand_dims(img_array, 0))

    predictions = model.predict(img_array)
    confidence = np.max(predictions)
    predicted_class = class_names[np.argmax(predictions)]

    if confidence < threshold:
        print(f"Image not confidently identified (confidence: {confidence:.2f}). "
              f"Likely a new stop sign type.")
    else:
        print(f"Predicted class: {predicted_class}, Confidence: {confidence*100:.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Stop Sign Identifier")
    parser.add_argument('--mode', choices=['train', 'predict'], required=True)
    parser.add_argument('--dataset', type=str, default='StopSignDataset')
    parser.add_argument('--image', type=str, help='Path to image for prediction')
    parser.add_argument('--epochs', type=int, default=10)
    args = parser.parse_args()

    if args.mode == 'train':
        train_model(args.dataset, epochs=args.epochs)
    elif args.mode == 'predict':
        if not args.image:
            print("Please specify an image path using --image")
        else:
            predict_image('stop_sign_model.keras', args.image)


if __name__ == "__main__":
    main()
