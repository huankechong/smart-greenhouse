/*
 * ============================================================
 *  智能花房养护站 Smart GreenHouse — 主程序框架 v1
 *  《Introduction to Project Work》Final Project
 *  Liu Junbo · x20260134 · DT1班
 * ============================================================
 *  设计思路：一套代码从 W1 用到答辩。文件头部的"功能开关"
 *  每周开启一个，改完重新编译上传即可，代码不用大动：
 *
 *    W1  传感器逐个点亮 → 全部开关保持 0，串口看数据
 *    W2  执行闭环       → 接好继电器+水泵后 EN_WATER=1
 *    W3  上云           → EN_WIFI/EN_MQTT/EN_WEB 改 1
 *
 *  上传提示（踩过的坑）：如果报 "not responding / not in sync"，
 *  按住板上 BOOT 键再点上传，出现 Connecting 后松开。
 *
 *  v1.1（2026-10-17 代码审计修复）：修复 0% 哨兵误判、WiFi 掉线不重连、
 *  手动浇水改非阻塞、凭据移入 config.h、魔法数字常量化、标定防呆自检。
 *  详见《AR01_GreenHouse代码审计修复报告_2026-10-17.md》
 *
 *  v1.2（2026-10-19 异常保护）：补两条"长期跑会出事"的缺口——
 *    ① 连浇上限：连续 MAX_ROUNDS_PER_CYCLE 轮仍判缺水 → 停水冷却 10 分钟并红灯快闪
 *       （防传感器脱土/线松导致每 33 秒一轮、无限浇下去）
 *    ② 低水位保护：EN_LEVEL=1 时读雨滴/浮球开关，水位低则拒绝启动、浇到一半也会停泵
 *       （防水箱空了泵空转干烧）
 *  两条都是"默认关闭"，接好传感器再开，不影响 W1/W2 的既有节奏。
 */

// ==================== 功能开关（按周开启） ====================
#define EN_DHT    0   // W1-D5：接好温湿度(41号)后改 1 → 需装 DHT sensor library
#define EN_OLED   0   // W1-D5：接好 OLED(25号)后改 1  → 需装 U8g2
#define EN_WATER  0   // W2-D8：接好继电器(16号)+水泵后改 1（注意：会真实出水！）
#define EN_WIFI   0   // W3-D11：上云时改 1 → 需装 PubSubClient
#define EN_MQTT   0   // 依赖 EN_WIFI=1：数据上报 + 远程浇水
#define EN_WEB    0   // 依赖 EN_WIFI=1：局域网保底网页（断外网手机也能看）
#define EN_LEVEL  0   // v1.2：接好水位检测（雨滴26号贴瓶壁 / 浮球开关）后改 1 → 低水位停泵

// ==================== 引脚定义（对照《花房接线规划表.md》） ====================
#define PIN_SOIL    34   // 土壤湿度 AO → ADC1（只读脚，不能接输出设备）
#define PIN_LIGHT   35   // 光敏 AO    → ADC1（只读脚）
#define PIN_DHT     33   // 温湿度 DATA（41号）
#define PIN_RELAY   26   // 继电器 IN（16号）
#define PIN_LED_R   25   // 双色LED 红（13号，课堂双色LED实验件复用为状态灯）
#define PIN_LED_G   27   // 双色LED 绿（13号）
#define PIN_RAIN    32   // v1.2 水位检测 AO（26号雨滴模块 / 水位开关）→ ADC1，EN_LEVEL=1 才读

// ==================== 标定/浇水参数（到货实测后改这里） ====================
const int SOIL_RAW_DRY = 3200;        // 探针全干的 raw 读数 → W1-4.1 实测后修改！
const int SOIL_RAW_WET = 1300;        // 探针全湿的 raw 读数 → W1-4.1 实测后修改！
const int SOIL_THRESHOLD_PCT  = 35;   // 土壤湿度% 低于此值 → 判定缺水
const unsigned long WATER_MS  = 3000;    // 每轮浇水 3 秒
const unsigned long SETTLE_MS = 30000;   // 浇完等 30 秒复测（防反复触发）
const unsigned long MANUAL_WATER_MS = 5000; // 远程手动浇水 5 秒
const int RELAY_ACTIVE_HIGH = 1;  // 继电器触发极性：吸合=高电平填1；实测相反就改0

