/*
 * ============================================================
 *  智能花房养护站 Smart GreenHouse — 主程序框架 v1
 *  《Introduction to Project Work》Final Project
 *  Liu Junbo · DT1班
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
 *  v1.5（2026-10-20 AR08 全面审计修复，详见 docs/审计报告/AR08）：
 *    ① [🔴高] 连浇上限计数 bug：状态2 复测后再浇时 waterRounds 未自增，恒为 1，
 *       MAX_ROUNDS_PER_CYCLE 上限永远触发不了 → 已修（再浇前 waterRounds++）
 *    ② [🟡中] 水位保护空窗：状态2 复测等待 30s / 状态3 手动浇水期间水位变低无人停泵
 *       → waterTick 顶部按 waterState∈{1,2,3} 统一断泵（v1.5.1 重构：原 relayIsOn()
 *       门控在状态2 是死代码——进入状态2 前继电器必已断，电平门恒假）
 *    ③ [🟡中] MQTT "ON"/"On" 大小写拒收 → 统一 toLowerCase 后比对
 *    ④ [🟢低] 标定防呆补两条：量程超 0..4095 报错、干湿差 <800 警告
 *  v1.4（2026-10-19 水位检测换浮球开关）：EN_LEVEL 从"读模拟量比阈值"改成
 *    "读干接点 + 消抖"。浮球开关是无源干接点（P52 / M10 / 常开 / 0~110V，
 *    43→52mm 修正：P43 报警点太高，1L 桶可用余量不足 650ml；P52 报警点 52mm，
 *    余量 700ml 够单轮浇灌上限），
 *    比电阻式雨滴板可靠：不电解、不受瓶壁影响、断线默认判"没水"（fail-safe）。
 *    删除 LEVEL_DRY_RAW；新增 LEVEL_WET_CLOSED 极性宏 + LEVEL_INTERVAL_MS 节流 +
 *    连续 3 次一致才认（水面波动会让干接点抖）。
 *  v1.3（2026-10-19 上电毛刺）：继电器"先锁电平再开输出"，避免低电平触发模块上电误吸合
 *  v1.2（2026-10-19 异常保护）：补两条"长期跑会出事"的缺口——
 *    ① 连浇上限：连续 MAX_ROUNDS_PER_CYCLE 轮仍判缺水 → 停水冷却 10 分钟并红灯快闪
 *       （防传感器脱土/线松导致每 33 秒一轮、无限浇下去）
 *    ② 低水位保护：EN_LEVEL=1 时读浮球开关（v1.4 改为干接点），水位低则拒绝启动、浇到一半也会停泵
 *       （防水箱空了泵空转干烧）
 *  两条都是"默认关闭"，接好传感器再开，不影响 W1/W2 的既有节奏。
 */

// ==================== 功能开关（按周开启） ====================
#define EN_DHT  0   // W1-D5：接好温湿度(41号)后改 1 → 需装 DHT sensor library
#define EN_OLED  0   // W1-D5：接好 OLED(25号)后改 1  → 需装 U8g2
#define EN_WATER  0   // W2-D8：接好继电器(16号)+水泵后改 1（注意：会真实出水！）
#define EN_WIFI  0   // W3-D11：上云时改 1 → 需装 PubSubClient
#define EN_MQTT  0   // 依赖 EN_WIFI=1：数据上报 + 远程浇水
#define EN_WEB  0   // 依赖 EN_WIFI=1：局域网保底网页（断外网手机也能看）
#define EN_LEVEL  0   // v1.4：接好浮球开关（第 10 件替换盖 + P52 浮球）后改 1 → 低水位停泵

// ==================== 引脚定义（对照《花房接线规划表.md》） ====================
#define PIN_SOIL    34   // 土壤湿度 AO → ADC1（只读脚，不能接输出设备）
#define PIN_LIGHT   35   // 光敏 AO    → ADC1（只读脚）
#define PIN_DHT     33   // 温湿度 DATA（41号）
#define PIN_RELAY   26   // 继电器 IN（16号）
#define PIN_LED_R   25   // 双色LED 红（13号，课堂双色LED实验件复用为状态灯）
#define PIN_LED_G   27   // 双色LED 绿（13号）
#define PIN_LEVEL   32   // v1.4 浮球开关干接点（第 10 件替换盖中心孔穿出）→ 数字输入，1kΩ 上拉到 3V3

