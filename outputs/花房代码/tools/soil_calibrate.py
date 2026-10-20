#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
soil_calibrate.py —— W1 土壤传感器标定助手（PC 端）

做什么：
  1. 扫描并连接 ESP32 的串口（CH340 → 通常 COM3/COM5…）
  2. 分两阶段采集 raw 读数：
       阶段 A「干」：探针完全离开土/水（拿在手里或插在干杯底）
       阶段 B「湿」：探针插进一杯水里（完全浸没到标记线以上）
  3. 剔除异常值后取中位数，算出 SOIL_RAW_DRY / SOIL_RAW_WET
  4. 可选 --write：直接把两个常量回写进主程序 GreenHouse_v1.ino
  5. 打印一份可粘贴进报告的「标定记录」

依赖：pyserial（已装在项目隔离 venv 里）
用法：
  python soil_calibrate.py                # 交互式，两阶段采集
  python soil_calibrate.py --port COM5    # 指定端口
  python soil_calibrate.py --write        # 采集后自动回写主程序
  python soil_calibrate.py --dry-seconds 3 --wet-seconds 3
  python soil_calibrate.py --list-ports   # 只列端口就退出
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("缺少 pyserial。先执行：")
    print(r'  C:\Users\junbo\.workbuddy\binaries\python\envs\default\Scripts\pip.exe install pyserial')
    sys.exit(1)

# 项目根：脚本在 outputs/花房代码/tools/ 下，往上三层是仓库根
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
MAIN_INO = PROJECT_ROOT / "outputs" / "花房代码" / "GreenHouse_v1" / "GreenHouse_v1.ino"

BAUD = 115200

# 剔除异常值的容差：中位数 ± 该比例之外的值丢弃（抑制偶发跳变）
OUTLIER_TOL = 0.08
# 干湿差下限：小于此值说明传感器没真正响应，或接线有问题（与主程序自检阈值 800 一致）
MIN_SPAN = 800


# ---------------------------------------------------------------
# 端口
# ---------------------------------------------------------------
def list_ports_info():
    ports = list(list_ports.comports())
    if not ports:
        return []
    out = []
    for p in ports:
        desc = f"{p.description} | VID={p.vid:04X} PID={p.pid:04X}" if p.vid is not None else p.description
        out.append((p.device, desc))
    return out


def pick_port(explicit=None):
    """挑一个最可能的 ESP32 串口。CH340/CP2102 优先。"""
    if explicit:
        return explicit
    ports = list(list_ports.comports())
    if not ports:
        return None
    # 优先 CH340(1A86) / CP2102(10C4) / 常见 ESP32 描述
    for p in ports:
        blob = f"{p.vid:04X} {p.pid:04X} {p.description}".upper() if p.vid is not None else p.description.upper()
        if "1A86" in blob or "CH340" in blob or "CH341" in blob or "10C4" in blob or "CP210" in blob:
            return p.device
    return ports[0].device


# ---------------------------------------------------------------
# 采样
# ---------------------------------------------------------------
class SoilReader:
    def __init__(self, port, verbose=True):
        self.port = port
        self.verbose = verbose
        self.ser = None

    def open(self):
        self.ser = serial.Serial(self.port, BAUD, timeout=1)
        time.sleep(2.0)  # 等 ESP32 reset + 首行 READY
        self.ser.reset_input_buffer()
        self.ser.write(b"P")
        self.ser.flush()
        time.sleep(0.5)
        return self

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    def _drain(self, seconds):
        """读 seconds 秒，返回所有 RAW 值。"""
        vals = []
        end = time.time() + seconds
        buf = b""
        while time.time() < end:
            chunk = self.ser.read(256)
            if chunk:
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    txt = line.decode("utf-8", errors="ignore").strip()
                    if txt.startswith("RAW,"):
                        parts = txt.split(",")
                        if len(parts) >= 3:
                            try:
                                vals.append(int(parts[2]))
                            except ValueError:
                                pass
        return vals

    def sample_stage(self, label, seconds):
        if self.verbose:
            print(f"  采集中…（{seconds}s，请保持当前状态）")
        vals = self._drain(seconds)
        if self.verbose and vals:
            print(f"  → 收到 {len(vals)} 个样本")
        return vals


