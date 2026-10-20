#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
soil_watch.py —— 土壤传感器接线检查 & 实时读数看板

做什么：
  1. 连上 ESP32 串口，实时显示 GPIO34 的 raw 读数
  2. 判定接线是否正确：
       - 读数几乎恒定在 0 附近（< 200）→ 传感器 OUT 没接 / 没上电 / 没共地
       - 读数恒定在满量程附近（> 4000）→ 传感器 5V 悬空 / GND 没接
       - 读数在几百到三千多之间 → 接线正确，可以做干湿标定
  3. 可选 --raw 模式：直接打印原始 CSV（供 soil_calibrate.py 使用）

用法：
  python soil_watch.py                 # 实时看板（默认）
  python soil_watch.py --port COM6     # 指定端口
  python soil_watch.py --seconds 30    # 跑 30 秒后自动退出
  python soil_watch.py --raw           # 只打印原始行，给标定脚本用
"""

import argparse
import sys
import time
from collections import deque

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("缺少 pyserial。先执行：")
    print(r'  C:\Users\junbo\.workbuddy\binaries\python\envs\default\Scripts\pip.exe install pyserial')
    sys.exit(1)

BAUD = 115200
WINDOW = 40          # 滑动窗口长度
HISTORY = 120        # 保留的历史条数


def pick_port(explicit=None):
    if explicit:
        return explicit
    ports = list(list_ports.comports())
    if not ports:
        print("✗ 没有可用串口。板子插了吗？数据线是数据线吗？")
        return None
    # CH340 / CP2102 优先
    for p in ports:
        if p.vid is not None and p.vid in (0x1A86, 0x10C4):
            return p.device
    return ports[0].device


def verdict(lo, hi, span):
    """根据读数区间给出接线判定。"""
    if hi < 200:
        return ("✗ 读数几乎为 0", "传感器 OUT 没接上，或模块没供电/没共地。先查 5V→3V3 和 GND→GND 两根线。")
    if lo > 4000:
        return ("✗ 读数顶到满量程", "OUT 悬空或短路了。查 5V→3V3 是否接反/漏接，GND 是否真的接到 ESP32 的 GND。")
    if span < 200:
        return ("△ 接线像是通了，但读数几乎不动", "插到干土/水里看数值有没有变化。若纹丝不动，多半是 OUT 没接到 GPIO34。")
    return ("✓ 接线正常", "读数在合理区间且有波动，可以开始干湿标定了。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None)
    ap.add_argument("--seconds", type=int, default=0, help="0 = 一直跑，Ctrl+C 退出")
    ap.add_argument("--raw", action="store_true", help="只输出原始行")
    args = ap.parse_args()

    port = pick_port(args.port)
    if not port:
        sys.exit(1)

    if not args.raw:
        print("=" * 62)
        print("  智能花房 · 土壤传感器接线检查 / 实时读数")
        print("=" * 62)
        print(f"  端口：{port}   波特率：{BAUD}")
        print("  接线：模块 5V→ESP32 3V3 | GND→GND | OUT→GPIO34")
        print("  Ctrl+C 退出")
        print("-" * 62)

    try:
        ser = serial.Serial(port, BAUD, timeout=1)
    except Exception as e:
        print(f"✗ 打开 {port} 失败：{e}")
        print("  提示：串口可能被 arduino-cli monitor 占着，关掉那个窗口再试。")
        sys.exit(1)

    buf = deque(maxlen=WINDOW)
    hist = deque(maxlen=HISTORY)
    t0 = time.time()
    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                if args.seconds and time.time() - t0 > args.seconds:
                    break
                continue
            if not line.startswith("RAW,"):
                if not args.raw:
                    print("  [非数据行]", line)
                continue
            if args.raw:
                print(line)
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            try:
                raw = int(parts[2])
            except ValueError:
                continue
            buf.append(raw)
            hist.append(raw)
            if len(buf) < 5:
                continue
            lo, hi = min(buf), max(buf)
            span = hi - lo
            # 用 6 位一组打印柱状图
            bar = "#" * max(1, min(40, raw // 100))
            print(f"  raw={raw:5d}  [{lo:5d}–{hi:5d}]  跨度={span:5d}  |{bar}")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

    if not args.raw and len(hist) >= 5:
        lo, hi = min(hist), max(hist)
        span = hi - lo
        title, tip = verdict(lo, hi, span)
        print("-" * 62)
        print(f"  统计：共 {len(hist)} 条   最小 {lo}   最大 {hi}   跨度 {span}")
        print(f"  {title}")
        print(f"  → {tip}")
        if 200 <= lo and hi <= 4000:
            print()
            print("  下一步：干湿两阶段标定（会自动回写主程序常量）")
            print(r'  "C:\Users\junbo\.workbuddy\binaries\python\envs\default\Scripts\python.exe" '
                  r'"outputs/花房代码/tools/soil_calibrate.py" --port ' + port + " --write")


if __name__ == "__main__":
    main()
