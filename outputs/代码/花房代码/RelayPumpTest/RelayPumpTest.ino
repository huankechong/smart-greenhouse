/*
 * ============================================================
 *  RelayPumpTest —— 继电器 / 水泵 手动测试固件
 *  用途：2026-10-26 (D8) 实验室联调专用
 *  作者：小马 · 2026-10-25
 * ============================================================
 *  ⚠️ 为什么需要这个固件：
 *     主固件 v1.6 里【没有任何手动触发继电器的入口】——
 *       - Serial.read() 零处（没有串口指令）
 *       - manualWaterStart() 只被 MQTT 回调调用（要填 WiFi/UID 才能用）
 *     所以 8.1「GPIO 控制继电器吸合/断开」没法主动触发。
 *     更麻烦的是主固件在 EN_WATER=1 且土壤传感器悬空插空气时，
 *     会读到接近 DRY 的 raw → 判缺水 → 自己开始浇水，干扰观察。
 *
 *     本固件只做一件事：**用串口指令直接控制继电器**，不读任何传感器。
 *
 *  ============================================================
 *  串口指令（115200，末尾要按回车）
 * ============================================================
 *    h 或 help    显示帮助
 *    on           继电器吸合（泵转）
 *    off          继电器断开（泵停）
 *    w <秒>       吸合指定秒数后自动断开（测「浇 N 秒 = 出多少水」用）
 *                 例：w 10  → 吸合 10 秒
 *    auto         进入自动循环：吸合 3 秒 / 停 10 秒，反复
 *    stop         退出自动循环并断开继电器
 *
 *  ============================================================
 *  安全设计
 * ============================================================
 *   1. 上电第一件事：先锁"断开"电平再开输出（防上电毛刺，同主固件 v1.3/v1.6）
 *   2. 单次吸合硬上限 120 秒 —— 防止误输入 `w 999` 把水泵干烧
 *   3. 每条指令都回显动作 + 累计吸合时长，便于记录
 *   4. 不读任何传感器，不受土壤读数影响，绝不会"自己开始浇水"
 *
 *  ============================================================
 *  烧录
 * ============================================================
 *   arduino-cli upload -p COM6 --fqbn esp32:esp32:esp32 <本目录>
 *   （测完记得烧回主固件 GreenHouse_v1/）
 */

// ==================== 接线（与主固件一致） ====================
#define PIN_RELAY          26    // 继电器 IN（16 号模块）
#define RELAY_ACTIVE_HIGH  1     // 吸合=高电平填1；实测相反就改0
#define SERIAL_BAUD        115200

// ==================== 安全上限 ====================
#define MAX_ON_MS          120000UL   // 单次吸合硬上限 120 秒
#define AUTO_ON_MS         3000UL     // 自动模式：吸合 3 秒
#define AUTO_OFF_MS        10000UL    // 自动模式：停 10 秒

// ==================== 状态 ====================
unsigned long onStartMs   = 0;       // 本次吸合起始时刻
unsigned long totalOnMs   = 0;       // 累计吸合时长（跨多次）
bool          relayOnFlag = false;
bool          autoMode    = false;
unsigned long autoTimer   = 0;
bool          autoPhaseOn = false;

// ---------- 继电器封装（与主固件同极性逻辑） ----------
inline void relayOn()  { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? HIGH : LOW);  }
inline void relayOff() { digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? LOW  : HIGH); }

void help() {
  Serial.println(F("================ 指令表 ================"));
  Serial.println(F("  h / help   显示本帮助"));
  Serial.println(F("  on         继电器吸合（泵转）"));
  Serial.println(F("  off        继电器断开（泵停）"));
  Serial.println(F("  w <秒>     吸合 N 秒后自动断开（测出水量用）"));
  Serial.println(F("  auto       自动循环：吸合3秒/停10秒"));
  Serial.println(F("  stop       退出自动循环 + 断开"));
  Serial.println(F("  t          查看当前状态与累计吸合时长"));
  Serial.println(F("========================================"));
}

void printState() {
  unsigned long now = millis();
  unsigned long cur = relayOnFlag ? (now - onStartMs) : 0;
  Serial.printf("[状态] 继电器=%s | 本次已吸合 %.1f 秒 | 累计 %.1f 秒 | 自动=%s\n",
                relayOnFlag ? "吸合(泵转)" : "断开(泵停)",
                cur / 1000.0,
                (totalOnMs + cur) / 1000.0,
                autoMode ? "开" : "关");
}