// ---------- v1.2 异常保护参数 ----------
const int           MAX_ROUNDS_PER_CYCLE = 6;        // 一次处理最多连浇 6 轮（6×3s=18s 水）
const unsigned long COOLDOWN_MS  = 600000;           // 触发上限后冷却 10 分钟再恢复自动
const int           LEVEL_DRY_RAW = 2500;            // [实测标定] 水位检测 raw 高于此值 → 判定缺水
                                                     // 电阻式雨滴模块：干=高、湿=低；浮球开关请改判断极性

// ---------- 运行周期参数（v1.1 常量化，改节奏只动这里） ----------
const unsigned long SENSOR_INTERVAL_MS  = 5000;   // 传感器采样 + 串口打印周期
const unsigned long OLED_INTERVAL_MS    = 1000;   // OLED 刷新周期
const unsigned long PUBLISH_INTERVAL_MS = 10000;  // 云端上报周期
const unsigned long WIFI_TIMEOUT_MS     = 15000;  // 启动时连 WiFi 的超时
const unsigned long WIFI_RETRY_MS       = 30000;  // 运行中掉线自动重连间隔

// ==================== 巴法云配置（W3 只需填 WiFi 和 UID） ====================
#if EN_WIFI
#include <WiFi.h>
#include "config.h"               // WiFi/UID 凭据集中管理，分享前脱敏（见 config.h 头注释）
unsigned long lastWifiRetry = 0;  // WiFi 掉线重连计时（v1.1：支持运行中自动重连）
#endif
#if EN_MQTT
#include <PubSubClient.h>
#include "config.h"               // MQTT_UID 在 config.h（含 include guard，重复包含安全）
const char* MQTT_SERVER = "bemfa.com";
const int   MQTT_PORT   = 9501;
const char* TOPIC_DATA  = "cYQ9geudA004";  // 传感器主题(004)数据上行——真实主题名，已建好勿改
const char* TOPIC_CMD   = "4QT4BZIBM001";  // 插座主题(001)指令下行——真实主题名，已建好勿改
const unsigned long MQTT_RETRY_MS = 5000;  // MQTT 重连间隔
WiFiClient espClient;
PubSubClient mqtt(espClient);
unsigned long lastMqttRetry = 0;
#endif

// ==================== 传感器/OLED 对象 ====================
#if EN_DHT
#include <DHT.h>
DHT dht(PIN_DHT, DHT11);
#endif
#if EN_OLED
#include <U8g2lib.h>
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
#endif
#if EN_WEB
#include <WebServer.h>   // ESP32 核心自带，无需安装
WebServer server(80);
#endif

// ==================== 全局读数 ====================
int   gSoilRaw = 0, gSoilPct = 0;
int   gLightRaw = 0;
float gTemp = NAN, gHum = NAN;
bool  gSensorReady = false;     // 首次读数完成标志：0% 是合法湿度，不能拿 0 当"无数据"哨兵（v1.1 修复）
bool  gLevelLow = false;        // v1.2：水位过低标志（EN_LEVEL=1 时才更新）
int   waterState = 0;          // 0=监视 1=浇水中 2=停水复测中 3=远程手动浇水中 4=冷却保护中
int   waterRounds = 0;         // v1.2：本处理周期已连浇轮数，恢复湿度或冷却结束时清零
unsigned long waterTimer = 0;
unsigned long manualMs = 0;     // 状态3手动浇水的时长
unsigned long lastLevelWarn = 0; // v1.2：低水位日志节流（10 秒一条，防串口刷屏）

// ---------- 继电器极性封装（低电平触发的模块只需改 RELAY_ACTIVE_HIGH） ----------
void relayOn()  { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? HIGH : LOW); }
void relayOff() { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? LOW  : HIGH); }

// ---------- 模拟口均值滤波：10 次取平均，抑制读数抖动（报告可写的技术点） ----------
int readAverage(int pin) {
  long sum = 0;
  for (int i = 0; i < 10; i++) { sum += analogRead(pin); delay(5); }
  return sum / 10;
}

void readSensors() {
  gSoilRaw  = readAverage(PIN_SOIL);
  // 电容式传感器：干=高raw 湿=低raw → 映射成 0-100%
  gSoilPct  = constrain(map(gSoilRaw, SOIL_RAW_WET, SOIL_RAW_DRY, 100, 0), 0, 100);
  gLightRaw = readAverage(PIN_LIGHT);
#if EN_LEVEL
  // 电阻式雨滴/水位板：干（无水）= 高 raw；湿（泡到水）= 低 raw
  gLevelLow = (readAverage(PIN_RAIN) > LEVEL_DRY_RAW);
#endif
#if EN_DHT
  gHum  = dht.readHumidity();
  gTemp = dht.readTemperature();
#endif
}

