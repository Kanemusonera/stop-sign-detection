// motor_direction_test.ino
//
// Drives both motors continuously forward at full speed. The first thing to
// upload when wiring a new chassis: it answers "do the motors turn, and do
// both wheels drive the vehicle the same way?"
//
// STATUS: verified. Confirmed working after the two fixes below.
//
// ── TWO THINGS THAT COST REAL DEBUGGING TIME ─────────────────────────────
//
// 1. COMMON GROUND. The Arduino GND and the L298N GND must be tied together.
//    Without it the motors do absolutely nothing and no error appears
//    anywhere — it looks like a code problem and it isn't.
//
// 2. ONE MOTOR IS MOUNTED MIRRORED. Because the two motors face opposite
//    directions on the chassis, identical logic levels spin them in opposite
//    rotational directions, so the vehicle turns on the spot instead of
//    driving forward. Fixed by physically reversing one motor's output leads
//    at the L298N, not in software. If you rewire this chassis, that swap has
//    to be preserved or the code below stops meaning what it says.
//
// ── WIRING ────────────────────────────────────────────────────────────────
//   L298N IN1 -> D7      L298N IN3 -> D5      L298N ENA -> D9  (PWM)
//   L298N IN2 -> D6      L298N IN4 -> D4      L298N ENB -> D10 (PWM)
//   L298N GND -> Arduino GND    (see note 1)
//   Motor A -> OUT1/OUT2        Motor B -> OUT3/OUT4
//   Battery + -> L298N motor supply, Battery - -> L298N GND
//
// Remove the ENA/ENB jumpers before driving those pins with PWM. Leave them
// fitted only if running at fixed full speed off the 5V rail.

const int IN1 = 7;
const int IN2 = 6;
const int IN3 = 5;
const int IN4 = 4;
const int ENA = 9;
const int ENB = 10;

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);
}

void loop() {
  // Both motors forward
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 255);
  analogWrite(ENB, 255);
}
