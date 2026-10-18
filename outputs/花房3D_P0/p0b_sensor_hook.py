# -*- coding: utf-8 -*-
"""
P0-1b 盆沿挂钩式土壤传感器支架
================================
替代 p0_models.py 里的 01_sensor_L_bracket（那个是"立在土里"的方案）。

结构（局部坐标: 原点在盆沿顶面中心, +Y 向外径向, +X 切向, +Z 向上）
  1. 内外夹爪: 跨住盆沿壁(3mm), 下端开口, 靠 12° 斜臂自锁
  2. 顶桥: 连接两爪
  3. 斜臂: 从顶桥内侧向下、向内倾 12°, 板槽贯穿, 探针斜插入土

打印朝向: 两条腿(外爪 + 斜臂)落地, 桥在上, 无需支撑。
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

P = {
    # 盆沿
    "rim_t": 4.0,            # [实测待填] 花盆壁厚(模型实测: 顶面 41-37=4)
    "rim_gap": 5.6,          # 夹口: 盆壁 4~4.35 且带锥度, 留 1.2 余量; 实物到手按 实测壁厚+0.6 改
    # 夹爪
    "arm_w": 30.0,           # 桥/斜臂宽 (X)
    "jaw_w": 14.0,           # 夹爪宽 —— 30mm 平板卡 φ80 圆盆时两端会切进盆壁(弦高)，只能收窄
    "jaw_t": 3.5,            # 爪厚
    "taper": 8.5,            # 盆壁锥度(角度) —— 夹爪必须跟着斜, 否则顶穿盆壁
    "jaw_down": 16.0,        # 爪子向下长度
    "reach": 14.0,           # 顶桥向内伸出量 —— 斜臂从这里下挂, 远离盆壁
    "bridge_h": 6.0,         # 顶桥厚
    # 斜臂
    "tilt": 8.0,            # 斜臂倾角 [设计决策: 盆是锥形(壁倾斜8°), 12°会贴壁/穿壁, 18°才留出余量]
    "link_t": 12.0,          # 斜臂法向厚度
    "link_len": 46.0,        # 斜臂沿轴长度
    "link_w": 30.0,          # 斜臂宽
    # 板槽
    "groove_w": 23.6,        # = 板宽 23 + 0.6
    "groove_gap": 1.5,       # = 板厚 1.6 - 0.1 过盈
    "groove_len": 74.0,      # 必须长于斜臂, 两端贯穿, 否则成封闭内腔(板也插不进去)
    # 板
    "board_w": 23.0,         # [实测待填] 传感器 PCB 宽
    "board_t": 1.6,          # [实测待填] PCB 厚
}


def rect_prism(center_yz, axis_yz, half_len, half_perp, x0, x1):
    """在 YZ 平面画一个沿 axis 方向、半长 half_len、半厚 half_perp 的矩形, 沿 X 拉伸"""
    c = np.asarray(center_yz, float)
    a = np.asarray(axis_yz, float)
    a = a / np.linalg.norm(a)
    p = np.array([-a[1], a[0]])          # 法向
    pts = [c + p * half_perp + a * half_len,
           c - p * half_perp + a * half_len,
           c - p * half_perp - a * half_len,
           c + p * half_perp - a * half_len]
    return trimesh.creation.extrude_polygon(
        trimesh.path.polygons.Polygon(pts), height=x1 - x0, transform=None
    ).apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))


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


def build(p=P):
    """局部坐标: 原点在盆沿壁中线(r=39.5)与盆沿顶面(z=盆沿顶), +Y 向外, +Z 向上"""
    jt, aw, jd, bh = p["jaw_t"], p["arm_w"], p["jaw_down"], p["bridge_h"]
    tp = np.deg2rad(p["taper"]); g = p["rim_gap"] / 2

    d = np.array([-np.sin(tp), -np.cos(tp)])          # 夹爪轴: 向下并随锥度内收
    nj = np.array([-d[1], d[0]])

    def slab(c_top, half_t, length, x0, x1):
        c = np.asarray(c_top, float) + d * (length / 2)
        pts = [c + nj * half_t + d * length / 2, c - nj * half_t + d * length / 2,
               c - nj * half_t - d * length / 2, c + nj * half_t - d * length / 2]
        return prism_yz(pts, x0, x1)

    # 1) 内外夹爪: 跟随盆壁锥度
    jw = p["jaw_w"]
    outer = slab((g + jt / 2, bh * 0.3), jt / 2, jd, -jw / 2, jw / 2)
    inner = slab((-(g + jt / 2), bh * 0.3), jt / 2, jd, -jw / 2, jw / 2)
    # 2) 顶桥: 向外压住外爪, 向内伸到 y=-reach (给斜臂让出盆内空间)
    reach = p["reach"]
    bridge = B(0, (6.3 - reach) / 2, bh / 2, aw, 6.3 + reach, bh)
    body = union([outer, inner, bridge], engine="manifold")

    # 3) 斜臂: 从顶桥内端下挂, 以 tilt 角伸进盆里
    ang = np.deg2rad(p["tilt"])
    axis = np.array([-np.sin(ang), -np.cos(ang)])
    start = np.array([-reach, bh * 0.55])   # 起点埋进顶桥, 保证连通
    link = prism_yz(
        [start + nj * p["link_t"] / 2, start - nj * p["link_t"] / 2,
         start - nj * p["link_t"] / 2 + axis * p["link_len"],
         start + nj * p["link_t"] / 2 + axis * p["link_len"]],
        -p["link_w"] / 2, p["link_w"] / 2)
    body = union([body, link], engine="manifold")

    # 4) 板槽: 沿斜臂轴贯穿
    gc = start + axis * (p["link_len"] * 0.55)
    gp = [gc + nj * p["groove_gap"] / 2 + axis * p["groove_len"] / 2,
          gc - nj * p["groove_gap"] / 2 + axis * p["groove_len"] / 2,
          gc - nj * p["groove_gap"] / 2 - axis * p["groove_len"] / 2,
          gc + nj * p["groove_gap"] / 2 - axis * p["groove_len"] / 2]
    body = difference([body, prism_yz(gp, -p["groove_w"] / 2, p["groove_w"] / 2)],
                      engine="manifold")
    return body, gc, axis        # gc 是局部 (y,z) 二元组


def board_mesh(p=P, gc=None, axis=None):
    """板子: 绕 X 倾斜 tilt 度, 沿斜臂轴插在槽里
    box 局部: X=板宽, Y=板厚, Z=板长; +Z 端朝上外, -Z 端朝下内
    """
    ang = np.deg2rad(p["tilt"])
    m = box(extents=[p["board_w"], p["board_t"], 98.0])
    m.apply_transform(trimesh.transformations.rotation_matrix(-ang, [1, 0, 0]))
    m.apply_translation([0.0, float(gc[0]), float(gc[1])])   # 局部 (y,z) -> 世界 (x=0,y,z)
    return m


if __name__ == "__main__":
    mesh, gc, axis = build()
    mesh.merge_vertices()
    mesh.fix_normals()
    lo = mesh.bounds[0].copy()
    mesh.apply_translation([0, 0, -lo[2]])          # 落床
    stl = os.path.join(STL_DIR, "01b_sensor_rim_hook_v1.stl")
    mesh.export(stl)
    rep = {
        "watertight": bool(mesh.is_watertight),
        "bodies": len(mesh.split(only_watertight=False)),
        "bbox": [round(float(x), 2) for x in mesh.extents],
        "z_min": round(float(mesh.bounds[0][2]), 3),
        "vol_mm3": round(float(mesh.volume), 1),
        "solid_g": round(float(mesh.volume) * 1.24 / 1000, 1),
        "tris": len(mesh.faces),
        "local_origin_z": round(float(lo[2]), 2),
        "groove_center_yz": [round(float(gc[0]), 2), round(float(gc[1]), 2)],
    }
    print(json.dumps(rep, ensure_ascii=False, indent=1))
