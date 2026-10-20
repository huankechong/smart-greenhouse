# -*- coding: utf-8 -*-
"""跳线穿模校验：每条线沿途密集采样，用奇偶射线法判断是否扎进实体。

判定口径（2026-10-20 收紧）：
- 采样步长 1.2mm（原每段固定 10 点，短段会漏掉薄壁穿刺）
- 采样区间 3%~97%（两端连接器插入不算穿模）
- 检测目标扩到全部实体件：结构件、水管、浮球组件、水箱盖、PCB
- 水体/浮子不计：泵线与水管本来就穿水，浮子是活动件

用法：python check_wires.py
输出：逐条报穿模点；全部干净则打印 PASS；有问题返回码 1。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_assembly as BA

TARGETS = ["花盆", "土壤", "水箱", "水箱盖", "面包板", "ESP32", "继电器",
           "OLED 45°支架", "OLED 屏", "DHT11 座", "底盘左片", "底盘右片",
           "水泵", "水泵固定座", "连接块", "水管末端夹", "水管",
           "浮球法兰", "浮球本体", "浮球杆", "土壤传感器板", "传感器盆沿挂钩"]

d = {}
for m, ck, nm in BA.items:
    d.setdefault(nm, []).append(m)


def sample(points, step=1.2):
    P, T = [], []
    for si, (a, b) in enumerate(zip(points[:-1], points[1:])):
        a, b = np.asarray(a, float), np.asarray(b, float)
        L = float(np.linalg.norm(b - a))
        n = max(4, int(np.ceil(L / step)))
        for t in np.linspace(0.03, 0.97, n):
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
            for h in sorted(set(hits))[:4]:
                print("  !! 线%02d 段%d 穿入 %s @%s" % (i, h[0] + 1, h[1], h[2]))
    print("\n跳线 %d 根，穿模 %d 根" % (len(BA.WIRES), bad))
    print("PASS" if bad == 0 else "（上方每一处都是真实相交，需改线）")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
