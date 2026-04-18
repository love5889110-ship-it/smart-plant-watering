#include "pump.h"

static bool _running = false;
static unsigned long _start_time = 0;
static unsigned long _duration = 0;
static unsigned long _last_stop = 0;

void pump_init() {
    pinMode(PUMP_PIN, OUTPUT);
    digitalWrite(PUMP_PIN, LOW);
}

void pump_start(unsigned long duration_ms) {
    // 强制不超过安全上限
    if (duration_ms > MAX_PUMP_DURATION_MS) {
        duration_ms = MAX_PUMP_DURATION_MS;
    }
    // 检查最短间隔（上次停泵到现在）
    if (_last_stop > 0 && (millis() - _last_stop) < MIN_PUMP_INTERVAL_MS) {
        Serial.println("[PUMP] 间隔太短，跳过本次浇水");
        return;
    }
    _duration = duration_ms;
    _start_time = millis();
    _running = true;
    digitalWrite(PUMP_PIN, HIGH);
    Serial.printf("[PUMP] 开始浇水 %lu ms\n", duration_ms);
}

void pump_stop() {
    if (_running) {
        _running = false;
        _last_stop = millis();
        digitalWrite(PUMP_PIN, LOW);
        Serial.println("[PUMP] 水泵停止");
    }
}

bool pump_is_running() {
    return _running;
}

void pump_update() {
    if (_running && (millis() - _start_time) >= _duration) {
        pump_stop();
    }
}

unsigned long pump_last_stop_time() {
    return _last_stop;
}
