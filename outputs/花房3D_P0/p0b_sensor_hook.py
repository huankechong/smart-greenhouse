# -*- coding: utf-8 -*-
"""
P0-1b v2 盆沿挂钩式土壤传感器支架（2026-10-19，对齐 AR05 的盆沿双爪夹）
=====================================================================
v1 的问题：长斜臂 46mm 埋进土里 35mm —— 必须先卡盆沿再填土，装完不能调；
且 v1 的夹爪（jaw_down 16 / jaw_w 14 / rim_gap 5.6）与 AR05 新管夹 v2 不是同一套。

v2 结构（局部坐标：原点 = 盆沿壁中线(r=39.5) 与 盆沿顶面(z=0)；+Y 向外径向，+Z 向上）
  1. 内外夹爪：跨住盆沿壁，随锥度下探 7mm（土面在 z=-8，爪不入土）
  2. 两侧导轨（替代整块顶桥）：中间留空，让传感器板穿过
  3. 夹板柱：坐在导轨上，板槽沿 8° 斜轴贯穿，板从上方插入
  4. 传感器板本身不参与打印，插进后下部靠土支撑

打印朝向：两条爪落地（z_min=0），导轨在上跨接两爪，夹板柱再往上堆 —— 全垂直壁，免支撑。
"""

import os
import json
import numpy as np
import trimesh
from trimesh.creation import box
from trimesh.boolean import difference, union

OUT = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(OUT, "STL")
PREVIEW_DIR = os.path.join(OUT, "preview")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

VERSION = 2

P = {
    # ---------- 盆沿（模型实测：内 37 / 外 41，壁厚 4）----------
    "rim_gap": 5.6,          # 夹口 = 壁厚 4 + 1.6（实测 5.6 时与花盆干涉=0；4.6 会啃掉 21.9mm³）[实物到手按 实测壁厚+1.2 改]
    "taper": 8.1,            # 盆壁锥度 atan(12/85)=8.04°，取 8.1° 略让开
    "wall_mid_y": -0.5,      # 盆壁中线在局部坐标的 Y（壁占 -2.5~+1.5，中线 -0.5）
    # ---------- 夹爪 ----------
    "jaw_t": 3.5,            # 爪厚
    "jaw_w": 20.0,           # 外爪宽（切向）——30mm 会因弦高切进盆壁
    "jaw_w_in": 25.2,        # 内爪宽：加宽到与两侧导轨叠合（12.2~12.6），否则内爪悬空成独立块
    "jaw_down": 7.0,         # 爪下探 = 土面深度 8 - 1，不入土
    # ---------- 导轨（替代整块顶桥）----------
    "rail_x": 13.95,         # 导轨中心 X（±），内表面 = ±12.2，给 23 宽的板留通道
    "rail_w": 3.5,           # 导轨宽（X）
    "rail_y_out": 5.3,       # 导轨外端 Y（= 外爪外表面）
    "rail_y_in": -14.0,      # 导轨内端 Y（伸到盆口内侧，托住夹板柱）
    "rail_t": 6.0,           # 导轨厚（Z），z 0~6
    # ---------- 夹板柱 ----------
    "col_x": 30.0,           # 柱宽 X
    "col_y": -8.0,           # 柱中心 Y（负 = 盆内方向）
    "col_d": 12.0,           # 柱深 Y
    "col_h": 21.0,           # 柱高（导轨顶面以上）
    # ---------- 板槽 ----------
    "tilt": 8.0,             # 板倾角
    "groove_w": 23.6,        # 槽宽 X = 板宽 23 + 0.6
    "groove_gap": 1.5,       # 槽厚 = 板厚 1.6 - 0.1 过盈
    "slot_len": 46.0,        # 槽长（沿轴，贯穿柱子上下表面即可）
    # ---------- 板（仅用于装配示意，不打印）----------
    "board_w": 23.0,         # [实测待填] PCB 宽
    "board_t": 1.6,          # [实测待填] PCB 厚
    "board_len": 98.0,       # [市售常见值] 含探针段总长
    "board_bottom_z": -70.0, # 板下端在局部坐标的 Z（= 入土 62mm）
}


def prism_yz(pts_yz, x0, x1):
    """凸多边形 (y,z) 沿 X 拉伸"""
    p = np.asarray(pts_yz, float)
    n = len(p)
    v = np.vstack([np.column_stack([[x0] * n, p[:, 0], p[:, 1]]),
                   np.column_stack([[x1] * n, p[:, 0], p[:, 1]])])
    f = []
    for i in range(1, n - 1):
        f.append([0, i + 1, i]); f.append([n, n + i, n + i + 1])
    for i in range(n):
        j = (i + 1) % n
        f.append([i, j, n + j]); f.append([i, n + j, n + i])
    m = trimesh.Trimesh(vertices=v, faces=np.asarray(f), process=True)
    m.fix_normals()
    return m


def B(cx, cy, cz, sx, sy, sz):
    m = box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, cz])
    return m


def _board_line(p):
    """板/槽的中心线：返回 (axis_yz, 线上任意点 yz)"""
    ang = np.deg2rad(p["tilt"])
    axis = np.array([-np.sin(ang), -np.cos(ang)])   # 向下、向内
    top = np.array([p["col_y"], p["rail_t"] + p["col_h"]])   # 柱顶面处的板中心
    return axis, top


