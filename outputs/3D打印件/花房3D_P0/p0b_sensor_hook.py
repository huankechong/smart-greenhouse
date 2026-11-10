# -*- coding: utf-8 -*-
"""
P0-1b v2 盆沿挂钩式土壤传感器支架（2026-10-19，对齐 AR05 的盆沿双爪夹）
=====================================================================
v1 的问题：长斜臂 46mm 埋进土里 35mm —— 必须先卡盆沿再填土，装完不能调；
且 v1 的夹爪（jaw_down 16 / jaw_w 14 / rim_gap 5.6）与 AR05 新管夹 v2 不是同一套。

★ 2026-10-23 改为【方案 B · 土插式】（局部坐标：z=0 为土面，+Y 向盆外，+Z 向上）
  起因：实盆 8x8x8 直筒树脂盆壁厚 10~20mm，范围太宽，刚性双爪无法同时覆盖 → 弃用夹持。
  ★★ 2026-10-24 二次减薄 + 合并管环（领导要种两株薄荷，土面不够）：
     col_x 36→30、col_d 12→10；腿从「X 向两侧薄片」改为「Y 向前后两条宽片」（不占柱宽）；
     把 03 管夹的 C 形管环**合并进本件 +X 侧** → 03 作废，总占地 912→470 mm²（−48%）
  ★★ 2026-10-24 三次减薄（领导要求再薄）：col_x 30→27、col_d 10→6；
     腿改「柱子直接向下延伸进土」+ 土里两侧稳定鳍（鳍只在土面以下，不占土面）
     → 土面上方投影 27×6 = 162 mm²（原 300，再减 46%）
  1. 主体：柱 27×6 从土面上方 36 一延伸到土面下 35，板槽贯穿全长
     2. 土里两侧稳定鳍：27 × 5.5 × 高20，位于土面下 12~32，提供抗倾覆
  2. 夹板柱：底面坐在土面，顶面 z=36（板顶与柱顶齐平即到位）
  3. 板槽：沿 8° 斜轴贯穿夹板柱，传感器板从上方插入
  4. C 形管环：+X 侧凸台，竖孔 φ10.6，开口 6.2（朝盆内，管子压进去不掉）
  5. 先立架子再填土 —— 板深可调

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
    "leg_t": 5.5,            # 土里稳定鳍的厚度（Y）—— 鳍在板槽两侧，不挡板
    "leg_w": 27.0,           # 鳍宽（X）= 柱宽
    "leg_dy": 0.0,           # [弃用] 鳍改为按 col_d 自动定位
    "fin_h": 20.0,           # 鳍高（Z），位于土面下 12~32
    "fin_bury": 1.0,         # 鳍内侧伸进柱子 1mm，避免共面（共面会 bodies=2）
    # 盆沿/夹爪参数保留但不再用于夹持（历史留档）
    "rim_gap": 4.6,          # [已弃用·改土插式]
    "taper": 0.0,            # [已弃用·改土插式]
    "wall_mid_y": 0.0,       # [已弃用·改土插式]
    "jaw_t": 3.5,            # [已弃用]
    "jaw_w": 20.0,           # [已弃用]
    "jaw_w_in": 25.2,        # [已弃用]
    "jaw_down": 7.0,         # [已弃用]
    # ---------- 夹板柱（板槽所在）----------
    "col_x": 27.0,           # 柱宽（板槽23.6 + 两侧壁1.7）—— 30→27，过盈挤压方向不靠它
    "col_y": -2.0,           # 柱中心 Y
    "col_d": 9.0,            # 柱深（2026-11-10：6→9。接线端实测 3.1 厚，上段槽要 3.4，两侧壁各 2.8）
    "col_h": 36.0,           # 柱高 = 土面到板顶（板顶与柱顶齐平即到位）
    # ---------- 水管 C 形卡箍（2026-10-23 从 03 件合并进来，03 作废）----------
    "ring_on": False,        # 管孔φ10.6 需 Y深≥14.6，30×10 的柱放不下 → 改由 03 窄版管夹承担         # 是否带管环
    "ring_boss_w": 17.0,     # 卡箍凸台从柱边外伸宽度
    "ring_boss_h": 8.0,      # 凸台高（Z）
    "ring_z": 12.0,          # 管孔中心离土面高度
    "ring_od": 9.0,          # 环外半径
    "ring_id": 10.6,         # 管孔内径 = 管外径 10 + 0.6
    "ring_slot_w": 6.2,      # C 形开口宽（<管外径10，压进去不自己掉）
    "rail_x": 13.95,         # [已弃用]
    "rail_w": 3.5,           # [已弃用]
    "rail_y_out": 5.3,       # [已弃用]
    "rail_y_in": -14.0,      # [已弃用]
    "rail_t": 6.0,           # [已弃用]
    # ---------- 板槽 ----------
    "tilt": 0.0,             # 板倾角 [AR28 2026-11-09: 8°→0°。柱深仅 6mm，8° 在 ±35mm 高度横移 ±4.9mm，槽会穿出侧壁]
    "groove_w": 23.6,        # 槽宽 X = 板宽 23 + 0.6
    "groove_gap": 1.8,
    "term_t": 3.1,           # [实测 2026-11-10] 接线端最厚 3.1
    "term_len": 21.0,        # 接线端长度（板 87 − 感湿区 66.3 ≈ 20.7，取 21）
    "term_clear": 0.3,       # 接线端单边间隙
    "open_window": False,    # 感湿窗/接线端开口（2026-11-10 领导看过效果图后要求删掉，恢复封闭槽）       # 槽厚 [AR28: 1.4→1.8。板 1.5~1.6，单边 0.1 间隙是 FDM 可打印下限；原 1.4 打成死缝]
    "slot_len": 81.0,        # 槽长 [AR28: 46→81 = 柱总高 71 + 上下各 5，贯通用]
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

def prism_xz(pts_xz, y0, y1):
    """凸多边形 (x,z) 沿 Y 拉伸"""
    p = np.asarray(pts_xz, float)
    n = len(p)
    v = np.vstack([np.column_stack([p[:, 0], [y0] * n, p[:, 1]]),
                   np.column_stack([p[:, 0], [y1] * n, p[:, 1]])])
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


def C(cx, cy, cz, r, h, sections=64):
    """圆柱/圆孔：中心 (cx,cy,cz)，半径 r，高 h（沿 Z）"""
    from trimesh.creation import cylinder
    m = cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([cx, cy, cz])
    return m


def cut(target, tools):
    """布尔差集（target 减 tools）"""
    return difference([target] + list(tools), engine="manifold")


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

    # ---- 1) 主体：柱直接向下延伸进土（土面上方投影 = col_x × col_d，最省土面）----
    ld = p["leg_depth"]
    body = B(0, p["col_y"], (p["col_h"] - ld) / 2,
             p["col_x"], p["col_d"], p["col_h"] + ld)

    # ---- 2) 土里两侧稳定鳍：只在土面以下展开，不占土面；避开中间板槽 ----
    ft, fw, fh = p["leg_t"], p["leg_w"], p["fin_h"]
    inner = p["col_d"] / 2 - p["fin_bury"]          # 内侧伸进柱子，保证 union 相连
    for sy in (-1, 1):
        fy = sy * (inner + ft / 2)
        body = union([body, B(0, p["col_y"] + fy, -ld + fh / 2 + 2,
                              fw, ft, fh)], engine="manifold")

    # ---- 3) 水管 C 形卡箍凸台（+X 侧外伸，管子竖向穿过）----
    if p.get("ring_on", False):
        bw, bh2, rz = p["ring_boss_w"], p["ring_boss_h"], p["ring_z"]
        bx_c = p["col_x"] / 2 + bw / 2 - 2.0          # 与柱边重叠 2mm 保证连接牢固
        ring_cx = p["col_x"] / 2 + bw - p["ring_od"] - 2.0
        # 凸台 Y 深度比柱小 0.4，避免与柱子共面（共面会导致布尔 union 产出两个体）
        boss = B(bx_c, p["col_y"], rz, bw, p["col_d"] - 0.4, bh2)
        body = union([body, boss], engine="manifold")
        # 竖向管孔
        body = cut(body, [C(ring_cx, p["col_y"], rz, p["ring_id"] / 2, bh2 + 6, sections=64)])
        # C 形开口（朝 -Y，管子从盆内侧压进去）
        # C 形开口：Y 向只切到孔心 +1，留 4mm 实心把凸台连在柱子上
        slot = B(ring_cx, p["col_y"] - 2.5, rz, p["ring_slot_w"], 7.0, bh2 + 6)
        body = cut(body, [slot])

    # ---- 3.5) 感湿窗 + 接线端开口（2026-11-10：领导指出感应区被塑料包住 / 接线端没出线空间）----
    # ① 感湿窗：把板槽两侧 3.6 的 PLA 在土面以下开掉（中间 17 宽），板面直接接触土壤。
    #    窗顶做成尖顶（≈45°）→ 免支撑，不会形成桥。
    # ② 接线端开口：把 +Y 侧壁在接线端那 16mm 开掉，杜邦头/线可以朝盆外弯出。
    if p.get("open_window", True):
        wx, peak = p.get("win_w", 17.0) / 2, p.get("win_peak", 5.0)
        win = prism_xz([(-wx, -33.0), (wx, -33.0), (wx, peak - wx), (0.0, peak), (-wx, peak - wx)],
                       -p["col_d"] / 2, p["col_d"] / 2)
        body = cut(body, [win])
        body = cut(body, [B(0, p["col_y"] + p["col_d"] / 4 + 0.2, 26.0,
                            p.get("win_w", 17.0), p["col_d"] / 2 + 1.0, 16.0)])

    # ---- 4) 板槽：沿竖直轴贯穿整根柱子（AR28 起 tilt=0，两侧各留 3.2 壁）----
    ang_r = np.deg2rad(p["tilt"])
    axis = np.array([-np.sin(ang_r), -np.cos(ang_r)])
    zc = (p["col_h"] - p["leg_depth"]) / 2                 # 槽心 = 柱子真实中点 [AR28: 原 col_h/2=18 使槽只覆盖上部，下半实心]
    gc = np.array([p["col_y"] - (p["col_h"] - zc) * np.tan(ang_r), zc])
    half = p["slot_len"] / 2
    gp = [gc + nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 + axis * half,
          gc - nj * p["groove_gap"] / 2 - axis * half,
          gc + nj * p["groove_gap"] / 2 - axis * half]
    body = difference([body, prism_yz(gp, -p["groove_w"] / 2, p["groove_w"] / 2)],
                      engine="manifold")

    # ---- 阶梯槽：上段（接线端）加宽到 3.1 + 0.3 单边 ----
    # 板顶 = 柱顶；接线端占板顶往下 term_len → 该段槽宽 = term_t + 2*term_clear
    gw2 = (p["term_t"] + 2 * p["term_clear"]) / 2
    t_top = -half                      # 柱顶（axis 指向下，故顶部为 -half）
    t_bot = -half + p["term_len"]      # 接线端下沿
    wide = [gc + nj * gw2 + axis * t_top, gc - nj * gw2 + axis * t_top,
            gc - nj * gw2 + axis * t_bot, gc + nj * gw2 + axis * t_bot]
    body = difference([body, prism_yz(wide, -p["groove_w"] / 2, p["groove_w"] / 2)],
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
