/*
 * MoveJoy Handheld Controller Firmware
 * Device: Seeed XIAO ESP32-S3
 *
 * Wiring:
 *   UP    button → D2 + GND
 *   DOWN  button → D3 + GND
 *   LEFT  button → D1 + GND
 *   RIGHT button → D0 + GND
 *   Vibration motor → D4
 *
 * BLE Service UUID:     4fafc201-1fb5-459e-8fcc-c5c9c331914b
 * Button Char UUID:     beb5483e-36e1-4688-b7f5-ea07361b26a8  [NOTIFY]
 *   Values sent: 0x01=UP  0x02=DOWN  0x03=LEFT  0x04=RIGHT
 * Haptic Char UUID:     beb5483e-36e1-4688-b7f5-ea07361b26a9  [WRITE]
 *   Values received: 0x01=short buzz  0x02=double buzz (wrong)
 */

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ── BLE UUIDs ─────────────────────────────────────────────────
#define SERVICE_UUID     "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_BUTTON_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_HAPTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// ── Pins (same as sample code) ────────────────────────────────
const int btnUp    = D2;
const int btnDown  = D1;
const int btnLeft  = D3;
const int btnRight = D0;
const int motorPin = D4;

// ── BLE globals ───────────────────────────────────────────────
BLEServer*         pServer         = nullptr;
BLECharacteristic* pButtonChar     = nullptr;
BLECharacteristic* pHapticChar     = nullptr;
bool               deviceConnected = false;
bool               wasConnected    = false;

// ── Forward declaration ───────────────────────────────────────
void buzz(int durationMs);

// ── BLE connection callbacks ──────────────────────────────────
class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* s) override {
    deviceConnected = true;
    Serial.println("[BLE] Client connected");
  }
  void onDisconnect(BLEServer* s) override {
    deviceConnected = false;
    Serial.println("[BLE] Client disconnected — restarting advertising");
  }
};

// ── Haptic write callback ─────────────────────────────────────
class HapticCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pChar) override {
    std::string val = pChar->getValue();
    if (val.empty()) return;
    uint8_t cmd = (uint8_t)val[0];
    if (cmd == 0x01) {
      buzz(80);
    } else if (cmd == 0x02) {
      buzz(60); delay(80); buzz(60);
    }
  }
};

// ── Motor helper ──────────────────────────────────────────────
void buzz(int durationMs) {
  digitalWrite(motorPin, HIGH);
  delay(durationMs);
  digitalWrite(motorPin, LOW);
}

// ── Setup ─────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(btnUp,    INPUT_PULLUP);
  pinMode(btnDown,  INPUT_PULLUP);
  pinMode(btnLeft,  INPUT_PULLUP);
  pinMode(btnRight, INPUT_PULLUP);

  pinMode(motorPin, OUTPUT);
  digitalWrite(motorPin, LOW);

  // Startup buzz
  buzz(100);

  // ── BLE init ──────────────────────────────────────────────
  BLEDevice::init("MoveJoy Controller");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  pButtonChar = pService->createCharacteristic(
    CHAR_BUTTON_UUID, BLECharacteristic::PROPERTY_NOTIFY
  );
  pButtonChar->addDescriptor(new BLE2902());

  pHapticChar = pService->createCharacteristic(
    CHAR_HAPTIC_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  pHapticChar->setCallbacks(new HapticCallbacks());

  pService->start();
  BLEDevice::getAdvertising()->addServiceUUID(SERVICE_UUID);
  BLEDevice::getAdvertising()->setScanResponse(true);
  BLEDevice::startAdvertising();

  Serial.println("[BLE] Advertising as 'MoveJoy Controller'");
}

// ── Loop ──────────────────────────────────────────────────────
void loop() {
  // Restart advertising after disconnect
  if (!deviceConnected && wasConnected) {
    delay(300);
    pServer->startAdvertising();
    wasConnected = false;
  }
  if (deviceConnected && !wasConnected) {
    wasConnected = true;
  }

  // Read buttons (same style as sample code)
  bool up    = digitalRead(btnUp)    == LOW;
  bool down  = digitalRead(btnDown)  == LOW;
  bool left  = digitalRead(btnLeft)  == LOW;
  bool right = digitalRead(btnRight) == LOW;

  // Motor on while any button held (same as sample code)
  digitalWrite(motorPin, (up || down || left || right) ? HIGH : LOW);

  // Send BLE notification on press
  static bool lastUp = false, lastDown = false, lastLeft = false, lastRight = false;

  if (up    && !lastUp)    { uint8_t c = 0x01; pButtonChar->setValue(&c,1); pButtonChar->notify(); Serial.println("[Button] UP");    }
  if (down  && !lastDown)  { uint8_t c = 0x02; pButtonChar->setValue(&c,1); pButtonChar->notify(); Serial.println("[Button] DOWN");  }
  if (left  && !lastLeft)  { uint8_t c = 0x03; pButtonChar->setValue(&c,1); pButtonChar->notify(); Serial.println("[Button] LEFT");  }
  if (right && !lastRight) { uint8_t c = 0x04; pButtonChar->setValue(&c,1); pButtonChar->notify(); Serial.println("[Button] RIGHT"); }

  lastUp    = up;
  lastDown  = down;
  lastLeft  = left;
  lastRight = right;

  delay(20);
}
