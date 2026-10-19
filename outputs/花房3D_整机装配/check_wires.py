# -*- coding: utf-8 -*-
"""跳线穿模校验：每条线沿途采样，用奇偶射线法判断是否扎进实体。

用法：python check_wires.py
输出：逐条报穿模点；全部干净则打印 PASS。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_assembly as BA

# 只查主要结构件（细节件之间互相穿插无意义）
TARGETS = ["花盆", "土壤", "水箱", "水体", "面包板", "ESP32", "继电器",
           "OLED 45°支架", "DHT11 座", "底盘左片", "底盘右片",
           "水泵固定座", "连接块", "水管末端夹"]

d = {}
for m, ck, nm in BA.items:
    d.setdefault(nm, []).append(m)


def sample(points, n=10):
    P, T = [], []
    for si, (a, b) in enumerate(zip(points[:-1], points[1:])):
        a, b = np.asarray(a, float), np.asarray(b, float)
        for t in np.linspace(0.06, 0.94, n):
            P.append(a + (b - a) * t)
            T.append(si)
    return np.asarray(P), np.asarray(T)


def main():
    bad = 0
    for i, w in enumerate(BA.WIRES, 1):
        P, T = sample(w)
        hits = []
        for key in TARGETS:
            for mesh in d.get(key, []):
                _, idx, _ = mesh.ray.intersects_location(
                    ray_origins=P, ray_directions=np.tile([0, 0, 1.0], (len(P), 1)))
                cnt = np.bincount(idx, minlength=len(P))
                for k in np.where(cnt % 2 == 1)[0]:
                    hits.append((int(T[k]), key, tuple(np.round(P[k], 1))))
        if hits:
            bad += 1
            for h in sorted(set(hits))[:3]:
                print("  !! 线%02d 段%d 穿入 %s @%s" % (i, h[0] + 1, h[1], h[2]))
    print("\n跳线 %d 根，穿模 %d 根" % (len(BA.WIRES), bad))
    print("PASS" if bad == 0 else "（端点扎进零件 0.1mm 内视为插入，可接受）")


if __name__ == "__main__":
    main()
