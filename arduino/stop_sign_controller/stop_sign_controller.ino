// StopSignController.ino  (originally SmoothStopWithBrakingAndBufferClear.ino)
//
// SOURCE: Recovered verbatim from the development log, 29 April 2025 01:04.
// This is the FINAL controller demonstrated at the EG3005 presentation.
// It supersedes the simpler sketch reproduced in the final report (Figure A5),
// which was written before the system worked end-to-end.
//
// Reads lines of the form "stop_sign: 92.4%" from the Raspberry Pi over USB
// serial at 9600 baud. Note the label format and class mapping differ from the
// report-era system, which sent numeric classes ("0: 67.40%") with class 0
// meaning stop. Here the model outputs class 1 = stop_sign.

// SmoothStopWithBrakingAndBufferClear.ino

const int IN1 = 7;
const int IN2 = 6;
const int IN3 = 5;
const int IN4 = 4;
const int ENA = 9;
const int ENB = 10;

const int WINDOW = 5;
float confBuffer[WINDOW] = {0};
int bufferIndex = 0;

const float STOP_THRESHOLD = 86.0;         // Average confidence needed to stop
const unsigned long STOP_DELAY = 5000;      // 5 seconds stop
const unsigned long COOLDOWN_PERIOD = 5000; // 5 seconds cooldown after stop
const unsigned long BRAKE_DURATION = 1000;  // 1 second gradual braking

bool isStopped = false;
bool isCooldown = false;
bool isBraking = false;
unsigned long stopStartTime = 0;
unsigned long cooldownStartTime = 0;
unsigned long brakeStartTime = 0;
int brakeStep = 255; // Start full speed

void setup() {
  Serial.begin(9600);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  runCar();
}

void loop() {
  unsigned long currentTime = millis();

  if (isBraking) {
    // During braking, gradually slow down
    if (currentTime - brakeStartTime <= BRAKE_DURATION) {
      int elapsed = currentTime - brakeStartTime;
      int newSpeed = map(BRAKE_DURATION - elapsed, 0, BRAKE_DURATION, 0, 255);
      newSpeed = constrain(newSpeed, 0, 255);
      analogWrite(ENA, newSpeed);
      analogWrite(ENB, newSpeed);
    } else {
      // Braking finished
      stopMotors();
      isBraking = false;
      isStopped = true;
      stopStartTime = millis();
    }
    return; // skip the rest while braking
  }

  if (isStopped) {
    if (currentTime - stopStartTime >= STOP_DELAY) {
      Serial.println("5 seconds passed, resuming driving...");
      runCar();
      isStopped = false;
      isCooldown = true;
      cooldownStartTime = millis();

      // 🌟 Clear the buffer after stop
      for (int i = 0; i < WINDOW; i++) confBuffer[i] = 0;
      bufferIndex = 0;
      Serial.println("Buffer cleared after stop.");
    }
    return;
  }

  if (isCooldown) {
    if (currentTime - cooldownStartTime >= COOLDOWN_PERIOD) {
      isCooldown = false;
      Serial.println("Cooldown finished, monitoring for new stop signs.");
    }
    return;
  }

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    int colonIndex = input.indexOf(':');
    if (colonIndex >= 0) {
      String label = input.substring(0, colonIndex);
      String confStr = input.substring(colonIndex + 1);
      confStr.replace("%", "");
      float confidence = confStr.toFloat();

      // 🚫 Ignore very weak detections
      if (confidence < 70.0) {
        Serial.println("Low confidence frame ignored.");
        return;
      }

      confBuffer[bufferIndex] = confidence;
      bufferIndex = (bufferIndex + 1) % WINDOW;

      float sum = 0;
      for (int i = 0; i < WINDOW; i++) sum += confBuffer[i];
      float averageConf = sum / WINDOW;

      Serial.print("Label: ");
      Serial.print(label);
      Serial.print(" | Confidence avg: ");
      Serial.println(averageConf);

      if (label.equals("stop_sign") && averageConf >= STOP_THRESHOLD) {
        Serial.println("High confidence stop sign detected. Starting braking...");
        startBraking();
      } else {
        runCar();
      }
    }
  }

  delay(50);
}

void runCar() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 255);
  analogWrite(ENB, 255);
}

void stopMotors() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

void startBraking() {
  isBraking = true;
  brakeStartTime = millis();
}
