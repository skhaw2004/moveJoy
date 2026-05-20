#include <Arduino.h>
#include <Wire.h>
#include <math.h>

static const uint8_t IMU_ADDR = 0x68;

static const uint8_t REG_WHO_AM_I    = 0x75;
static const uint8_t REG_PWR_MGMT_1   = 0x6B;
static const uint8_t REG_ACCEL_CONFIG = 0x1C;
static const uint8_t REG_GYRO_CONFIG  = 0x1B;
static const uint8_t REG_ACCEL_XOUT_H = 0x3B;

uint8_t read8(uint8_t reg) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0xFF;
  if (Wire.requestFrom(IMU_ADDR, (uint8_t)1) != 1) return 0xFF;
  return Wire.read();
}

void write8(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

int16_t read16(uint8_t reg) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0;
  if (Wire.requestFrom(IMU_ADDR, (uint8_t)2) != 2) return 0;
  uint8_t hi = Wire.read();
  uint8_t lo = Wire.read();
  return (int16_t)((hi << 8) | lo);
}

struct ImuData {
  float ax, ay, az;
};

ImuData readAccel() {
  int16_t ax_raw = read16(REG_ACCEL_XOUT_H);
  int16_t ay_raw = read16(REG_ACCEL_XOUT_H + 2);
  int16_t az_raw = read16(REG_ACCEL_XOUT_H + 4);

  ImuData d;
  d.ax = ax_raw / 16384.0f;
  d.ay = ay_raw / 16384.0f;
  d.az = az_raw / 16384.0f;
  return d;
}

// Gravity estimate
float gX = 0.0f, gY = 0.0f, gZ = 1.0f;

// Noise calibration
float noiseX = 0.0f;
float noiseY = 0.0f;

// Gesture window
float sumLX = 0.0f;
float sumLY = 0.0f;
unsigned long windowStart = 0;
bool windowActive = false;
unsigned long lastGestureTime = 0;

const float gravityAlpha = 0.985f;
const unsigned long windowMs = 550;
const unsigned long cooldownMs = 1200;

// Tuning
const float minStartFloor = 0.0025f;
const float minDeadFloor  = 0.0012f;
const float upBoost       = 1.45f;
const float dominance     = 1.30f;

String classifyGesture(float x, float y) {
  // Make UP a little easier to detect
  y *= upBoost;

  float ax = fabs(x);
  float ay = fabs(y);

  const float minMag = 0.0035f;
  if (ax < minMag && ay < minMag) return "NONE";

  // Strong horizontal preference
  if (ax > ay * dominance) {
    // Your left/right mapping is already close to correct
    return (x > 0) ? "LEFT" : "RIGHT";
  }

  // Only allow UP, never DOWN
  if (ay > ax * dominance) {
    return (y > 0) ? "UP" : "NONE";
  }

  return "NONE";
}

void calibrateNoise() {
  Serial.println("Hold the IMU still for calibration...");

  const int samples = 120;
  float totalAbsX = 0.0f;
  float totalAbsY = 0.0f;

  for (int i = 0; i < samples; i++) {
    ImuData d = readAccel();

    gX = gravityAlpha * gX + (1.0f - gravityAlpha) * d.ax;
    gY = gravityAlpha * gY + (1.0f - gravityAlpha) * d.ay;
    gZ = gravityAlpha * gZ + (1.0f - gravityAlpha) * d.az;

    float lx = d.ax - gX;
    float ly = d.ay - gY;

    totalAbsX += fabs(lx);
    totalAbsY += fabs(ly);

    delay(20);
  }

  noiseX = totalAbsX / samples;
  noiseY = totalAbsY / samples;

  if (noiseX < minStartFloor) noiseX = minStartFloor;
  if (noiseY < minStartFloor) noiseY = minStartFloor;

  Serial.print("Noise X = ");
  Serial.println(noiseX, 6);
  Serial.print("Noise Y = ");
  Serial.println(noiseY, 6);
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Wire.begin();

  Serial.println("Starting IMU gesture test...");

  uint8_t who = read8(REG_WHO_AM_I);
  Serial.print("WHO_AM_I = 0x");
  Serial.println(who, HEX);

  write8(REG_PWR_MGMT_1, 0x00);
  delay(100);

  write8(REG_ACCEL_CONFIG, 0x00);
  write8(REG_GYRO_CONFIG, 0x00);

  calibrateNoise();

  Serial.println("Ready. Use single LEFT / RIGHT / UP swipes.");
}

void loop() {
  ImuData d = readAccel();

  // Gravity estimate
  gX = gravityAlpha * gX + (1.0f - gravityAlpha) * d.ax;
  gY = gravityAlpha * gY + (1.0f - gravityAlpha) * d.ay;
  gZ = gravityAlpha * gZ + (1.0f - gravityAlpha) * d.az;

  // Linear acceleration
  float lx = d.ax - gX;
  float ly = d.ay - gY;

  // Per-axis thresholds based on noise
  float startThresholdX = max(noiseX * 5.0f, 0.0040f);
  float startThresholdY = max(noiseY * 5.0f, 0.0035f);

  float deadZoneX = max(noiseX * 2.5f, 0.0015f);
  float deadZoneY = max(noiseY * 2.5f, 0.0015f);

  // Start a window if either axis clearly moves
  if (!windowActive && (millis() - lastGestureTime > cooldownMs)) {
    if (fabs(lx) > startThresholdX || fabs(ly) > startThresholdY) {
      windowActive = true;
      windowStart = millis();
      sumLX = 0.0f;
      sumLY = 0.0f;
    }
  }

  if (windowActive) {
    if (fabs(lx) > deadZoneX) sumLX += lx;
    if (fabs(ly) > deadZoneY) sumLY += ly;

    if (millis() - windowStart >= windowMs) {
      String gesture = classifyGesture(sumLX, sumLY);

      if (gesture != "NONE") {
        Serial.print("Gesture detected: ");
        Serial.println(gesture);
        lastGestureTime = millis();
      }

      windowActive = false;
    }
  }

  delay(20);
}