def trim_outliers(vals, tol=OUTLIER_TOL):
    """中位数 ± tol*range 之外视为异常值丢弃。"""
    if not vals:
        return []
    med = statistics.median(vals)
    spread = max(vals) - min(vals)
    if spread == 0:
        return list(vals)
    lo = med - tol * spread
    hi = med + tol * spread
    kept = [v for v in vals if lo <= v <= hi]
    return kept or list(vals)


def stats(vals):
    if not vals:
        return None
    trimmed = trim_outliers(vals)
    return {
        "n": len(vals),
        "n_kept": len(trimmed),
        "min": min(trimmed),
        "max": max(trimmed),
        "median": int(statistics.median(trimmed)),
        "mean": round(statistics.fmean(trimmed), 1),
        "stdev": round(statistics.pstdev(trimmed), 1) if len(trimmed) > 1 else 0.0,
    }


# ---------------------------------------------------------------
# 回写主程序
# ---------------------------------------------------------------
def write_back(dry, wet, ino_path=MAIN_INO):
    """把标定值回写进主程序的两个常量。返回 (是否成功, 说明)。"""
    if not ino_path.exists():
        return False, f"找不到主程序：{ino_path}"
    text = ino_path.read_text(encoding="utf-8")
    orig = text
    import re

    new_text, n1 = re.subn(
        r"(const int SOIL_RAW_DRY\s*=\s*)\d+",
        lambda m: f"{m.group(1)}{dry}",
        text,
        count=1,
    )
    new_text, n2 = re.subn(
        r"(const int SOIL_RAW_WET\s*=\s*)\d+",
        lambda m: f"{m.group(1)}{wet}",
        new_text,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        return False, f"未能在主程序中唯一定位常量（DRY={n1} 处, WET={n2} 处），已放弃回写"
    if new_text == orig:
        return False, "写入内容与原文件完全相同，未做改动"
    ino_path.write_text(new_text, encoding="utf-8")
    return True, f"已回写 {ino_path.name}：SOIL_RAW_DRY={dry}, SOIL_RAW_WET={wet}"


# ---------------------------------------------------------------
# 报告
# ---------------------------------------------------------------
def print_report(dry_s, wet_s, dry_v, wet_v, span, verdict, note):
    line = "=" * 62
    print(line)
    print("  土壤传感器标定记录（W1-4.1 素材）")
    print(line)
    print(f"  引脚：GPIO34 (ADC1_CH6)   供电：3.3V   波特率：{BAUD}")
    print()
    print("  【干态】探针离开土/水")
    if dry_s:
        print(f"    样本 {dry_s['n']} 个（剔除后 {dry_s['n_kept']}）"
              f"  中位数 {dry_s['median']}  均值 {dry_s['mean']}"
              f"  范围 {dry_s['min']}~{dry_s['max']}  标准差 {dry_s['stdev']}")
    print()
    print("  【湿态】探针完全浸入水中")
    if wet_s:
        print(f"    样本 {wet_s['n']} 个（剔除后 {wet_s['n_kept']}）"
              f"  中位数 {wet_s['median']}  均值 {wet_s['mean']}"
              f"  范围 {wet_s['min']}~{wet_s['max']}  标准差 {wet_s['stdev']}")
    print()
    print(f"  → 干湿差 = {span}")
    print(f"  → 判定：{verdict}")
    if note:
        print(f"  → {note}")
    print()
    print("  填进主程序（GreenHouse_v1.ino 顶部）：")
    print(f"    const int SOIL_RAW_DRY = {dry_s['median'] if dry_s else '?'};")
    print(f"    const int SOIL_RAW_WET = {wet_s['median'] if wet_s else '?'};")
    print(line)


# ---------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="W1 土壤传感器标定助手")
    ap.add_argument("--port", help="串口，如 COM5（默认自动挑选）")
    ap.add_argument("--dry-seconds", type=int, default=3, help="干态采集秒数（默认 3）")
    ap.add_argument("--wet-seconds", type=int, default=3, help="湿态采集秒数（默认 3）")
    ap.add_argument("--write", action="store_true", help="采集后自动回写主程序常量")
    ap.add_argument("--list-ports", action="store_true", help="只列出可用串口")
    args = ap.parse_args()

    print("=" * 62)
    print("  智能花房 · W1 土壤传感器标定助手")
    print("=" * 62)
    print()

    ports = list_ports_info()
    print("  当前系统可用串口：")
    if ports:
        for dev, desc in ports:
            print(f"    {dev:<10} {desc}")
    else:
        print("    （无）—— 板子没插、数据线是充电线、或 CH340 驱动没装")
    print()

    if args.list_ports:
        return 0

    if not ports:
        print("  没有可用串口，无法标定。按上面提示排查后重试。")
        return 2

    port = pick_port(args.port)
    print(f"  使用端口：{port}")
    print()

    # ---- 连板 ----
    try:
        reader = SoilReader(port).open()
    except Exception as e:
        print(f"  打不开 {port}：{e}")
        print("  排查：① 换根数据线（必须支持数据传输）② 关掉 Arduino IDE 串口监视器")
        print("        ③ 设备管理器看有没有 CH340 黄色感叹号")
        return 3

    try:
        # ---- 阶段 A：干态 ----
        print("  【第 1 步 / 干态】")
        print("  把土壤探针完全离开土和水面（拿在手里，或插进干杯底）。")
        input("  准备好后按回车开始采集…")
        dry_vals = reader.sample_stage("干", args.dry_seconds)

        # ---- 阶段 B：湿态 ----
        print()
        print("  【第 2 步 / 湿态】")
        print("  把探针完全插进一杯水里（要没过探针上的标记线/到根部）。")
        input("  准备好后按回车开始采集…")
        wet_vals = reader.sample_stage("湿", args.wet_seconds)
    finally:
        reader.close()

    dry_s = stats(dry_vals)
    wet_s = stats(wet_vals)

    if not dry_s or not wet_s:
        print()
        print("  采集失败：没读到有效样本。")
        print("  排查：① 确认已烧录 W1_SoilCalib 固件（不是主程序！）")
        print("        ② 确认土壤 5V→3V3、GND→GND、OUT→GPIO34（丝印就是这三个字）")
        print("        ③ 看串口有没有 RAW,<millis>,<raw> 这种行")
        return 4

    dry = dry_s["median"]
    wet = wet_s["median"]
    span = dry - wet

    verdict = "正常"
    note = ""
    if dry <= wet:
        verdict = "异常：干点不高于湿点"
        note = "电容式传感器应是「干=高 raw、湿=低 raw」（湿土介电常数高→振荡频率低→输出电压低）。" \
               "请确认 OUT 没接反、没接 GPIO35；也可能型号不是电容式（电阻式是干低湿高），" \
               "那种情况主程序的 map 方向也要反过来，需改代码。"
    elif span < MIN_SPAN:
        verdict = f"异常：干湿差仅 {span}，小于 {MIN_SPAN}"
        note = "传感器没真正响应。查：① 探针根部（涂过防水漆的那段）有没有完全浸湿 " \
               "② 是不是插到了 GPIO35 或别的脚 ③ 模块是不是坏了。换一杯水、擦干后各测一次对比。"

    print_report(dry_s, wet_s, dry_vals, wet_vals, span, verdict, note)

    if args.write and dry > wet and span >= MIN_SPAN:
        ok, msg = write_back(dry, wet)
        print(f"  {msg}")
        print()
        print("  改完后必须重新编译再烧录，否则跑的还是旧标定值：")
        print(r'    outputs\.tools\arduino-cli\arduino-cli.exe compile --fqbn esp32:esp32:esp32 "outputs\花房代码\GreenHouse_v1"')
        print()
    elif args.write:
        print("  数据未通过自检，未回写主程序（避免把错误标定值写进去）。")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
