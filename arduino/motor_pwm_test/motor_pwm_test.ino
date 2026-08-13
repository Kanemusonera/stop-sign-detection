// motor_pwm_test.ino
//
// Ramps both motors up to full speed and back down, repeatedly. Verifies that
// PWM speed control works on the enable pins, as distinct from simply having
// the motors turn on and off.
//
// Upload this after motor_direction_test confirms direction and wiring.
//
// STATUS: verified. This sketch spins the motors correctly on the pin mapping
// below. A variant using IN1=2, IN2=3, IN3=4, IN4=5 was also tried and left
// one wheel dead — that mapping is not used anywhere in this project.
//
// ── WIRING ────────────────────────────────────────────────────────────────
//   L298N IN1 -> D7      L298N IN3 -> D5      L298N ENA -> D9  (PWM)
//   L298N IN2 -> D6      L298N IN4 -> D4      L298N ENB -> D10 (PWM)
//   L298N GND -> Arduino GND
//
// The ENA/ENB jumpers MUST be removed for this sketch. With the jumpers
// fitted the enable pins are held high and the analogWrite calls below do
// nothing — the motors just run flat out.
//
// Motors typically will not start turning until the duty cycle reaches
// roughly 100-130 depending on load and battery state, so the low end of the
// ramp is expected to be silent.

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

  // Both motors forward for the whole test; only speed changes.
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void loop() {
  // Accelerate
  for (int speed = 0; speed <= 255; speed += 5) {
    analogWrite(ENA, speed);
    analogWrite(ENB, speed);
    delay(30);
  }

  delay(1000);

  // Decelerate
  for (int speed = 255; speed >= 0; speed -= 5) {
    analogWrite(ENA, speed);
    analogWrite(ENB, speed);
    delay(30);
  }

  delay(1000);
}
