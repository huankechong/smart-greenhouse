# 固件应急包 · 2026-10-25

> **用途**：10/26 实验室万一那台电脑没装 arduino-cli / 编译环境用不了，
> 用 **flash_download_tool**（Windows 图形化）也能直接刷 .bin，不用编译。

## 三个固件（按明天使用顺序）

| # | 目录 | 开关状态 | 什么时候用 |
|---|---|---|---|
| 1 | `1_传感器版_DHT_OLED/` | EN_DHT=1, EN_OLED=1, 其余 0（30%/400KB） | 第 4 件：点亮 DHT11 + OLED |
| 2 | `2_继电器泵测试版/` | 独立测试固件（串口指令 on/off/w N/auto） | 第 2、3 件：8.1 + 8.2 |
| 3 | `3_主固件_收尾烧回/` | 全 0（v1.6 主固件） | **收尾必烧回**（第 4 节） |

## 刷 bin 的方法（应急路径）

1. 电脑装 [flash_download_tool](https://www.espressif.com/en/support/download/other-tools)（Espressif 官方，免安装单文件）
2. ESP32 插 USB，工具选 chipType=ESP32、workMode=Develop
3. 选上表 .bin，**下载地址填 0x10000**
4. SPI Speed 40MHz / SPI Mode DIO，点 START

## 正常路径（优先用这个）

实验室电脑能装 arduino-cli 的话，按操作清单第二节的命令走源码烧录，**不用这个包**。
bin 只是保险。

## 注意

- bin 是 2026-10-25 编译的，若之后改了固件源码（如 `LEVEL_WET_CLOSED`），以源码重烧为准
- 板子上现在是「继电器泵测试版」（2026-10-25 22:55 烧入并实机验证）