def build(p=P):
    """返回 (body, groove_center_yz, axis_yz)；body 已落床（z_min=0），
    metadata['rim_top_z'] 记录了盆沿顶面在落床后的高度。"""
    jt, jw, jd = p["jaw_t"], p["jaw_w"], p["jaw_down"]
    tp = np.deg2rad(p["taper"])
    g = p["rim_gap"] / 2
    ymid = p["wall_mid_y"]

    d = np.array([-np.sin(tp), -np.cos(tp)])      # 爪轴：向下并随锥度内收
    nj = np.array([-d[1], d[0]])

    def slab(c_top, half_t, length, x0, x1):
        c = np.asarray(c_top, float) + d * (length / 2)
        pts = [c + nj * half_t + d * length / 2, c - nj * half_t + d * length / 2,
               c - nj * half_t - d * length / 2, c + nj * half_t - d * length / 2]
        return prism_yz(pts, x0, x1)

    # ---- 1) 内外夹爪（以盆壁中线为基准，两侧各留 0.3 余量）----
    outer = slab((ymid + g + jt / 2, p["rail_t"] * 0.3), jt / 2, jd, -jw / 2, jw / 2)
    inner = slab((ymid - g - jt / 2, p["rail_t"] * 0.3), jt / 2, jd, -jw / 2, jw / 2)
    body = union([outer, inner], engine="manifold")

    # ---- 2) 顶桥：整块跨过盆沿，向盆内伸到 y=col_y-col_d/2（托住夹板柱）----
    ry_out, ry_in = p["rail_y_out"], p["col_y"] - p["col_d"] / 2
    bridge = B(0, (ry_out + ry_in) / 2, p["rail_t"] / 2, p["col_x"], ry_out - ry_in, p["rail_t"])
    body = union([body, bridge], engine="manifold")

    # ---- 3) 夹板柱（底面下探 0.6 与顶桥叠合）----
    cz0 = p["rail_t"] - 0.6
    col = B(0, p["col_y"], cz0 + p["col_h"] / 2 + 0.5, p["col_x"], p["col_d"], p["col_h"] + 1.0)
    body = union([body, col], engine="manifold")

    # ---- 4) 板槽：沿 8° 轴贯穿"顶桥 + 夹板柱"，两侧各留 3.2 壁 ----
    ang_r = np.deg2rad(p["tilt"])
    axis = np.array([-np.sin(ang_r), -np.cos(ang_r)])
    zc = cz0 + p["col_h"] / 2
    gc = np.array([p["col_y"] - (p["rail_t"] + p["col_h"] - zc) * np.tan(ang_r), zc])
    half = p["slot_len"] / 2
    gp = [gc + nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 - axis * half,
          gc + nj * p["groove_gap"] / 2 - axis * half]
    body = difference([body, prism_yz(gp, -p["groove_w"] / 2, p["groove_w"] / 2)],
                      engine="manifold")

    zmin = float(body.bounds[0][2])
    body.apply_translation([0, 0, -zmin])
    body.metadata["rim_top_z"] = -zmin
    gc_out = (float(gc[0]), float(gc[1] - zmin))
    return body, gc_out, axis


def board_mesh(p=P, gc=None, axis=None, rim_top_z=0.0):
    """装配示意用的传感器板（不打印）。板顶与夹板柱顶面齐平，下端入土。"""
    ang = np.deg2rad(p["tilt"])
    m = box(extents=[p["board_w"], p["board_t"], p["board_len"]])
    m.apply_transform(trimesh.transformations.rotation_matrix(-ang, [1, 0, 0]))
    if gc is not None:
        # 沿着"板槽中心线"走到板中心所在高度（gc 是落床坐标下的槽心）
        zc_target = p["board_bottom_z"] + rim_top_z + 0.5 * p["board_len"] * np.cos(ang)
        t = (zc_target - float(gc[1])) / float(axis[1])
        cy = float(gc[0]) + float(axis[0]) * t
        cz = float(gc[1]) + float(axis[1]) * t
    else:
        _, top = _board_line(p)
        zc = p["board_bottom_z"] + 0.5 * p["board_len"] * np.cos(ang)
        cy = p["col_y"] - (p["rail_t"] + p["col_h"] - zc) * np.tan(ang)
        cz = zc
    m.apply_translation([0.0, cy, cz])
    return m


if __name__ == "__main__":
    mesh, gc, axis = build()
    mesh.merge_vertices()
    mesh.fix_normals()
    stl = os.path.join(STL_DIR, "01b_sensor_rim_hook_v2.stl")
    mesh.export(stl)
    rep = {
        "version": VERSION,
        "watertight": bool(mesh.is_watertight),
        "bodies": len(mesh.split(only_watertight=False)),
        "bbox": [round(float(x), 2) for x in mesh.extents],
        "z_min": round(float(mesh.bounds[0][2]), 3),
        "vol_mm3": round(float(mesh.volume), 1),
        "solid_g": round(float(mesh.volume) * 1.24 / 1000, 1),
        "tris": len(mesh.faces),
        "rim_top_z": round(float(mesh.metadata["rim_top_z"]), 2),
        "groove_center_yz": [round(gc[0], 2), round(gc[1], 2)],
    }
    print(json.dumps(rep, ensure_ascii=False, indent=1))
