# GreenHouse_v1 使用说明

> 智能花房养护站主程序 · v1.1（审计修复版）· 已编译验证通过 · 2026-10-17
> 验证环境：esp32:esp32@2.0.17（ESP32 Dev Module）· Arduino CLI 1.5.1
> v1.1 修复明细见上级目录《AR01_GreenHouse代码审计修复报告_2026-10-17.md》

## 编译验证结果

| 配置 | Flash 占用 | RAM 占用 | 结果 |
|---|---|---|---|
| 全关（W1 出厂状态，只需 3V3/GND/模拟读取） | 269 KB (20%) | 21 KB (6%) | ✅ PASS |
| 全开（DHT+OLED+水泵+WiFi+MQTT+网页，W3 最终形态） | 900 KB (68%) | 47 KB (14%) | ✅ PASS |

两种形态都在 1.31MB Flash 上限内，余量充足。

## 三个外部库已装好（宿舍电脑）

- DHT sensor library（含 Adafruit Unified Sensor 依赖）
- U8g2 2.36.19（OLED 中文字体）
- PubSubClient 2.8.0（MQTT）

**到实验室电脑时**：库管理器搜同名安装即可，代码不用改。

## 使用节奏（对照 30 天计划）

| 周 | 操作 |
|---|---|
| W1 到货 | 全开关保持 0，直接烧录 → 串口 115200 看土壤/光照 raw 读数 → 实测后改 `SOIL_RAW_DRY / SOIL_RAW_WET` 两个标定值 |
| W1-D5 | 接好 DHT11(41号) 和 OLED(25号) → `EN_DHT=1`、`EN_OLED=1` → 编译烧录 |
| W2 | 接好继电器(16号)+水泵 → `EN_WATER=1`（**先空载试，蓄水瓶不接水路**）；继电器若低电平触发，把 `RELAY_ACTIVE_HIGH` 改 0 |
| W3 | `EN_WIFI=1` + 填 WiFi 名密码（手机 2.4G 热点）→ `EN_MQTT=1` + 填巴法云 UID → `EN_WEB=1` |

## 上传排障

报 `not responding / not in sync`：按住板上 **BOOT** 键点上传，出现 `Connecting....` 后松开。

## 巴法云主题（已创建，代码里已填死）

- 数据上行（004 传感器型）：`cYQ9geudA004`
- 指令下行（001 插座型，on=浇5秒）：`4QT4BZIBM001`
- **v1.1 起 UID 和 WiFi 密码不再写在主程序里**，统一填在 `config.h`（W3 上云前填好；交报告/发同学前把 config.h 改回 `<...>` 占位符）