// ---------- 串口打印：W1 全部"串口截图"素材都从这里来 ----------
void printSensors() {
  Serial.printf("[数据] 土壤raw=%d 湿度=%d%% | 光照raw=%d", gSoilRaw, gSoilPct, gLightRaw);
#if EN_LEVEL
  Serial.printf(" | 水位=%s", gLevelLow ? "低!!" : "正常");
#endif
#if EN_DHT
  if (!isnan(gTemp)) Serial.printf(" | 温度=%.1fC 气湿=%.0f%%", gTemp, gHum);
#endif
  Serial.println();
}

// ---------- 状态灯：绿=正常 / 红=缺水 / 红300ms闪=浇水中 / 红100ms快闪=保护冷却 / 红1s慢闪=水位低 ----------
void updateStatusLed() {
  if (waterState == 1) {                        // 浇水中：红灯 300ms 闪烁
    digitalWrite(PIN_LED_R, (millis() / 300) % 2);
    digitalWrite(PIN_LED_G, LOW);
    return;
  }
  if (waterState == 4) {                        // v1.2 冷却保护：红灯 100ms 快闪（一眼看出"出事了"）
    digitalWrite(PIN_LED_R, (millis() / 100) % 2);
    digitalWrite(PIN_LED_G, LOW);
    return;
  }
#if EN_LEVEL
  if (gLevelLow) {                              // v1.2 水位低：红灯 1s 慢闪，与"缺水常亮"区分
    digitalWrite(PIN_LED_R, (millis() / 1000) % 2);
    digitalWrite(PIN_LED_G, LOW);
    return;
  }
#endif
  digitalWrite(PIN_LED_R, (gSensorReady && gSoilPct < SOIL_THRESHOLD_PCT) ? HIGH : LOW);  // v1.1：0% 也亮红灯
  digitalWrite(PIN_LED_G, (gSoilPct >= SOIL_THRESHOLD_PCT) ? HIGH : LOW);
}

// ---------- 自动浇水状态机：监视 → 浇3秒 → 停30秒复测 → 仍干再浇（最多 6 轮）→ 冷却 ----------
void waterTick() {
#if EN_WATER
  unsigned long now = millis();

  // ---- 状态 4：冷却保护（v1.2）----
  if (waterState == 4) {
    if (now - waterTimer >= COOLDOWN_MS) {
      waterRounds = 0; waterState = 0; waterTimer = now;
      Serial.println("[保护] 冷却结束，恢复自动监测");
    }
    return;
  }

  // ---- 状态 3：远程手动浇水（v1.1 非阻塞：期间 MQTT/Web 照常响应）----
  if (waterState == 3) {
    if (now - waterTimer >= manualMs) {
      relayOff(); waterState = 0; waterTimer = now;
      digitalWrite(PIN_LED_R, LOW);
      Serial.println("[远程] 手动浇水完成");
    }
    return;
  }

  // ---- 状态 0：监视 ----
  if (waterState == 0) {
    if (!gSensorReady) return;
#if EN_LEVEL
    if (gLevelLow) {                            // v1.2：水箱没水就绝不启动，日志 10s 一条防刷屏
      if (now - lastLevelWarn >= 10000) {
        lastLevelWarn = now;
        Serial.println("[保护] 水位过低，暂停自动浇水（请给蓄水瓶补水）");
      }
      return;
    }
#endif
    if (gSoilPct < SOIL_THRESHOLD_PCT) {        // v1.1：去掉 >0 哨兵，0% 也触发
      waterRounds++;
      Serial.printf("[自动] 判定缺水，开始第 %d/%d 轮浇水\n", waterRounds, MAX_ROUNDS_PER_CYCLE);
      relayOn(); waterState = 1; waterTimer = now;
    }
    return;
  }

  // ---- 状态 1：浇水中 ----
  if (waterState == 1) {
#if EN_LEVEL
    if (gLevelLow) {                            // v1.2：浇到一半水抽干了 → 立刻停泵
      relayOff(); waterState = 0; waterRounds = 0; waterTimer = now;
      Serial.println("[保护] 浇水过程中水位过低，已立即停泵");
      return;
    }
#endif
    if (now - waterTimer >= WATER_MS) {
      relayOff(); waterState = 2; waterTimer = now;
      Serial.println("[自动] 本轮浇完，30秒后复测");
    }
    return;
  }

  // ---- 状态 2：停水复测 ----
  if (waterState == 2) {
    if (now - waterTimer >= SETTLE_MS) {
      readSensors();                            // 复测（"浇一段—停—复测"策略）
      if (gSoilPct < SOIL_THRESHOLD_PCT) {
        if (waterRounds >= MAX_ROUNDS_PER_CYCLE) {          // v1.2 上限保护
          waterState = 4; waterTimer = now;
          Serial.printf("[保护] 已连浇 %d 轮仍判缺水 —— 传感器可能脱土/线松/故障，停止浇水并冷却 %lu 分钟\n",
                        waterRounds, COOLDOWN_MS / 60000UL);
        } else {
          Serial.println("[自动] 复测仍缺水，再浇一轮");
          relayOn(); waterState = 1; waterTimer = now;
        }
      } else {
        Serial.println("[自动] 湿度已恢复，本轮结束");
        waterState = 0; waterRounds = 0;
      }
    }
  }
#endif
}

