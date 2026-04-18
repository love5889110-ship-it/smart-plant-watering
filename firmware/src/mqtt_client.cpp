#include "mqtt_client.h"
#include <ArduinoJson.h>

static WiFiClient _wifi_client;
static PubSubClient _mqtt(_wifi_client);
static unsigned long _last_reconnect_attempt = 0;
static unsigned long _last_mqtt_ok_time = 0;

// MQTT消息接收回调
static void _on_message(char* topic, byte* payload, unsigned int length) {
    // 解析JSON指令
    StaticJsonDocument<200> doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) {
        Serial.println("[MQTT] JSON解析失败");
        return;
    }

    if (strcmp(topic, TOPIC_PUMP_CMD) == 0) {
        unsigned long duration = doc["duration_ms"] | 8000UL;
        const char* reason = doc["reason"] | "server";
        Serial.printf("[MQTT] 收到浇水指令: %lu ms, 原因: %s\n", duration, reason);
        on_pump_command(duration, reason);
    }
}

static void _connect_wifi() {
    Serial.printf("[WiFi] 连接 %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int tries = 0;
    while (WiFi.status() != WL_CONNECTED && tries < 20) {
        delay(500);
        Serial.print(".");
        tries++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WiFi] 连接成功! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WiFi] 连接失败，将使用本地兜底模式");
    }
}

static bool _reconnect_mqtt() {
    if (_mqtt.connected()) return true;
    Serial.print("[MQTT] 尝试连接...");
    // 设置LWT遗嘱：掉线时自动发布离线状态
    String lwt_topic = String("plant/") + DEVICE_ID + "/heartbeat";
    String lwt_msg = "{\"online\":false,\"device_id\":\"" DEVICE_ID "\"}";
    bool ok = _mqtt.connect(DEVICE_ID, nullptr, nullptr,
                            lwt_topic.c_str(), 0, true, lwt_msg.c_str());
    if (ok) {
        Serial.println("成功");
        _mqtt.subscribe(TOPIC_PUMP_CMD);
        _last_mqtt_ok_time = millis();
        // 上线公告
        String online_msg = "{\"online\":true,\"device_id\":\"" DEVICE_ID "\"}";
        _mqtt.publish(lwt_topic.c_str(), online_msg.c_str(), true);
    } else {
        Serial.printf("失败, rc=%d\n", _mqtt.state());
    }
    return ok;
}

void mqtt_init() {
    _connect_wifi();
    _mqtt.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
    _mqtt.setCallback(_on_message);
    _mqtt.setKeepAlive(60);
    _mqtt.setBufferSize(512);
    _reconnect_mqtt();
}

void mqtt_update() {
    if (WiFi.status() != WL_CONNECTED) {
        return;
    }
    if (!_mqtt.connected()) {
        unsigned long now = millis();
        if (now - _last_reconnect_attempt > MQTT_RECONNECT_MS) {
            _last_reconnect_attempt = now;
            _reconnect_mqtt();
        }
    } else {
        _last_mqtt_ok_time = millis();
        _mqtt.loop();
    }
}

void mqtt_publish_sensor(float moisture_pct, int moisture_raw, bool pump_running) {
    if (!_mqtt.connected()) return;
    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID;
    doc["moisture_pct"] = (int)(moisture_pct * 10) / 10.0; // 保留1位小数
    doc["moisture_raw"] = moisture_raw;
    doc["pump_running"] = pump_running;
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["uptime_s"] = millis() / 1000;
    char buf[256];
    serializeJson(doc, buf);
    _mqtt.publish(TOPIC_SENSOR, buf);
}

void mqtt_publish_pump_status(bool running, unsigned long duration_ms) {
    if (!_mqtt.connected()) return;
    StaticJsonDocument<128> doc;
    doc["device_id"] = DEVICE_ID;
    doc["running"] = running;
    doc["duration_ms"] = duration_ms;
    char buf[128];
    serializeJson(doc, buf);
    _mqtt.publish(TOPIC_PUMP_ACK, buf);
}

bool mqtt_is_connected() {
    return _mqtt.connected();
}
