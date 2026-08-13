# Provenance

What evidence exists for every claim in this repository, and where it came from.

## Why this file exists

This project has two states, three weeks apart, and they disagree.

| | Report | This repository |
|---|---|---|
| Date | 7 April 2025 | 28–29 April 2025 |
| Model | 2-class softmax | binary sigmoid |
| Class 0 means | stop sign | **non**-stop sign |
| Serial format | `"0: 67.40%"` | `"stop_sign: 92.4%"` |
| Loop closed on real signs | **No** | Yes |

The report was submitted before the system worked. Development continued and it was completed
for the presentation. Anyone reading both documents will notice the discrepancy, so it is
stated here rather than left to be discovered.

## Sources, in order of authority

1. **Development logs, 28–29 April 2025** — timestamped, contain the executed scripts, the raw
   training output, and the author's own confirmations at the moment of testing. Primary
   source for everything in this repository.
2. **Final report, 7 April 2025** — authoritative for the *earlier* system only.
3. **Presentation slides, ~30 April 2025** — describe the final system correctly in structure,
   but contain two figures that are not supported by any measurement. See Corrections.

**Legend:** ✅ verified · ⚠️ partial evidence · ❌ unverified · 🚫 superseded

---

## Core files

| File | Status | Evidence |
|------|--------|----------|
| `train_cnn.py` | ✅ | Recovered verbatim from the log, 28 Apr 22:00. Two full runs recorded with complete per-epoch output. Run 1: validation peaked 95.31%, test **90.62%**. Run 2: validation peaked 97.52%, test **90.62%**. |
| `StopSignController.ino` | ✅ | Recovered verbatim, 29 Apr 01:04. Confirmed working the same night; the author's closing message that evening confirms the complete system. Every feature in it traces to a specific observed failure documented in the log. |
| `camera/camera_test.py` | ✅ | Minimal Picamera2 script; live feed confirmed. This was the resolution after `cv2.VideoCapture(0)`, V4L2 and GStreamer all failed on the Pi 5. |
| `camera/capture_still.py` | ⚠️ | No direct confirmation; its output was consumed successfully downstream. |
| `arduino/motor_direction_test/` | ✅ | Confirmed after the common-ground fix and reversing one motor's leads. |
| `arduino/motor_pwm_test/` | ✅ | Confirmed on the 7/6/5/4 + 9/10 mapping. |
| `mount/` | ✅ | Report Section 4.4, Figures 27–28 and A8–A9.1. Printed and used. |

### Key confirmations, quoted from the log

- **28 Apr 23:14** — after the first live test with the new model: the author reports a stop
  sign image classified correctly at 99.8%.
- **28 Apr 23:31** — the threshold calibration problem, in the author's own words: a green stop
  sign, red GO sign, 30mph sign and a TV remote all scoring high, while the empty room sat
  around 30%.
- **29 Apr 00:45** — the resolution: threshold lowered to 86% after establishing that a real
  stop sign reaches ~90% at ~30cm while the distractors stay below 86%.
- **29 Apr 01:11** — the author confirms the complete system working.
- **29 Apr 01:12** — the author states plainly that the final report was submitted when the
  project was not yet working. This is the basis for the two-state framing above.

---

## Not recovered

| Missing | Why, and where it might be |
|---|---|
| `detect_live.py` (final `StopSign.py`) | **Reconstructed, not recovered.** Delivered as a canvas document; ChatGPT exports contain only chat messages, so the original source is not retrievable. `inference/detect_live.py` is rebuilt from four sources: the verbatim pre-rebuild version (`experiments/detect_live_v1_no_serial.py`), the verbatim serial patch from the log (28 Apr 23:19), the verbatim `predict_image()` body from the same message, and the original's actual terminal output (28 Apr 23:22), against which its print statements are line-for-line verified. Behavioural equivalence is claimed; byte-for-byte identity is not. The Pi's filesystem is the only place the original may survive, and supersedes the reconstruction if found. |
| `plot_training_history.py` | Produced the training figures in the report. The figures survive; the script does not. |
| `requirements.txt` | Never existed. The committed file is **reconstructed from imports** and unpinned, and says so in its header. Replace it with `pip freeze` output from the Pi virtualenv if that is still available — the system-site-packages arrangement for `picamera2` and `python3-kms++` cannot be captured by a hand-written list. |

---

## Superseded

| Approach | Why |
|---|---|
| 2-class softmax model, class 0 = stop | 🚫 Replaced by binary sigmoid with inverted mapping. Report-era figures describe this model. |
| Report-era `StopSignController.ino` (report Fig. A5) | 🚫 Stateless; no braking ramp, latch, buffer or cooldown. Never worked on real detections. |
| 877-image dataset with phantom `unknown` class | 🚫 Most images lacked matching annotations, so the loader invented a class. Reported 92.61% while being useless. |
| `cv2.VideoCapture(0)`, V4L2, GStreamer, legacy `start_x=1` | 🚫 None work with Camera Module 3 on Pi 5; Picamera2 is the supported path. |
| Pi direct GPIO motor control (BCM 17/18/22/23), Pimoroni Explorer pHAT | 🚫 Superseded by Arduino/L298N over serial. |
| YOLOv4 / Darknet | 🚫 Failed to compile on ARM. |

### On YOLO

The dataset uses YOLO-format annotations and the development thread is titled for it, but
**no YOLO model was ever trained to a validated state or run for inference.** A search of the
complete conversation archive (1,279 conversations) found no `detect.py` invocation, no
`best.pt`, and no mAP figure. The report states directly that YOLO training was not validated
and its `train.py` was incomplete.

The working system is CNN classification throughout. Any claim of YOLO object detection in
this project would be unsupported.

---

## Corrections

Where sources disagree, resolved against the primary evidence.

**Accuracy: 90.62%, not 94%.** The presentation slides state "~94% accuracy". That figure does
not appear in any training output. It originated in an AI-drafted slide outline written on
29 April and was carried into the deck unchanged. The measured held-out test accuracy, printed
by the training script on two separate runs, is 90.62%.

**Frame rate: not measured.** The slides state "~15 FPS". Same origin — an AI-drafted slide
bullet, never measured. No frame-rate figure exists anywhere in the logs for this model. The
report's 8–12 FPS refers to a YOLO configuration that was never validated, and its 2–5 FPS
refers to the superseded model.

**"No false stops on other objects"** (slide 9) is true of the *system* at its operating
threshold, but not of the *model*. Confusing negatives scored high; the threshold excluded
them. The distinction matters and the README states it.

**Pin mapping.** A development log recorded the controller using IN1=2, IN2=3, IN3=4, IN4=5 —
a mapping separately recorded as leaving one wheel dead. Both the report listing and the final
recovered sketch use 7/6/5/4. The log was wrong.

---

## Method note

Everything above was reconstructed from a complete conversation archive, a submitted report and
a presentation deck, cross-checked against each other. Where the three disagreed, precedence
went to contemporaneous machine output (training logs, terminal transcripts) over prose
written afterwards.

Two general lessons, both earned here:

- A model recalling its own conversation reconstructs plausibly rather than accurately. Several
  details asserted in later summaries turned out to be wrong when checked against the original
  transcript.
- AI-drafted figures propagate. Two numbers invented for a slide outline travelled into a
  presentation and then onto a CV without ever having been measured. Anything quantitative
  should be traceable to output, not to prose.
