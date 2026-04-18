#include "ble.h"
#include <ArduinoJson.h>

// ============================================================
// 自定义 UUID（手机App用这些UUID发现和控制设备）
// ============================================================
#define BLE_SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define BLE_MOISTURE_UUID       "12345678-1234-1234-1234-123456789001"  // 只读+通知
#define BLE_PUMP_CMD_UUID       "12345678-1234-1234-1234-123456789002"  // 写入

static BLEServer*          _server = nullptr;
static BLECharacteristic*  _moisture_char = nullptr;
static BLECharacteristic*  _pump_cmd_char = nullptr;
static bool                _connected = false;

// ============================================================
// 连接状态回调
// ============================================================
class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* s) override {
        _connected = true;
        Serial.println("[BLE] 手机已连接");
    }
    void onDisconnect(BLEServer* s) override {
        _connected = false;
        Serial.println("[BLE] 手机已断开，重新广播...");
        BLEDevice::startAdvertising();
    }
};

// ============================================================
// 浇水指令写入回调
// 手机发送 JSON: {"duration_ms": 10000}
// ============================================================
class PumpCmdCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        String val = c->getValue().c_str();
        Serial.printf("[BLE] 收到指令: %s\n", val.c_str());
        StaticJsonDocument<128> doc;
        if (!deserializeJson(doc, val)) {
            unsigned long duration = doc["duration_ms"] | 8000UL;
            on_pump_command(duration, "ble");
        }
    }
};

// ============================================================
// 初始化
// ============================================================
void ble_init() {
    BLEDevice::init("智能浇花");
    _server = BLEDevice::createServer();
    _server->setCallbacks(new ServerCallbacks());

    BLEService* svc = _server->createService(BLE_SERVICE_UUID);

    // 湿度特征（通知）
    _moisture_char = svc->createCharacteristic(
        BLE_MOISTURE_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    _moisture_char->addDescriptor(new BLE2902());

    // 水泵控制特征（写入）
    _pump_cmd_char = svc->createCharacteristic(
        BLE_PUMP_CMD_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    _pump_cmd_char->setCallbacks(new PumpCmdCallbacks());

    svc->start();

    BLEAdvertising* adv = BLEDevice::getAdvertising();
    adv->addServiceUUID(BLE_SERVICE_UUID);
    adv->setScanResponse(true);
    BLEDevice::startAdvertising();

    Serial.println("[BLE] 蓝牙已启动，设备名: 智能浇花");
}

// ============================================================
// 推送湿度数据给已连接的手机
// ============================================================
void ble_update_moisture(float moisture_pct, bool pump_running) {
    if (!_connected || !_moisture_char) return;
    StaticJsonDocument<128> doc;
    doc["m"] = (int)(moisture_pct * 10) / 10.0;
    doc["p"] = pump_running;
    char buf[128];
    serializeJson(doc, buf);
    _moisture_char->setValue(buf);
    _moisture_char->notify();
}

bool ble_is_connected() {
    return _connected;
}