// ==================== 标定/浇水参数（到货实测后改这里） ====================
// ⚠️ 下面两个值是按通用资料估的，**未在本模块实测**。它们只是让系统能编译运行。
// ⛔ 在用 soil_calibrate.py 实测并回写真实值之前，**EN_WATER 必须保持 0**。
//    原因：估偏了两种都坏——
//      估高了：湿态算成 ~90% → 永远不判缺水 → 花一直渴着（静默失效，很难发现）
//      估低了：干态算成 ~20% → 一直判缺水 → 反复浇水 → 水箱空、盆泡烂（危险）
//    标定脚本会把实测中位数自动回写到下面这两行（--write 参数）。
const int SOIL_RAW_DRY = 3200;        // 探针全干的 raw 读数 → W1-4.1 实测后自动回写
const int SOIL_RAW_WET = 1300;        // 探针全湿的 raw 读数 → W1-4.1 实测后自动回写
const int SOIL_THRESHOLD_PCT  = 35;   // 土壤湿度% 低于此值 → 判定缺水（标定后再按实际土壤调）
const unsigned long WATER_MS  = 3000;    // 每轮浇水 3 秒
const unsigned long SETTLE_MS = 30000;   // 浇完等 30 秒复测（防反复触发）
const unsigned long MANUAL_WATER_MS = 5000; // 远程手动浇水 5 秒
const int RELAY_ACTIVE_HIGH = 1;  // 继电器触发极性：吸合=高电平填1；实测相反就改0

// ---------- v1.2 异常保护参数 ----------
const int           MAX_ROUNDS_PER_CYCLE = 6;        // 一次处理最多连浇 6 轮（6×3s=18s 水）
const unsigned long COOLDOWN_MS  = 600000;           // 触发上限后冷却 10 分钟再恢复自动

// ---------- v1.4 水位检测（浮球开关，干接点） ----------
const bool          LEVEL_WET_CLOSED = true;         // [实测确认] true=有水时触点闭合（常开型）
                                                     //   万用表蜂鸣档：浮子推上端应"响"，拉下端"不响"
const unsigned long LEVEL_INTERVAL_MS = 100;         // 干接点采样周期（100ms 足够，远快于 3s 浇一轮）
const uint8_t       LEVEL_STABLE_N = 3;              // 连续 3 次一致才认（水面波动会抖，别只看 1 次）
const bool          LEVEL_USE_INTERNAL_PULLUP = false; // 外部 1kΩ 上拉时填 false（内部 45kΩ 太弱，
                                                       //   干簧管湿电流不够会在触点氧化后时通时断）

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
bool  gLevelReady = false;      // v1.4：首次稳定判定完成前，保护逻辑按"未知"处理（不启动浇水）
int   waterState = 0;          // 0=监视 1=浇水中 2=停水复测中 3=远程手动浇水中 4=冷却保护中
int   waterRounds = 0;         // v1.2：本处理周期已连浇轮数，恢复湿度或冷却结束时清零
unsigned long waterTimer = 0;
unsigned long manualMs = 0;     // 状态3手动浇水的时长
unsigned long lastLevelWarn = 0; // v1.2：低水位日志节流（10 秒一条，防串口刷屏）
unsigned long tLevel = 0;        // v1.4：干接点采样计时
bool          levelLast = false; // v1.4：上一次原始采样
uint8_t       levelSame = 0;     // v1.4：连续一致次数

// ---------- 继电器极性封装（低电平触发的模块只需改 RELAY_ACTIVE_HIGH） ----------
void relayOn()  { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? HIGH : LOW); }
void relayOff() { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? LOW  : HIGH); }
// AR08 备注：relayIsOn() 已并入水位保护按状态判定方案，保留给排障用（读回输出锁存电平）

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
#if EN_DHT
  gHum  = dht.readHumidity();
  gTemp = dht.readTemperature();
#endif
}

