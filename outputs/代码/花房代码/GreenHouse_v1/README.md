# GreenHouse_v1 使用说明

> 智能花房养护站主程序 · **v1.9**（2026-11-19 起：本地 LittleFS CSV 记录、9 点中值滤波、Web 简易令牌）  
> 当前定稿形态：7 个功能开关全部启用；最近一次完整编译 **≈1.12 MB / 85% Flash**（±数百字节属编译正常漂移，报告写"≈1.12 MB"即可）  
> 验证环境：`esp32:esp32@3.3.12`（fqbn `esp32:esp32:esp32`）· Arduino CLI 1.5.2-rc.1

## 一、当前开关与参数（以源码为准）

`GreenHouse_v1.ino` 当前为 48h 实测后的定稿形态：

| 项 | 当前值 | 说明 |
|---|---:|---|
| `EN_DHT / EN_OLED` | 1 / 1 | 温湿度与 OLED 已实装 |
| `EN_WATER / EN_LEVEL` | 1 / 1 | 自动浇水与浮球水位保护已启用 |
| `EN_WIFI / EN_MQTT / EN_WEB` | 1 / 1 / 1 | 云上报、远程浇水、局域网页面已启用 |
| `SOIL_RAW_DRY / SOIL_RAW_WET` | 1855 / 857 | 真干土 / 完全浸没三轮实测定稿 |
| `SOIL_THRESHOLD_PCT` | 15 | 低于 15% 触发自动浇水（2026-11-22 演示定稿，原 3%） |
| `WATER_MS` | 2000 | 自动每轮 2 s，约 64 ml（32.1 ml/s 实测） |
| `SETTLE_MS` | 30000 | 每轮后等 30 s 复测 |
| `MANUAL_WATER_MS` | 2000 | 远程手动浇水 2 s，约 64 ml |
| `MAX_ROUNDS_PER_CYCLE` | 6 | 一个周期最多 6 轮（合计约 12 s / 384 ml） |
| `COOLDOWN_MS` | 600000 | 超上限后冷却 10 分钟 |
| `LEVEL_WET_CLOSED` | false | 没水时触点闭合；断线会判“有水”，属已知非 fail-safe 方向 |
| 采样 / 上报 / 本地记录 | 5 s / 10 s / 10 s | 上报与 CSV 记录相互独立 |

> 换传感器后必须重新标定，并在标定前把 `EN_WATER` 改回 0。标定非法时 setup 会硬停机，`safeMap()` 防止除零 panic。

## 二、外部依赖

| 库 | 锁定版本 | 用途 |
|---|---|---|
| DHT sensor library | 1.4.7 | DHT11 |
| Adafruit Unified Sensor | 1.1.15 | DHT 依赖 |
| U8g2 | 2.36.19 | OLED |
| PubSubClient | 2.8.0 | 巴法云 MQTT |

Arduino CLI 复现命令：

```bash
arduino-cli lib install "DHT sensor library@1.4.7" \
  "Adafruit Unified Sensor@1.1.15" "U8g2@2.36.19" "PubSubClient@2.8.0"
```

ESP32 core 固定 **3.3.12**（2026-11-22 升级，已实测通过）。core 3.x 有三个坑（U8g2 须显式传 SCL/SDA、I2C 只能 100 kHz、不要再装 2.0.x），详见项目根 `AGENTS.md` §4.0。

## 三、凭据与联网

- `config.h` 在仓库中必须保持 `<...>` 占位符（**四个值**：WIFI_SSID / WIFI_PASS / MQTT_UID / WEB_TOKEN）；真值只存本地忽略目录和 E 盘私档。
- 巴法云主题：上行 `cYQ9geudA004`（传感器 004）；下行 `4QT4BZIBM001`（插座 001）。
- MQTT：`bemfa.com:9501`，明文 TCP，clientID = UID；项目结束后建议重置 UID。
- 联调/烧录完成后，先把 `config.h` 恢复为占位符，再检查 `git status`。

## 四、局域网保底页

v1.9 起页面要求简易令牌：访问格式为 `http://<ESP32_IP>/?k=<WEB_TOKEN>`。令牌值在 `config.h`（2026-11-24 从 `.ino` 挪入），不写进公开文档；401 响应不回显令牌。

- 页面只读，无控制端点。
- 无令牌或令牌错误返回 401。
- 答辩现场用手机 2.4 GHz 热点；ESP32 不支持 5 GHz。

## 五、控制逻辑速览

```text
监视 → 土壤 < 15% → 浇 2 s → 停 30 s 复测
     → 仍低于阈值且未满 6 轮 → 再浇
     → 连续 6 轮仍低 → 冷却 10 分钟
远程 on → 手动浇 2 s → 自动回 off
水位低 → 拒绝启动；浇水/复测/手动中水位变低 → 立即停泵
```

状态灯：绿=正常；红常亮=缺水但未启动；红 300 ms 闪=浇水中；红 100 ms 快闪=冷却；红 1 s 慢闪=水位低。

## 六、本地 CSV 记录

v1.9 使用 LittleFS 保存 `/gh.csv`，每 10 s 一行，独立于 MQTT 与 Web 开关。

- 串口发 `dump`：导出全量 CSV（仅在停机后执行；约 600 KB 会阻塞数秒）。
- 串口发 `clearlog`：清空记录（操作前必须确认已导出）。
- 重启会写入 `#BOOT` 分隔行；`sec` 是相对秒数，绝对时间用起表人工记录换算。

## 七、上传与排障

- 报 `not responding / not in sync`：按住 **BOOT** 点上传，出现 `Connecting....` 后松开。
- 报 `Unable to verify flash chip connection`：上传波特率降到 115200。
- 编译缓存被强杀损坏：用 `--build-path` 指向全新目录。

## 八、审计依据

- AR01：`docs/审计报告/archive/AR01_GreenHouse代码审计修复报告_2026-10-17.md`
- AR10：`docs/审计报告/AR10_GreenHouse项目代码全面审计_2026-10-20.md`
- AR16/AR17：防除零、硬停机、编译守卫
- AR38：v1.9 本地记录与三轮固件审计
- AR39：48h 数据分析（27.8 h 窗口，土壤通道有效 13 h）

## 九、已知限制

1. MQTT 为明文 9501；局域网页面只做简易令牌，不是完整认证。
2. `LEVEL_WET_CLOSED=false` 的代价是浮球断线会被判为“有水”；如机械翻转浮球恢复“没水断开”，应改回 true。
3. 低成本土壤探头无温度补偿，高湿段非线性；百分比是相对指数，不是 VWC。
4. 光照通道暗态会 ADC 饱和，夜间曲线只能作“暗”定性使用。