#if EN_WATER
void manualWaterStart(unsigned long ms) {       // 远程手动浇水启动（v1.1 改非阻塞，实际计时在 waterTick 状态3）
#if EN_LEVEL
  if (gLevelLow) {                              // v1.2：没水就别让泵空转
    Serial.println("[远程] 拒绝：水位过低，请先给蓄水瓶补水");
    return;
  }
#endif
  Serial.println("[远程] 手动浇水开始");
  digitalWrite(PIN_LED_R, HIGH);
  relayOn();
  manualMs = ms; waterState = 3; waterTimer = millis();
}
#endif

#if EN_MQTT
void publishTo(const char* topic, const char* payload) {
  if (mqtt.connected()) mqtt.publish(topic, payload);
}

void mqttCallback(char* topic, byte* payload, unsigned int len) {
  String msg = "";
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  msg.trim();                                   // v1.1：去首尾空白/换行，防误匹配
  Serial.printf("[MQTT] 收到 %s: %s\n", topic, msg.c_str());
  if (String(topic) == TOPIC_CMD && msg == "on") {   // v1.1：精确匹配 on，避免 "online" 答案串误触发
#if EN_WATER
    manualWaterStart(MANUAL_WATER_MS);
#endif
    publishTo(TOPIC_CMD, "off");               // 回写 off，防服务器残留消息重复触发
  }
}

void mqttConnect() {                            // 非阻塞重连
  unsigned long now = millis();
  if (mqtt.connected() || now - lastMqttRetry < MQTT_RETRY_MS) return;
  lastMqttRetry = now;
  Serial.print("[MQTT] 连接巴法云...");
  if (mqtt.connect(String(MQTT_UID).c_str())) { // 巴法云 clientID 必须等于 UID
    Serial.println("成功");
    mqtt.subscribe(TOPIC_CMD);
  } else {
    Serial.printf("失败(rc=%d)，%.0f秒后重试\n", mqtt.state(), MQTT_RETRY_MS / 1000.0);
  }
}

void publishData() {                            // 巴法云004格式：字段#值|字段#值
  String p = "土壤#" + String(gSoilPct) + "|光照#" + String(gLightRaw);
#if EN_DHT
  if (!isnan(gTemp)) p += "|温度#" + String(gTemp, 1) + "|气湿#" + String(gHum, 0);
#endif
#if EN_WATER
  const char* st = "正常";
  if (waterState == 1) st = "浇水中";
  else if (waterState == 2) st = "复测中";
  else if (waterState == 3) st = "手动";
  else if (waterState == 4) st = "冷却保护";
  p += "|状态#" + String(st);
#endif
#if EN_LEVEL
  p += "|水位#" + String(gLevelLow ? "低" : "正常");
#endif
  publishTo(TOPIC_DATA, p.c_str());
  Serial.println("[MQTT] 上行: " + p);
}
#endif

#if EN_WEB
void handleRoot() {                             // 局域网保底网页（答辩断网兜底之一）
  String h = "<meta charset='utf-8'><h2>智能花房养护站</h2>";
  h += "<p>土壤湿度: " + String(gSoilPct) + "%</p><p>光照raw: " + String(gLightRaw) + "</p>";
#if EN_DHT
  if (!isnan(gTemp)) h += "<p>温度: " + String(gTemp, 1) + " C | 气湿: " + String(gHum, 0) + "%</p>";
#endif
#if EN_LEVEL
  h += String("<p>水位: ") + (gLevelLow ? "<b style='color:#c00'>过低</b>" : "正常") + "</p>";
#endif
  server.send(200, "text/html", h);
}
#endif

