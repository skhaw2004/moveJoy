#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ── Pin definitions ───────────────────────────────────────────
#define PIN_VIBRATE  1
#define PIN_LEFT     2
#define PIN_UP       3
#define PIN_DOWN     4
#define PIN_SELECT   5
#define PIN_RIGHT    6

// ── BLE UUIDs (must match game) ───────────────────────────────
#define SERVICE_UUID   "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define BTN_CHAR_UUID  "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define HAP_CHAR_UUID  "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// ── Button codes (must match game) ────────────────────────────
#define CODE_UP      0x01
#define CODE_DOWN    0x02
#define CODE_LEFT    0x03
#define CODE_RIGHT   0x04
#define CODE_SELECT  0x05

// ── Haptic config ─────────────────────────────────────────────
#define HAP_CORRECT  0x01
#define HAP_WRONG    0x02
#define HAP_DURATION_CORRECT 80
#define HAP_DURATION_WRONG   200

BLECharacteristic* btnChar;
bool deviceConnected = false;

struct Button {
  uint8_t pin;
  uint8_t code;
  bool lastState;
  unsigned long lastDebounce;
};

Button buttons[] = {
  { PIN_UP,     CODE_UP,     HIGH, 0 },
  { PIN_DOWN,   CODE_DOWN,   HIGH, 0 },
  { PIN_LEFT,   CODE_LEFT,   HIGH, 0 },
  { PIN_RIGHT,  CODE_RIGHT,  HIGH, 0 },
  { PIN_SELECT, CODE_SELECT, HIGH, 0 },
};
const int NUM_BUTTONS = 5;
const unsigned long DEBOUNCE_MS = 30;

unsigned long hapticOffTime = 0;

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* s)    { deviceConnected = true; }
  void onDisconnect(BLEServer* s) {
    deviceConnected = false;
    BLEDevice::startAdvertising();
  }
};

class HapticCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) {
    uint8_t* data = c->getData();
    if (data[0] == HAP_CORRECT) {
      digitalWrite(PIN_VIBRATE, HIGH);
      hapticOffTime = millis() + HAP_DURATION_CORRECT;
    } else if (data[0] == HAP_WRONG) {
      digitalWrite(PIN_VIBRATE, HIGH);
      hapticOffTime = millis() + HAP_DURATION_WRONG;
    }
  }
};

void setup() {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(buttons[i].pin, INPUT_PULLUP);
  }

  pinMode(PIN_VIBRATE, OUTPUT);
  digitalWrite(PIN_VIBRATE, LOW);

  BLEDevice::init("MoveJoy Controller");
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService* service = server->createService(SERVICE_UUID);

  btnChar = service->createCharacteristic(
    BTN_CHAR_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  btnChar->addDescriptor(new BLE2902());

  BLECharacteristic* hapChar = service->createCharacteristic(
    HAP_CHAR_UUID,
    BLECharacteristic::PROPERTY_WRITE_NR
  );
  hapChar->setCallbacks(new HapticCallbacks());

  service->start();

  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void loop() {
  if (hapticOffTime > 0 && millis() >= hapticOffTime) {
    digitalWrite(PIN_VIBRATE, LOW);
    hapticOffTime = 0;
  }

  if (!deviceConnected) return;

  for (int i = 0; i < NUM_BUTTONS; i++) {
    bool state = digitalRead(buttons[i].pin);
    if (state != buttons[i].lastState &&
        millis() - buttons[i].lastDebounce > DEBOUNCE_MS) {
      buttons[i].lastDebounce = millis();
      buttons[i].lastState = state;
      if (state == LOW) {
        uint8_t code = buttons[i].code;
        btnChar->setValue(&code, 1);
        btnChar->notify();
      }
    }
  }
}