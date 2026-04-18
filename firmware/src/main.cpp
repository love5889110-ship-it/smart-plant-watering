#include <Arduino.h>
#include "config.h"
#include "sensor.h"
#include "pump.h"
#include "mqtt_client.h"
#include "ble.h"

static unsigned long last_sensor_time = 0;
static unsigned long wifi_lost_time = 0;
static bool offline_mode = false;

void on_pump_command(unsigned long duration_ms, const char* reason) {
    Serial.printf("[MAIN] 执行浇水: %lu ms, 原因: %s\n", duration_ms, reason);
    pump_start(duration_ms);
    if (mqtt_is_connected()) {
        mqtt_publish_pump_status(true, duration_ms);
    }
}

static void check_offline_watering(float moisture) {
    if (moisture <= LOCAL_MOISTURE_LOW && !pump_is_running()) {
        Serial.printf("[OFFLINE] 湿度 %.1f%% 低于阈值 %d%%，本地触发浇水\n",
                      moisture, LOCAL_MOISTURE_LOW);
        pump_start(LOCAL_PUMP_DURATION);
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n============================");
    Serial.println("  智能浇花系统 启动中...");
    Serial.println("  WiFi + BLE 双模");
    Serial.println("============================");

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);

    sensor_init();
    pump_init();
    ble_init();
    mqtt_init();

    digitalWrite(LED_PIN, LOW);
    Serial.println("[MAIN] 初始化完成，开始运行");
}

void loop() {
    unsigned long now = millis();

    mqtt_update();
    pump_update();

    if (!mqtt_is_connected()) {
        if (wifi_lost_time == 0) {
            wifi_lost_time = now;
        } else if ((now - wifi_lost_time) > OFFLINE_FALLBACK_MS && !offline_mode) {
            offline_mode = true;
            Serial.println("[MAIN] 已切换到本地兜底模式");
        }
    } else {
        wifi_lost_time = 0;
        offline_mode = false;
    }

    if (now - last_sensor_time >= SENSOR_SAMPLE_MS) {
        last_sensor_time = now;

        float moisture = sensor_read_moisture_pct();
        int raw = sensor_read_raw();

        Serial.printf("[SENSOR] 湿度: %.1f%%  (raw: %d)  WiFi:%s  BLE:%s\n",
                      moisture, raw,
                      mqtt_is_connected() ? "在线" : "离线",
                      ble_is_connected()  ? "已连接" : "未连接");

        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);

        if (mqtt_is_connected()) {
            mqtt_publish_sensor(moisture, raw, pump_is_running());
        }

        ble_update_moisture(moisture, pump_is_running());

        if (offline_mode) {
            check_offline_watering(moisture);
        }
    }
}