void setup() {
  Serial.begin(115200);
  Serial.println("\n===== 智能花房养护站 v1.2 启动 =====");
  Serial.printf("功能开关: DHT=%d OLED=%d WATER=%d LEVEL=%d WIFI=%d MQTT=%d WEB=%d\n",
                EN_DHT, EN_OLED, EN_WATER, EN_LEVEL, EN_WIFI, EN_MQTT, EN_WEB);   // v1.1：排障先看烧的是哪套配置
  Serial.printf("标定: dry=%d wet=%d 缺水阈值=%d%%\n", SOIL_RAW_DRY, SOIL_RAW_WET, SOIL_THRESHOLD_PCT);
#if EN_WATER
  Serial.printf("浇水保护: 最多 %d 轮 / 冷却 %lu 分钟\n", MAX_ROUNDS_PER_CYCLE, COOLDOWN_MS / 60000UL);
#endif
#if EN_LEVEL
  Serial.printf("水位判据: raw > %d 视为缺水（实测后改 LEVEL_DRY_RAW）\n", LEVEL_DRY_RAW);
#endif

  if (SOIL_RAW_DRY <= SOIL_RAW_WET) {           // v1.1 标定防呆：干点必须大于湿点，填反立刻报错
    Serial.println("!! [自检失败] SOIL_RAW_DRY <= SOIL_RAW_WET，标定值疑似填反，请检查后重烧 !!");
  }

  pinMode(PIN_LED_R, OUTPUT); digitalWrite(PIN_LED_R, LOW);
  pinMode(PIN_LED_G, OUTPUT); digitalWrite(PIN_LED_G, LOW);
  pinMode(PIN_RELAY, OUTPUT); relayOff();       // 上电继电器必须断开

#if EN_DHT
  dht.begin();
#endif
#if EN_OLED
  u8g2.begin();
  u8g2.enableUTF8Print();
#endif
#if EN_WIFI
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("[WiFi] 连接中");
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) { delay(500); Serial.print("."); }
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("\n[WiFi] 已连接 IP=%s\n", WiFi.localIP().toString().c_str());
  else
    Serial.println("\n[WiFi] 连接失败（确认用2.4GHz热点）——本地功能不受影响");
#endif
#if EN_MQTT
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
#endif
#if EN_WEB
  server.on("/", handleRoot);
  server.begin();
#endif
  readSensors();
  gSensorReady = true;                          // v1.1：首次读数完成，自动浇水/状态灯从此用真值判断
}

unsigned long tSensor = 0, tOled = 0, tPub = 0;

void loop() {
#if EN_WIFI
  if (WiFi.status() != WL_CONNECTED && millis() - lastWifiRetry >= WIFI_RETRY_MS) {  // v1.1：运行中掉线自动重连
    lastWifiRetry = millis();
    Serial.println("[WiFi] 掉线，尝试重连...");
    WiFi.disconnect();
    WiFi.reconnect();
  }
#endif
#if EN_MQTT
  if (WiFi.status() == WL_CONNECTED) { mqttConnect(); mqtt.loop(); }
#endif
#if EN_WEB
  server.handleClient();
#endif
  waterTick();
  updateStatusLed();

  unsigned long now = millis();
  if (now - tSensor >= SENSOR_INTERVAL_MS) { tSensor = now; readSensors(); printSensors(); }

#if EN_OLED
  if (now - tOled >= OLED_INTERVAL_MS) {
    tOled = now;
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_wqy12_t_gb2312a);   // 中文字体
    char line[28];
    snprintf(line, sizeof(line), "土壤: %d%%", gSoilPct);  u8g2.drawUTF8(0, 14, line);
    snprintf(line, sizeof(line), "光照: %d", gLightRaw);   u8g2.drawUTF8(0, 30, line);
#if EN_DHT
    if (!isnan(gTemp)) {
      snprintf(line, sizeof(line), "温度: %.1fC", gTemp);  u8g2.drawUTF8(0, 46, line);
      snprintf(line, sizeof(line), "气湿: %.0f%%", gHum);  u8g2.drawUTF8(0, 62, line);
    }
#endif
    u8g2.sendBuffer();
  }
#endif

#if EN_MQTT
  if (mqtt.connected() && now - tPub >= PUBLISH_INTERVAL_MS) { tPub = now; publishData(); }
#endif
}
