/*
 * ============================================================
 *  W1 土壤传感器标定专用固件  SoilCalib
 *  《Introduction to Project Work》Final Project · 智能花房
 *  Liu Junbo · DT1班
 *
 *  用途：W1-D4.1 一次性任务 —— 实测土壤传感器干/湿两点 raw 读数，
 *        算出该填进主程序的 SOIL_RAW_DRY / SOIL_RAW_WET。
 *
 *  为什么单独写一个固件，而不是用主程序读：
 *    主程序 v1.5.1 已经能打 raw，但它是 5 秒一次、串口格式混杂，
 *    标定时要"连续采样 + 剔除异常值 + 算中位数"，靠肉眼看串口不可靠。
 *    这个固件：开机即连续输出 CSV 格式原始读数，配套 PC 端脚本
 *    soil_calibrate.py 做统计，直接把标定值写回主程序。
 *
 *  接线（只有土壤传感器，其余全部不接）：
 *    土壤 VCC  → ESP32  3V3    ← 必须 3.3V，接 5V 会超 ADC 量程
 *    土壤 GND  → ESP32  GND
 *    土壤 AOUT → ESP32  GPIO34  ← ADC1_CH6，只能接模拟输出
 *
 *  串口：115200 波特，输出格式（每行一条，CSV）：
 *    RAW,<millis>,<raw值>
 *  脚本解析此格式；人眼直接看也没问题。
 *
 *  编译：
 *    arduino-cli compile --fqbn esp32:esp32:esp32 W1_SoilCalib
 *  烧录：
 *    arduino-cli upload -p COMx --fqbn esp32:esp32:esp32 W1_SoilCalib
 * ============================================================
 */

#define PIN_SOIL 34          // 土壤湿度 AOUT → GPIO34 (ADC1_CH6)

// ---- 采样参数 ----
#define SAMPLE_INTERVAL_MS 100   // 每 100ms 输出一行（10Hz，脚本取 3 秒窗口≈30 个样本）
#define READ_AVG_N        10     // 单次读数取 10 次平均，抑制 ADC 噪声（与主程序 readAverage 一致）
#define READ_DELAY_MS     5

// ---- 串口命令（脚本下发，单字符）----
#define CMD_NONE  0
#define CMD_RESET 1   // 'R' 清空累积样本
#define CMD_MARK  2   // 'M' 打一个"阶段标记"（脚本用它分隔干/湿两个阶段）
#define CMD_PING  3   // 'P' 回一个 PONG（脚本用来确认端口活着）

unsigned long lastSample = 0;
unsigned long sampleCount = 0;

void setup() {
  Serial.begin(115200);
  delay(1500);          // 等 CH340 枚举稳定 + IDE/脚本别抢串口
  Serial.println();
  Serial.println("#SOILCALIB,1");
  Serial.println("#READY,soil_pin=34,interval_ms=100,avg_n=10");
  Serial.println("#CMD,R=reset,M=mark,P=ping");
}

void loop() {
  // ---- 处理串口命令 ----
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == 'R' || c == 'r') {
      Serial.println("#RESET");
    } else if (c == 'M' || c == 'm') {
      Serial.printf("#MARK,%lu\n", millis());
    } else if (c == 'P' || c == 'p') {
      Serial.println("PONG");
    }
  }

  // ---- 定时采样输出 ----
  unsigned long now = millis();
  if (now - lastSample < SAMPLE_INTERVAL_MS) return;
  lastSample = now;

  long sum = 0;
  for (int i = 0; i < READ_AVG_N; i++) {
    sum += analogRead(PIN_SOIL);
    delay(READ_DELAY_MS);
  }
  int raw = (int)(sum / READ_AVG_N);

  // 格式：RAW,<millis>,<raw>
  Serial.printf("RAW,%lu,%d\n", now, raw);
  sampleCount++;
}
