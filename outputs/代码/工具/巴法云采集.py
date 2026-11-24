# [2026-11-23 AR41 已修复] parse() 现已同时支持两种报文：
#   现行（11-23 起）：标签#值 严格交替  土壤#100#光照#1003#温度℃#26.5#气湿%#87#状态#待命#水位#正常#
#   历史（≤11-19）  ：字段#值|字段#值     土壤#72|光照#1109|…
# AR40 P-6 原本记录"整串被吞进 soil_pct"，起因是只按 '|' 切分而固件已改用 '#' 分隔。
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴法云 MQTT 主题数据采集器（R2 · 上云与数据）
================================================
为什么要有它：巴法云「数据存储」是收费项（40 元/5 主题/年）。本工具改用官方
取消息接口轮询（免费），把上行报文落成 CSV，48h 曲线与历史归档都用它出。

用法
----
    python3 巴法云采集.py --minutes 5            # 连续采 5 分钟（每 20s 一次）
    python3 巴法云采集.py --minutes 2880         # 48h 测试：采 48 小时
    python3 巴法云采集.py --once                 # 只取一次，看通不通

  UID 默认从仓库外的私档读，绝不写进代码：
    ~/Documents/花房私档/巴法云凭据.md 里的 `UID=` 行
  也可用环境变量覆盖：BEMFA_UID=xxxx python3 巴法云采集.py --once

输出
----
    outputs/素材/巴法云采集_<起始时间>.csv
    列：time, unix, soil_pct, lux_raw, temp_c, hum_pct, state, level, raw_msg
    （同一 unix 重复的不重复写，掉线缺口会留空行，便于图上看出断点）
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

API = "https://apis.bemfa.com/va/getmsg"
TOPIC_DATA = "cYQ9geudA004"   # 上行（传感器 004）
PRIVATE = os.path.expanduser("~/Documents/花房私档/巴法云凭据.md")
FIELDS = ["time", "unix", "soil_pct", "lux_raw", "temp_c", "hum_pct", "state", "level", "raw_msg"]


def load_uid() -> str:
    uid = os.environ.get("BEMFA_UID", "").strip()
    if uid:
        return uid
    if os.path.exists(PRIVATE):
        for line in open(PRIVATE, encoding="utf-8"):
            m = re.match(r"^UID=(.*)$", line.strip())
            if m and m.group(1).strip():
                return m.group(1).strip()
    sys.exit("找不到 UID：请填 ~/Documents/花房私档/巴法云凭据.md 的 UID= 行，或设 BEMFA_UID 环境变量")


def fetch(uid: str, topic: str) -> dict | None:
    url = f"{API}?uid={uid}&topic={topic}&num=1&type=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            j = json.loads(r.read().decode())
    except Exception as e:
        print(f"  [warn] 请求失败：{e}")
        return None
    if j.get("code") != 0 or not j.get("data"):
        print(f"  [warn] 接口返回：{j}")
        return None
    return j["data"][0]


def parse(msg: str) -> dict:
    """解析上行报文，返回各字段。

    现行格式（2026-11-23 起，固件 v1.9+）：
        土壤#100#光照#1003#温度℃#26.5#气湿%#87#状态#待命#水位#正常#
        → 按 '#' 切分后两两配对（标签, 值）
    历史格式（≤2026-11-19）：土壤#72|光照#1109|温度#21.9|…
        → 按 '|' 切分，每段再按 '#' 拆成 标签/值
    """
    out = {"soil_pct": "", "lux_raw": "", "temp_c": "", "hum_pct": "", "state": "", "level": ""}
    keymap = {"土壤": "soil_pct", "光照": "lux_raw",
              "温度": "temp_c", "温度℃": "temp_c",
              "气湿": "hum_pct", "气湿%": "hum_pct",
              "状态": "state", "水位": "level"}

    if "|" in msg:                                  # 历史格式
        pairs = [p.split("#", 1) for p in msg.split("|") if "#" in p]
    else:                                           # 现行格式：标签#值 交替
        seg = msg.split("#")
        pairs = list(zip(seg[0::2], seg[1::2]))

    for k, v in pairs:
        k = k.strip()
        if k in keymap:
            out[keymap[k]] = v.strip()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=5, help="采集时长（分钟）")
    ap.add_argument("--interval", type=float, default=20, help="轮询间隔（秒）")
    ap.add_argument("--once", action="store_true", help="只取一次")
    ap.add_argument("--topic", default=TOPIC_DATA)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    uid = load_uid()
    out = args.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "素材", f"巴法云采集_{datetime.now():%Y%m%d_%H%M}.csv")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    new_file = not os.path.exists(out)
    fh = open(out, "a", newline="", encoding="utf-8-sig")
    wr = csv.DictWriter(fh, fieldnames=FIELDS)
    if new_file:
        wr.writeheader()

    print(f"采集到 {out}\n主题 {args.topic}｜间隔 {args.interval}s｜时长 "
          f"{'单次' if args.once else f'{args.minutes} 分钟'}")

    last_unix, rows, t_end = None, 0, time.time() + args.minutes * 60
    while True:
        d = fetch(uid, args.topic)
        if d and d.get("unix") != last_unix:
            last_unix = d["unix"]
            row = {"time": d.get("time", ""), "unix": d.get("unix", ""),
                   "raw_msg": d.get("msg", "")}
            row.update(parse(d.get("msg", "")))
            wr.writerow(row)
            fh.flush()
            rows += 1
            print(f"  [{row['time']}] {row['raw_msg']}")
        if args.once or time.time() >= t_end:
            break
        time.sleep(args.interval)

    fh.close()
    print(f"完成：新增 {rows} 行 → {out}")


if __name__ == "__main__":
    main()
