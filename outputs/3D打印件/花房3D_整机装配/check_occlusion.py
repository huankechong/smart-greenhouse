# -*- coding: utf-8 -*-
"""
OLED 屏幕遮挡量化 + 位置搜索
采样点朝观察方向打射线, 被别的件挡住即算遮挡。合格线: 4 个方向都 0%。
同时查干涉, 避免"不挡了但撞上别的件"。
"""
import os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_assembly as BA

CAMS = [(90, 30), (60, 30), (42, 26), (90, 45)]
TUBE_PTS = [(85, 8, 38), (85, 8, 58), (58, 8, 70), (15, 10, 70), (-25, 30, 55),
            (-52, 42, 80), (-46, 56, 112), (-65.5, 58.4, 112), (-65.5, 58.4, 96),
            (-74, 51, 87), (-78, 50, 80)]

parts = [(m, nm or ck) for m, ck, nm in BA.items]
others = trimesh.util.concatenate(
    [m for m, nm in parts if nm not in ("OLED 45°支架", "OLED 屏")])
print("合并检测网格: %d 面" % len(others.faces))

stand_proto = [m for m, nm in parts if nm == "OLED 45°支架"][0]
solid_parts = [(m, nm) for m, nm in parts if nm not in ("OLED 45°支架", "OLED 屏")]
solid_bbox = [(np.array(m.bounds[0]), np.array(m.bounds[1]), m, nm) for m, nm in solid_parts]


def cam_pos(az, el, dist=2000.0):
    a, e = np.deg2rad(az), np.deg2rad(el)
    return np.array([dist * np.cos(e) * np.cos(a),
                     dist * np.cos(e) * np.sin(a),
                     dist * np.sin(e) + 60.0])


def screen_pts(pos, k=6):
    ox, oy = pos
    cy, cz = oy + 0.11, 6.0 + 14.75
    n = np.array([0.0, np.sin(np.deg2rad(45)), np.cos(np.deg2rad(45))])
    u = np.array([1.0, 0.0, 0.0])
    v = np.array([0.0, -np.cos(np.deg2rad(45)), np.sin(np.deg2rad(45))])
    return np.array([np.array([ox, cy, cz]) + u * (i * 13.0) + v * (j * 13.0) + n * 0.9
                     for i in np.linspace(-1, 1, k) for j in np.linspace(-1, 1, k)])


def occl(pos, cam):
    pts = screen_pts(pos)
    c = cam_pos(*cam)
    d = c[None, :] - pts
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return float(others.ray.intersects_any(pts + d * 0.6, d).mean())


def inter_vol(pos):
    t = stand_proto.copy()
    t.apply_translation([pos[0], pos[1], 0.0])
    lo, hi = t.bounds
    tot = 0.0
    for b0, b1, m, nm in solid_bbox:
        if np.any(b0 > hi) or np.any(b1 < lo):
            continue
        it = trimesh.boolean.intersection([t, m], engine="manifold")
        if len(it.faces):
            tot += float(it.volume)
    return tot


print("\n【现在的屏幕 (-45,38) 被谁挡】")
pts0 = screen_pts((-45.0, 38.0))
for cam in CAMS:
    c = cam_pos(*cam)
    d = c[None, :] - pts0
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    blame = {}
    for m, nm in solid_parts:
        hit = m.ray.intersects_any(pts0 + d * 0.6, d)
        if hit.any():
            blame[nm] = int(hit.sum())
    print("  方位%3d° 仰角%2d° → 遮挡 %2d/36  %s" % (
        cam[0], cam[1], sum(blame.values()),
        "、".join("%s %d点" % (k, v) for k, v in sorted(blame.items(), key=lambda x: -x[1])) or "无"))

print("\n【搜索: 4 个方向全 0% 遮挡 + 零干涉】")
cands = []
for x in range(-155, -19, 5):
    for y in range(-105, 106, 5):
        pos = (float(x), float(y))
        if any(occl(pos, cam) > 0 for cam in CAMS):
            continue
        ov = inter_vol(pos)
        if ov > 1.0:
            continue
        cands.append((np.hypot(x + 100, y + 50), pos, ov))

cands.sort()
print("合格位置 %d 个（按离面包板引线出口 (-100,-50) 由近到远）：" % len(cands))
for d, pos, ov in cands[:10]:
    print("   (%7.1f, %7.1f)  距 ESP32 %5.1f mm" % (pos[0], pos[1], d))
if cands:
    print("\n推荐位置: (%g, %g)" % cands[0][1])
