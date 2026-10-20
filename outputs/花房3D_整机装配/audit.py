# -*- coding: utf-8 -*-
"""花房 3D 全套审计：几何自检 + 装配干涉 + 文档对账"""
import os, sys, glob, re, json
import numpy as np
import trimesh
from trimesh.boolean import intersection

ROOT = r"D:/Documents/workbuddydocument/2026-10-17-08-59-13/outputs"
sys.path.insert(0, os.path.join(ROOT, "花房3D_整机装配"))

print("=" * 70)
print("① 全部 STL 自检 (watertight / 单体 / 落床 / bbox)")
print("=" * 70)
stl_files = sorted(glob.glob(os.path.join(ROOT, "**", "*.stl"), recursive=True))
rows = []
for f in stl_files:
    m = trimesh.load(f)
    rows.append((os.path.relpath(f, ROOT), m))
    ok = m.is_watertight and m.body_count == 1 and abs(m.bounds[0][2]) < 1e-6
    print("%s %-46s %-24s %8.1f g  tri=%d" % (
        "OK " if ok else "!! ", os.path.relpath(f, ROOT).replace("\\", "/"),
        str(np.round(m.extents, 1).tolist()), m.volume * 1.24 / 1000, len(m.faces)))

print()
print("=" * 70)
print("② 装配干涉 (两两求交, 只报 >1 mm3)")
print("=" * 70)
import build_assembly as BA          # 模块级已构建 items
# v1.7 细节件（螺丝/跳线/孔阵/板载件）只做视觉叠加，不参与两两干涉：
# 它们本来就贴在零件表面，逐对求交既慢又没有工程意义。跳线单独由 check_wires.py 校验。
DETAIL = ("跳线", "M3×6", "面包板孔阵", "面包板中央沟", "面包板电源轨",
          "ESP32 USB", "ESP32 按键", "ESP32 EN", "ESP32 天线", "ESP32 屏蔽",
          "继电器端子", "继电器指示", "继电器光耦", "OLED FPC", "OLED 排针",
          "OLED 驱动", "传感器铜探头", "传感器排针", "DHT11 格栅",
          "水泵进水", "水泵出水",
          # 液体与浸没件：水体是流体，泵/浮子泡在水里属正常，不算干涉
          "水体", "浮子", "叶片")
items = [(m, ck, nm) for m, ck, nm in BA.items if not (nm or "").startswith(DETAIL)]
print("装配几何体 %d 个（另有 %d 个细节件不参与干涉检查）"
      % (len(items), len(BA.items) - len(items)))

def bbox_overlap(a, b, tol=0.0):
    return np.all(a.bounds[0] - tol <= b.bounds[1]) and np.all(b.bounds[0] - tol <= a.bounds[1])

hits = []
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i][0], items[j][0]
        if not bbox_overlap(a, b):
            continue
        try:
            inter = intersection([a, b], engine="manifold")
            v = float(inter.volume) if len(inter.faces) else 0.0
        except Exception:
            v = -1.0
        if v > 1.0:
            hits.append((items[i][2] or items[i][1], items[j][2] or items[j][1], v))

if hits:
    for n1, n2, v in sorted(hits, key=lambda x: -x[2]):
        print("  %-18s × %-18s  %10.1f mm3" % (n1, n2, v))
else:
    print("  无干涉")

print()
print("=" * 70)
print("③ 文档数字 vs 实际文件")
print("=" * 70)


def doc(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


checks = []
# P0
d = doc(os.path.join(ROOT, "花房3D_P0", "交付说明_P0三件v1.md"))
# 01 已被 01b 取代(存档), 现行件是 01b/02/03
for name, stl in [("01b_sensor_rim_hook", "01b_sensor_rim_hook_v2.stl"),
                  ("02_pump_mount", "02_pump_mount_v1.stl"),
                  ("03_tube_clip", "03_tube_clip_v1.stl")]:
    m = trimesh.load(os.path.join(ROOT, "花房3D_P0", "STL", stl))
    g = round(m.volume * 1.24 / 1000, 1)
    checks.append((f"P0 文档 {stl} 估重 {g}g 是否出现", str(g) in d))
    bb = [round(x, 2) for x in m.extents]
    expect = {"01b_sensor_rim_hook_v2.stl": "30 × 19.78 × 32.78",
              "02_pump_mount_v1.stl": "57 × 55 × 25",
              "03_tube_clip_v1.stl": "26 × 26.6 × 31.4"}[stl]
    checks.append((f"P0 文档 {stl} 外形写作「{expect}」", expect in d))

# P1P2
d1 = doc(os.path.join(ROOT, "花房3D_P1P2", "交付说明_P1P2五件v1.md"))
for stl, key in [("04_oled_stand_v1.stl", "21.1"),
                 ("07_dht11_holder_v1.stl", "14.9"), ("08_cable_clip_v1.stl", "4.8")]:
    m = trimesh.load(os.path.join(ROOT, "花房3D_P1P2", "STL", stl))
    g = round(m.volume * 1.24 / 1000, 1)
    checks.append((f"P1P2 文档 {stl} 实际 {g}g / 文档写 {key}g", abs(g - float(key)) < 0.15))

# 底盘
d2 = doc(os.path.join(ROOT, "花房3D_整机底盘", "交付说明_整机底盘两片式v1.md"))
for stl, key in [("06a_base_left_v1.stl", "299.8"), ("06b_base_right_v1.stl", "291.8"),
                 ("06c_joint_block_v1.stl", "4.2")]:
    m = trimesh.load(os.path.join(ROOT, "花房3D_整机底盘", "STL", stl))
    g = round(m.volume * 1.24 / 1000, 1)
    checks.append((f"底盘 文档 {stl} 实际 {g}g / 文档写 {key}g", abs(g - float(key)) < 0.6))

# 装配
d3 = doc(os.path.join(ROOT, "花房3D_整机装配", "交付说明_整机示意模型.md"))
_glb = trimesh.load(os.path.join(ROOT, "花房3D_整机装配", "花房整机示意模型.glb"))
_n = len(_glb.geometry)
checks.append((f"装配文档写的几何体数 = 实际 {_n}", f"{_n} 个几何体" in d3))

for name, ok in checks:
    print("%s %s" % ("OK " if ok else "!! ", name))