void doOn(const char* why) {
  if (relayOnFlag) { Serial.println(F("[提示] 已经是吸合状态")); return; }
  onStartMs = millis();
  relayOnFlag = true;
  autoMode = false;                       // 手动优先，退出自动
  relayOn();
  Serial.printf("[动作] 继电器吸合 —— %s\n", why);
}

void doOff(const char* why) {
  if (!relayOnFlag) { Serial.println(F("[提示] 已经是断开状态")); return; }
  unsigned long d = millis() - onStartMs;
  totalOnMs += d;
  relayOnFlag = false;
  relayOff();
  Serial.printf("[动作] 继电器断开 —— %s（本次吸合 %.1f 秒）\n", why, d / 1000.0);
}

// htimed 到点自动断开
unsigned long timedOffAt = 0;   // 0 = 无定时

void handleCmd(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  String low = cmd;
  low.toLowerCase();

  if (low == "h" || low == "help") { help(); return; }
  if (low == "on")  { doOn("手动 on"); return; }
  if (low == "off") { doOff("手动 off"); timedOffAt = 0; return; }
  if (low == "t")   { printState(); return; }

  if (low == "stop") {
    autoMode = false;
    timedOffAt = 0;
    doOff("stop 指令");
    Serial.println(F("[动作] 已退出自动模式"));
    return;
  }

  if (low == "auto") {
    autoMode = true;
    autoTimer = millis();
    timedOffAt = 0;
    Serial.println(F("[动作] 进入自动循环：吸合3秒 / 停10秒（stop 退出）"));
    // 进入时立即吸合一次 —— 否则要干等 10 秒才动，现场会误判成"没反应"
    doOn("自动循环（首次）");
    autoMode = true;                  // doOn 会清 autoMode，这里补回
    return;
  }

  if (low.startsWith("w ")) {
    long sec = cmd.substring(2).toInt();
    if (sec <= 0) { Serial.println(F("[错误] 秒数要大于 0，例：w 10")); return; }
    unsigned long ms = (unsigned long)sec * 1000UL;
    if (ms > MAX_ON_MS) {
      Serial.printf("[保护] %ld 秒超过上限 %lu 秒，已按上限执行\n", sec, MAX_ON_MS / 1000UL);
      ms = MAX_ON_MS;
    }
    doOn("定时浇水");
    timedOffAt = millis() + ms;
    Serial.printf("[定时] 将在 %.1f 秒后自动断开 —— 请用秒表/量杯同步记录出水量\n", ms / 1000.0);
    return;
  }

  Serial.printf("[错误] 不认识的指令：%s（输入 h 看帮助）\n", cmd.c_str());
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  // ⚠️ 第一件事：先锁"断开"电平，再开输出（防上电毛刺，同主固件 v1.6）
  digitalWrite(PIN_RELAY, RELAY_ACTIVE_HIGH ? LOW : HIGH);
  pinMode(PIN_RELAY, OUTPUT);
  relayOff();

  delay(300);
  Serial.println();
  Serial.println(F("===== RelayPumpTest 继电器/水泵测试固件 ====="));
  Serial.printf("引脚 GPIO%d | 触发极性=%s\n",
                PIN_RELAY, RELAY_ACTIVE_HIGH ? "高电平吸合" : "低电平吸合");
  Serial.printf("单次吸合硬上限 %lu 秒\n", MAX_ON_MS / 1000UL);
  Serial.println(F("上电状态：继电器已断开"));
  help();
}

void loop() {
  // ---- 串口指令 ----
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCmd(cmd);
  }

  unsigned long now = millis();

  // ---- 定时断开（w N 指令）----
  if (timedOffAt && relayOnFlag && now >= timedOffAt) {
    timedOffAt = 0;
    doOff("定时到点");
    Serial.println(F("[提示] 已停止。记录一下：本次出水量 = ? ml"));
  }

  // ---- 硬上限保护 ----
  if (relayOnFlag && (now - onStartMs) > MAX_ON_MS) {
    doOff("超过硬上限，强制断开");
    Serial.println(F("[保护] 单次吸合超过上限，已强制断开"));
  }

  // ---- 自动循环 ----
  if (autoMode && !relayOnFlag && now - autoTimer >= AUTO_OFF_MS) {
    autoTimer = now;
    doOn("自动循环");
    autoMode = true;            // doOn 会关掉 autoMode，这里补回
  } else if (autoMode && relayOnFlag && now - onStartMs >= AUTO_ON_MS) {
    doOff("自动循环");
    autoMode = true;
    autoTimer = now;
  }

  // ---- 每 5 秒打一次状态（便于长时间观察）----
  static unsigned long lastBeat = 0;
  if (now - lastBeat >= 5000) {
    lastBeat = now;
    printState();
  }
}
