# -*- coding: utf-8 -*-
"""check_clearance.py — 逐件量「零件 vs 底盘槽」的实际配合（2026-11-10）

做法（不改模型，只量）：
  1. 从零件 STL 取「落座截面」——把零件平移到它落座的高度，取 z_min+0.15 的截面，得长/宽；
  2. 从底盘 STL 沿 ±X / ±Y 打射线，量槽在该高度的实际开口；
  3. 单边间隙 = (槽 − 件) / 2；同时量槽底高度，与零件 z_min 比对（差值=悬空/干涉）。

用法：  python check_clearance.py
"""
import os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # .../outputs/3D打印件
BASE_A = os.path.join(ROOT, "花房3D_整机底盘", "STL", "06a_base_left_v1.stl")
BASE_B = os.path.join(ROOT, "花房3D_整机底盘", "STL", "06b_base_right_v1.stl")

PARTS = {
    # (零件, 底盘, 槽心 cx, 槽心 cy, 落座高度)
    # ⚠ cx / cy 是从 花房3D_整机底盘/base_2pc_models.py 的 PARAMS["fits"] / ["fits_taper"] 手抄的。
    #   2026-11-24 修正：三行坐标停在 AR36（2026-11-12）布局重排之前——04 的 y 差 46、07 落在继电器槽上、
    #   11 差 (10,5)——导致射线在错误位置打、3/3 误报「!! 检查」。下方 _assert_coords_in_sync() 会核对，
    #   不一致直接报错，别绕过它去改 assert。
    "04 屏架":  ("花房3D_P1P2/STL/04_oled_stand_v1.stl", BASE_A,  -45.0,  83.8,  5.0),
    "07 DHT":   ("花房3D_P1P2/STL/07_dht11_holder_v1.stl", BASE_A, -40.0,   0.0,  3.5),
    "11 光敏":  ("花房3D_P1P2/STL/11_ldr_stand_v1.stl",  BASE_A, -120.0,   0.0,  4.0),
    # "08 扎线" 已于 2026-11-19 废弃删除（扎线改扎带），不再参与配合校验
}


def _assert_coords_in_sync():
    """PARTS 里的槽心必须与建模参数表一致——布局一改而这里没跟，量出来的就是别处的槽（2026-11-24 踩过）。"""
    import importlib.util, sys
    src = os.path.join(ROOT, "花房3D_整机底盘", "base_2pc_models.py")
    spec = importlib.util.spec_from_file_location("base_2pc_models", src)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(src))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    truth = {}
    for row in mod.P.get("fits", []) + mod.P.get("fits_taper", []):   # 注意：此模块参数表叫 P，非 PARAMS
        truth[row[0]] = (float(row[1]), float(row[2]))
    bad = []
    for name, (_p, _b, cx, cy, _seat) in PARTS.items():
        if name not in truth:
            bad.append(f"{name}: 建模表里已无此槽（是否已废弃？从 PARTS 删掉）")
        elif abs(truth[name][0] - cx) > 0.05 or abs(truth[name][1] - cy) > 0.05:
            bad.append(f"{name}: PARTS 写 ({cx}, {cy})，建模表是 {truth[name]}")
    if bad:
        raise SystemExit("check_clearance: PARTS 坐标与建模表不一致，结果不可信：\n  - " + "\n  - ".join(bad))


_assert_coords_in_sync()

_cache = {}


def load(path):
    if path not in _cache:
        _cache[path] = trimesh.load(path)
    return _cache[path]


def part_xy(path, seat_z):
    """零件自身 z_min 上方 0.15mm 的截面（=落座时的实际外廓）"""
    m = load(path)
    z = float(m.bounds[0][2]) + 0.15
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    v = sec.vertices
    return v[:, 0].max() - v[:, 0].min(), v[:, 1].max() - v[:, 1].min()


def _solid(m, x, y, z, s=0.12):
    bb = trimesh.creation.box(extents=[s, s, s])
    bb.apply_translation([x, y, z])
    try:
        v = m.intersection(bb, engine="manifold").volume
    except Exception:
        v = m.intersection(bb).volume
    return v / s ** 3 > 0.5


def pocket_halfwidth(base_path, cx, cy, z, axis, step=0.02, limit=30.0):
    """从槽心沿 +axis 扫，碰到实体即停 → 返回半宽"""
    m = load(base_path)
    r = 0.0
    while r < limit:
        r += step
        x = cx + (r if axis == "x" else 0)
        y = cy + (r if axis == "y" else 0)
        if _solid(m, x, y, z):
            return r - step
    return 0.0


def pocket_floor(base_path, cx, cy, ztop=7.9):
    """从顶面往下找第一个实体 → 槽底高度"""
    m = load(base_path)
    z = ztop
    while z > 0.2:
        o = np.array([cx, cy, z])
        loc, _, _ = m.ray.intersects_location([o + np.array([0, 0, 0.01])], [np.array([0, 0, -1.0])],
                                              multiple_hits=False)
        if len(loc) and np.linalg.norm(loc[0] - (o + np.array([0, 0, 0.01]))) < 0.02:
            break
        z -= 0.05
    return z


print("%-9s %-18s %-18s %-12s %-10s %s" % ("件", "槽开口(X×Y)", "件底座(X×Y)", "单边间隙", "槽底/落座", "判定"))
print("-" * 94)
for name, (pp, bp, cx, cy, seat) in PARTS.items():
    px, py = part_xy(os.path.join(ROOT, pp), seat)
    hx = pocket_halfwidth(bp, cx, cy, seat + 0.3, "x")
    hy = pocket_halfwidth(bp, cx, cy, seat + 0.3, "y")
    floor = pocket_floor(bp, cx, cy)
    gap = ((2 * hx - px) / 2 + (2 * hy - py) / 2) / 2
    dz = seat - floor
    ok = "OK" if (gap > 0.02 and abs(dz) < 0.5) else "!! 检查"
    print("%-9s %-18s %-18s %-12s %-10s %s" % (
        name, "%.1f × %.1f" % (2 * hx, 2 * hy), "%.1f × %.1f" % (px, py),
        "%+.2f mm" % gap, "%.1f / %.1f" % (floor, seat), ok))
