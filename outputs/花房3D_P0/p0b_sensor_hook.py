# -*- coding: utf-8 -*-
"""
P0-1b v2 盆沿挂钩式土壤传感器支架（2026-10-19，对齐 AR05 的盆沿双爪夹）
=====================================================================
v1 的问题：长斜臂 46mm 埋进土里 35mm —— 必须先卡盆沿再填土，装完不能调；
且 v1 的夹爪（jaw_down 16 / jaw_w 14 / rim_gap 5.6）与 AR05 新管夹 v2 不是同一套。

★ 2026-10-23 改为【方案 B · 土插式】（局部坐标：z=0 为土面，+Y 向盆外，+Z 向上）
  起因：实盆 8x8x8 直筒树脂盆壁厚 10~20mm，范围太宽，刚性双爪无法同时覆盖 → 弃用夹持。
  1. 两条插土腿（x 向薄片，板槽两侧各一）：深 35mm 插入土中，完全不碰盆壁 → 壁厚多少都行
  2. 夹板柱：底面坐在土面，顶面 z=36（板顶与柱顶齐平即到位）
  3. 板槽：沿 8° 斜轴贯穿夹板柱，传感器板从上方插入
  4. 传感器板不参与打印：总长 87，入土 51、露出土面 27（⇒ 土面在板顶下 36）
  5. 先立架子再填土 —— 板深可调（这正是 01b v1 想保留、v2 丢掉的能力）

打印朝向：两条腿落地（z_min=0），腿往上接夹板柱 —— 全垂直壁，免支撑。
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
    # ---------- 2026-10-23 改方案 B：土插式（不夹盆沿）----------
    # 理由：实盆 8x8x8 直筒树脂盆壁厚 10~20mm（范围太宽，刚性双爪无法同时覆盖：
    #       按 10 设计则壁 20 撑不开、按 20 设计则壁 10 合不拢，两种都会废件）。
    #       改为「两腿插土」—— 完全不依赖壁厚，且保留「先立架子再填土、板深可调」的能力。
    # 坐标系：z=0 为土面，z 向上；腿从 z=-leg_depth 插入土中。
    "soil_gap": 36.0,        # 土面→板顶 距离（板总长87, 入土51 ⇒ 土面在板顶下36）
    "leg_depth": 35.0,       # 插土深度（盆内土层 57~62，插 35 余量充足）
    "leg_t": 3.0,            # 腿厚（X 向薄片，插土阻力小）
    "leg_w": 14.0,           # 腿宽（Y 向）
    "leg_x": 15.5,           # 腿中心 X（±），内侧到板槽边留 2.2mm 壁
    "leg_y": -2.0,           # 腿的 Y 中心（略偏盆内，避开板槽前端）
    # 盆沿/夹爪参数保留但不再用于夹持（历史留档）
    "rim_gap": 4.6,          # [已弃用·改土插式]
    "taper": 0.0,            # [已弃用·改土插式]
    "wall_mid_y": 0.0,       # [已弃用·改土插式]
    "jaw_t": 3.5,            # [已弃用]
    "jaw_w": 20.0,           # [已弃用]
    "jaw_w_in": 25.2,        # [已弃用]
    "jaw_down": 7.0,         # [已弃用]
    # ---------- 夹板柱（板槽所在）----------
    "col_x": 36.0,           # 柱宽（加宽给两条腿让位；壁厚 (36-23.6)/2 = 6.2）
    "col_y": -2.0,           # 柱中心 Y
    "col_d": 12.0,           # 柱深（Y）
    "col_h": 36.0,           # 柱高 = 土面到板顶（板顶与柱顶齐平即到位）
    "rail_x": 13.95,         # [已弃用]
    "rail_w": 3.5,           # [已弃用]
    "rail_y_out": 5.3,       # [已弃用]
    "rail_y_in": -14.0,      # [已弃用]
    "rail_t": 6.0,           # [已弃用]
    # ---------- 板槽 ----------
    "tilt": 8.0,             # 板倾角
    "groove_w": 23.6,        # 槽宽 X = 板宽 23 + 0.6
    "groove_gap": 1.4,       # 槽厚 = 板厚 1.5 - 0.1 过盈
    "slot_len": 46.0,        # 槽长（沿轴，贯穿柱子上下表面即可）
    # ---------- 板（仅用于装配示意，不打印；尺寸 2026-10-19 领导手绘图实测）----------
    "board_w": 23.0,         # [实测] 头部宽 23
    "board_probe_w": 13.5,   # [实测] 探针段宽 13.5（手绘图③；商品图①标 15 以手绘为准）
    "board_t": 1.5,          # [实测 10-19] PCB 厚 1.5
    "board_len": 87.0,       # [实测] 含尖头总长 87
    "board_head_len": 15.0,  # [实测] 头段（23宽）轴向长 15 —— 硬约束：槽内过盈夹持段须 ≥10 即可（现夹持体 27 深，头段+过渡段全程在槽内，宽度 23<23.6 全程容纳）
    "board_trans_len": 13.5, # [实测] 收窄过渡段长 13.5（23→13.5 宽线性过渡）
    "board_tip_len": 10.5,   # [实测] 尖头段长 10.5
    "board_top_z": None,     # None = 板顶与夹板柱顶面齐平（插入深度基准）
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
    # ==== 方案 B：土插式（z=0 为土面，向下为插入土中）====
    # 板槽轴向（8° 斜）与其法向（板槽宽度方向）
    _ar = np.deg2rad(p["tilt"])
    _axis = np.array([-np.sin(_ar), -np.cos(_ar)])
    nj = np.array([-_axis[1], _axis[0]])

    # ---- 1) 两条插土腿：x 向薄片，插在板槽两侧，完全不碰盆壁 ----
    ld = p["leg_depth"]
    legs = [B(sx * p["leg_x"], p["leg_y"], (p["soil_gap"] - ld) / 2,
               p["leg_t"], p["leg_w"], p["soil_gap"] + ld)
            for sx in (-1, 1)]
    body = union(legs, engine="manifold")

    # ---- 2) 夹板柱：底面坐在土面(z=0)，顶面 z=col_h（板顶与柱顶齐平即到位）----
    col = B(0, p["col_y"], p["col_h"] / 2, p["col_x"], p["col_d"], p["col_h"])
    body = union([body, col], engine="manifold")

    # ---- 4) 板槽：沿 8° 轴贯穿"顶桥 + 夹板柱"，两侧各留 3.2 壁 ----
    ang_r = np.deg2rad(p["tilt"])
    axis = np.array([-np.sin(ang_r), -np.cos(ang_r)])
    zc = p["col_h"] / 2                                  # 槽心在柱中（z=0 为土面）
    gc = np.array([p["col_y"] - (p["col_h"] - zc) * np.tan(ang_r), zc])
    half = p["slot_len"] / 2
    gp = [gc + nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 - axis * half,
          gc + nj * p["groove_gap"] / 2 - axis * half]
    body = difference([body, prism_yz(gp, -p["groove_w"] / 2, p["groove_w"] / 2)],
                      engine="manifold")

    zmin = float(body.bounds[0][2])
    body.apply_translation([0, 0, -zmin])
    # 落床后: z=0 是腿底（土面下 leg_depth），土面在 z=leg_depth
    body.metadata["soil_top_z"] = -zmin
    body.metadata["rim_top_z"] = -zmin   # 兼容旧字段名（语义已改为"土面高度"）
    gc_out = (float(gc[0]), float(gc[1] - zmin))
    return body, gc_out, axis


def board_mesh(p=P, gc=None, axis=None, rim_top_z=0.0):
    """装配示意用的传感器板（不打印）：头部 23 宽 15 长 / 过渡 13.5 / 探针 13.5 宽 / 尖头 10.5，总长 87。
    插进板槽后，板顶与夹板柱顶面齐平。"""
    ang = np.deg2rad(p["tilt"])
    L, HW, PW = p["board_len"], p["board_w"], p["board_probe_w"]
    hl, tl = p["board_head_len"], p["board_tip_len"]
    tl_len = p.get("board_trans_len", 4.0)            # 过渡段长
    pl = L - hl - tl_len - tl                         # 等宽探针段
    # 轮廓（x=宽，y=从板顶向尖头方向）
    pts = [(-HW / 2, 0), (HW / 2, 0), (HW / 2, hl),
           (PW / 2, hl + tl_len),
           (PW / 2, hl + tl_len + pl),
           (0.0, L),                                   # 尖头
           (-PW / 2, hl + tl_len + pl), (-PW / 2, hl + tl_len),
           (-HW / 2, hl)]
    poly = trimesh.path.polygons.Polygon(pts)
    m = trimesh.creation.extrude_polygon(poly, height=p["board_t"])
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    # 此时：X=宽，Y=厚度(-1.6~0)，Z=沿板长向下
    m.apply_transform(trimesh.transformations.rotation_matrix(-ang, [1, 0, 0]))
    m.apply_translation([0, -p["board_t"] / 2, 0])   # 挤出后厚度在 y 0..t，居中到 0

    if gc is not None:
        # 板顶（y=0 端）落在夹板柱顶面；gc 是落床坐标下的槽心
        # 方案B: 板顶与柱顶齐平 ⇒ 落床后板顶 z = soil_top_z + col_h
        top_z = rim_top_z + p["col_h"] if p["board_top_z"] is None else rim_top_z + p["board_top_z"]
        t = (top_z - float(gc[1])) / float(axis[1])
        cy = float(gc[0]) + float(axis[0]) * t
        cz = float(gc[1]) + float(axis[1]) * t
    else:
        cy, cz = p["col_y"], p["rail_t"] + p["col_h"]
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