// ---------- v1.4 浮球开关读取：干接点 + 100ms 节流 + 连续 3 次一致消抖 ----------
// 为什么不用内部上拉：干簧管有"湿电流"门槛（小信号型号约 1~10mA），
// 内部 45kΩ 只有 0.07mA，触点氧化后会出现"时通时断"；外部 1kΩ 给到 3.3mA 才稳。
void levelTick() {
#if EN_LEVEL
  unsigned long now = millis();
  if (now - tLevel < LEVEL_INTERVAL_MS) return;
  tLevel = now;

  // 常开型(有水闭合)：有水→闭合→读到 LOW；没水/线断→断开→被 1kΩ 上拉到 HIGH
  bool rawLow = (digitalRead(PIN_LEVEL) == (LEVEL_WET_CLOSED ? HIGH : LOW));

  if (rawLow == levelLast) {
    if (levelSame < LEVEL_STABLE_N) levelSame++;
  } else {
    levelLast = rawLow;
    levelSame = 0;
  }
  if (levelSame >= LEVEL_STABLE_N - 1) {          // 连续 3 次一致才采信
    if (!gLevelReady) {
      gLevelReady = true;
      Serial.printf("[水位] 首次判定：%s（%s）\n",
                    rawLow ? "低" : "正常",
                    LEVEL_WET_CLOSED ? "常开型/有水闭合" : "常闭型/没水闭合");
    }
    if (gLevelLow != rawLow) {
      gLevelLow = rawLow;
      Serial.println(gLevelLow ? "[水位] 变为【低】→ 停泵保护" : "[水位] 恢复【正常】");
    }
  }
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

  // ---- 浇水相关状态（1/2/3）：水位过低 → 立即断泵并复位周期（AR08 修复：原 v1.2 只查
  //      状态1，状态2 复测等待 30s / 状态3 手动浇水期间水位跌到低点都无人管。
  //      按 waterState 判定而非读回继电器电平——状态2 进入前继电器必已断开，
  //      靠 relayIsOn() 门控会让状态2 分支成为死代码，复测期只能"脉冲一拍再停"）----
#if EN_LEVEL
  if (gLevelReady && gLevelLow && waterState >= 1 && waterState <= 3) {
    relayOff();                                   // 状态2 本已断，幂等再断一次无副作用
    Serial.println("[保护] 水位过低，停泵并中止本轮浇水周期");
    waterRounds = 0; waterState = 0; waterTimer = now;
    return;
  }
#endif

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
    if (!gLevelReady) return;                   // v1.4：水位还没判稳，先别开泵
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
          waterRounds++;                        // AR08 修复：进入下一轮前同步计数，
                                                // 否则 waterRounds 恒为 1，连浇上限永远够不到（v1.2 保护形同虚设）
          Serial.printf("[自动] 复测仍缺水，再浇第 %d/%d 轮\n", waterRounds, MAX_ROUNDS_PER_CYCLE);
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
  msg.toLowerCase();                            // AR08：巴法云部分客户端发 "ON"/"On"，统一小写再比
  Serial.printf("[MQTT] 收到 %s: %s\n", topic, msg.c_str());
  if (String(topic) == TOPIC_CMD && msg == "on") {   // 精确匹配 on，避免 "online" 等串误触发
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
  Serial.println("\n===== 智能花房养护站 v1.5 启动 =====");
  Serial.printf("功能开关: DHT=%d OLED=%d WATER=%d LEVEL=%d WIFI=%d MQTT=%d WEB=%d\n",
                EN_DHT, EN_OLED, EN_WATER, EN_LEVEL, EN_WIFI, EN_MQTT, EN_WEB);   // v1.1：排障先看烧的是哪套配置
  Serial.printf("标定: dry=%d wet=%d 缺水阈值=%d%%\n", SOIL_RAW_DRY, SOIL_RAW_WET, SOIL_THRESHOLD_PCT);
#if EN_WATER
  Serial.printf("浇水保护: 最多 %d 轮 / 冷却 %lu 分钟\n", MAX_ROUNDS_PER_CYCLE, COOLDOWN_MS / 60000UL);
#endif
#if EN_LEVEL
  pinMode(PIN_LEVEL, LEVEL_USE_INTERNAL_PULLUP ? INPUT_PULLUP : INPUT);
  Serial.printf("水位检测: 浮球开关 %s | 上拉=%s | 消抖 %d×%lu ms\n",
                LEVEL_WET_CLOSED ? "常开(有水闭合)" : "常闭(没水闭合)",
                LEVEL_USE_INTERNAL_PULLUP ? "内部45k(仅应急)" : "外部1k",
                (int)LEVEL_STABLE_N, LEVEL_INTERVAL_MS);
#endif

  if (SOIL_RAW_DRY <= SOIL_RAW_WET) {           // v1.1 标定防呆：干点必须大于湿点，填反立刻报错
    Serial.println("!! [自检失败] SOIL_RAW_DRY <= SOIL_RAW_WET，标定值疑似填反，请检查后重烧 !!");
  }
  if (SOIL_RAW_DRY > 4095 || SOIL_RAW_WET > 4095 || SOIL_RAW_DRY < 0 || SOIL_RAW_WET < 0) {  // AR08 防呆
    Serial.println("!! [自检失败] 标定值超出 ADC 0..4095 量程，12 位 ADC 读不到，请检查 !!");
  }
  if (SOIL_RAW_DRY - SOIL_RAW_WET < 800) {      // AR08 防呆：量程太窄映射会放大噪声
    Serial.println("!! [自检警告] 干湿标定差 <800，湿度%会对读数噪声过敏，建议重测标定 !!");
  }

  pinMode(PIN_LED_R, OUTPUT); digitalWrite(PIN_LED_R, LOW);
  pinMode(PIN_LED_G, OUTPUT); digitalWrite(PIN_LED_G, LOW);
  // v1.3：先把"断开"电平锁进输出寄存器，再打开输出驱动。
  // 低电平触发的继电器模块，若先 pinMode 再写电平，中间有几微秒是浮空/低电平 → 会"咔"一下吸合，
  // 表现就是"一上电水泵就转"。顺序反过来可以消掉这个毛刺。
  digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? LOW : HIGH);
  pinMode(PIN_RELAY, OUTPUT);
  relayOff();                                   // 上电继电器必须断开

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
  levelTick();                                   // v1.4：干接点采样 + 消抖
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
