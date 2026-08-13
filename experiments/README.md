# Experiments

Approaches that were tried and superseded. None of these are part of the
deployed system. They are kept because the reasons they were abandoned are
part of the engineering record.

| File | What it was | Why it isn't in the final system |
|---|---|---|
| `shape_detection.py` | Classical OpenCV contour detection | Detects shapes, not signs. Cannot distinguish a stop sign from any other octagon, and degrades with lighting, occlusion and viewing angle. Faster than the CNN at 10-15 FPS, and the honest baseline it had to beat. |
| `mobilenet_classifier.py` | MobileNetV2 transfer learning, 224×224 | Too heavy for real-time inference on a Pi 5. Never executed. The deployed model is a small custom CNN at 64×64, trading capacity for throughput. |
| `detect_live_v1_no_serial.py` | The live detection script before the 28 April rebuild | Loads a label *encoder* rather than a label *mapping*, threshold 0.5 rather than 0.88, and no serial output at all — it cannot drive the Arduino. Direct ancestor of `inference/detect_live.py`; the diff between them is the whole story of the rebuild. |

## Not included: the phantom class incident

An earlier training run used an 877-image dataset in which most images had no
matching annotation file. The loader silently assigned all of them to an
invented `unknown` class. The run completed normally and reported 92.61%
validation accuracy while being completely useless.

The script is not preserved, but the failure is the single most useful thing
that happened in this project. A high validation number on broken data is worse
than a low one on clean data, because it tells you to stop looking.
