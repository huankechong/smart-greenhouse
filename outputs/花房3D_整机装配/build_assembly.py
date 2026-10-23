# -*- coding: utf-8 -*-
"""
花房 Final Project · 整机系统示意模型（装配态）
================================================
基础: import 前面三批的参数化建模脚本, 复用同一份几何函数
      -> 装配图里的打印件与送打 STL 完全一致, 不是另画一套

产出:
  花房整机示意模型.glb      (可旋转查看)
  preview/00_整机四视图.png  + 单张视角

坐标系: 与整机底盘一致, 底板 z=0 为桌面, X 右为正, Y 前为正
"""
import os
import importlib.util
import numpy as np
import trimesh
from trimesh.creation import box, cylinder, icosphere

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_PREVIEW = os.path.join(HERE, "preview")
os.makedirs(OUT_PREVIEW, exist_ok=True)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M_P0 = load(os.path.join(ROOT, "花房3D_P0", "p0_models.py"), "m_p0")
M_P1 = load(os.path.join(ROOT, "花房3D_P1P2", "p1p2_models.py"), "m_p1")
M_BASE = load(os.path.join(ROOT, "花房3D_整机底盘", "base_2pc_models.py"), "m_base")
M_P0B = load(os.path.join(ROOT, "花房3D_P0", "p0b_sensor_hook.py"), "m_p0b")

C = {
    # —— 3D 打印件族：现实里都是同一种白色 PLA，只做极轻微区分 ——
    "base": (0.805, 0.842, 0.886),    # 底盘（浅冷灰）
    "white": (0.972, 0.976, 0.984),   # 打印件（近白）
    # —— 植物与土 ——
    "pot": (0.760, 0.455, 0.310),     # 花盆（陶土）
    "soil": (0.278, 0.192, 0.122),    # 土壤（深棕）
    "stem": (0.247, 0.631, 0.353),    # 植株
    "leaf": (0.247, 0.631, 0.353),    # 植株（同一株植物，不另配色）
    # —— 电控 ——
    "pcb_green": (0.122, 0.478, 0.235),  # 传感器/模块 PCB（深绿）
    "mcu": (0.169, 0.188, 0.220),        # ESP32（炭黑）
    "relay": (0.184, 0.341, 0.659),      # 继电器（靛蓝）
    "breadboard": (0.890, 0.851, 0.722), # 面包板（米黄）
    "screen": (0.055, 0.086, 0.149),     # OLED 屏（近黑蓝）
    "led": (0.839, 0.204, 0.161),        # 双色 LED 灯珠（红）
    "metal": (0.604, 0.639, 0.678),      # 螺丝 / 排针 / 屏蔽罩（不锈钢灰）
    "gold": (0.788, 0.635, 0.153),       # 铜探头 / 天线（铜金）
    "wire": (0.290, 0.310, 0.341),       # 跳线 / 面包板印线（哑光深灰）
    # —— 水系统 ——
    "tank": (0.659, 0.824, 0.910),    # 水箱（浅青）
    "water": (0.247, 0.557, 0.839),   # 水体（中蓝）
    "pump": (0.420, 0.447, 0.502),    # 水泵（岩灰）
    "tube": (0.059, 0.604, 0.659),    # 水管（青绿）
    "float": (0.929, 0.596, 0.278),   # 浮球浮子（琥珀，仅示意，实物为白/灰）
}


def prism_xy(poly, z0, z1):
    """凸多边形（XY）沿 Z 拉伸成棱柱；用于桶壁 90° 观察口"""
    pts = np.asarray(poly, dtype=float)
    n = len(pts)
    v = np.vstack([np.column_stack([pts, np.full(n, z0)]),
                   np.column_stack([pts, np.full(n, z1)])])
    f = []
    for i in range(1, n - 1):
        f.append([0, i, i + 1])
        f.append([n, n + i + 1, n + i])
    for i in range(n):
        j = (i + 1) % n
        f.append([i, n + i, n + j])
        f.append([i, n + j, j])
    m = trimesh.Trimesh(vertices=v, faces=np.asarray(f), process=True)
    m.fix_normals()
    return m


def place(mesh, x=0.0, y=0.0, z=0.0, rz=0.0):
    m = mesh.copy()
    if rz:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(rz), [0, 0, 1]))
    m.apply_translation([x, y, z])
    return m


def frustum(r_bot, r_top, h, sections=96):
    ang = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    bot = np.column_stack([r_bot * np.cos(ang), r_bot * np.sin(ang), np.zeros(sections)])
    top = np.column_stack([r_top * np.cos(ang), r_top * np.sin(ang), np.full(sections, h)])
    v = np.vstack([bot, top, [0, 0, 0], [0, 0, h]])
    f = []
    for i in range(sections):
        j = (i + 1) % sections
        f.append([i, j, sections + j])
        f.append([i, sections + j, sections + i])
    cb, ct = 2 * sections, 2 * sections + 1
    for i in range(sections):
        j = (i + 1) % sections
        f.append([cb, j, i])
        f.append([ct, sections + i, sections + j])
    m = trimesh.Trimesh(vertices=v, faces=np.asarray(f), process=True)
    m.fix_normals()
    return m


def _cyl(r, h, sec=20, axis="z", x=0.0, y=0.0, z=0.0):
    """圆柱（z 为该轴中心）；axis 指定轴向"""
    m = cylinder(radius=r, height=h, sections=sec)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, y, z])
    return m


def tube_path(points, r=5.0):   # 硅胶管外径 10 (实测)
    parts = []
    pts = [np.asarray(p, dtype=float) for p in points]
    for a, b in zip(pts[:-1], pts[1:]):
        v = b - a
        L = np.linalg.norm(v)
        if L < 1e-6:
            continue
        seg = cylinder(radius=r, height=L, sections=18)
        seg.apply_translation([0, 0, L / 2])
        seg.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
        seg.apply_translation(a)
        parts.append(seg)
    for p in pts[1:-1]:
        s = icosphere(subdivisions=2, radius=r)
        s.apply_translation(p)
        parts.append(s)
    return trimesh.boolean.union(parts, engine="manifold")


# ============================================================
PT = 8.0      # 底板顶面 (v1.2 板厚 8, 连接块与板面齐平)
items = []


def add(mesh, ck, name=""):
    items.append((mesh, ck, name))


# ---------- 1. 整机底盘两片 + 连接块 ----------
add(M_BASE.build_half(M_BASE.P, -1), "base", "底盘左片")
add(M_BASE.build_half(M_BASE.P, +1), "base", "底盘右片")
for jy in M_BASE.P["joint_y"]:
    add(place(M_BASE.build_block(M_BASE.P), 0, jy, PT - M_BASE.P["recess_d"]), "base", "连接块")

# ---------- 2. 花盆 + 土 ----------
POT = (-111.0, 60.0)         # 与底盘 pot_pos 同步 [2026-10-23 换 8x8x8 直筒盆]
R_BOT, R_TOP, POT_H, FLOOR = 40.0, 40.0, 80.0, 3.0   # 8x8x8 直筒盆: 外φ80恒定, 高80, 底厚3
pot = trimesh.boolean.difference(
    [frustum(R_BOT, R_TOP, POT_H), place(frustum(30.0, 30.0, POT_H - FLOOR), 0, 0, FLOOR)],
    engine="manifold")
add(place(pot, POT[0], POT[1], 2.0), "pot", "花盆")

SOIL_TOP = 2.0 + POT_H - 8.0        # = 79
# 土做成贴合盆内壁的锥台(只小 0.5mm), 否则盆下半截是空的, 传感器会扎进空气
soil = frustum(23.6, 35.2, 74.0, sections=72)
add(place(soil, POT[0], POT[1], 5.0), "soil", "土壤")

# ---------- 3. 植株 ----------
PLANT = (-84.0, 74.0)
stem = cylinder(radius=1.8, height=36.0, sections=16)
add(place(stem, PLANT[0], PLANT[1], SOIL_TOP + 18.0), "stem", "主茎")
for i in range(7):
    ang = i * 51.0 + 12.0
    z = SOIL_TOP + 12 + i * 3.6
    leaf = icosphere(subdivisions=3, radius=1.0)
    leaf.apply_scale([4.4, 10.5, 1.2])
    leaf.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(ang), [0, 0, 1]))
    leaf.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-34 + (i % 3) * 16), [1, 0, 0]))
    leaf.apply_translation([PLANT[0], PLANT[1], z])
    add(leaf, "leaf", "叶片")

# ---------- 4. 水箱：1L 打包桶（圆台）+ 3D 替换盖 + P52 浮球（AR08 圆桶化）----------
TANK = (85.0, 32.0)
# ★ 1L 打包桶【2026-10-23 到货实测·领导量具】底 φ105 / 口内 φ120 / 桶身口沿 φ124 / 桶口最外侧 φ132
#   桶口有加强翻边（从 124 再外凸 4mm 到 132）→ 盖板压翻边顶面、裙边套 132
BUCKET_BOT_OD, BUCKET_MOUTH_ID, BUCKET_MOUTH_OD = 105.0, 120.0, 132.0
BUCKET_H = 127.0              # 桶身高 [实测 127]
#   BUCKET_MOUTH_OD = 桶口【最外侧】= 加强翻边外径 132（实测）
#   桶身口沿外径 = 124（壁厚 = (124-120)/2 = 2）—— 翻边从 124 再外凸 4 到 132
#   桶高 127（实测）→ 桶口沿 z = 槽底3 + 127 = 130
BUCKET_RIM_OD = 124.0           # 桶身口沿外径（翻边根部）
BUCKET_LIP_H = 6.0              # 加强翻边高度 [待实测] —— 裙边高必须 <= 它
BUCKET_WALL = (BUCKET_RIM_OD - BUCKET_MOUTH_ID) / 2           # 2.0 侧壁厚（实测推算）
BOT_R, TOP_R, TANK_H, TANK_T = BUCKET_BOT_OD / 2, BUCKET_RIM_OD / 2, BUCKET_H, BUCKET_WALL
#   桶高 127（2026-10-23 实测）；桶底厚未实测，暂按侧壁厚 2.0 建模
# 替换盖几何（与 p10_tank_lid.py 同参数）
LID_SKIRT_CLR, LID_SKIRT_WALL, LID_SKIRT_H = 0.8, 2.8, 6.0   # 裙边高 <= 翻边高
LID_FLANGE_R = (BUCKET_MOUTH_OD + LID_SKIRT_CLR + 2 * LID_SKIRT_WALL) / 2   # 69.2 盖板半径
LID_SKIRT_IR = (BUCKET_MOUTH_OD + LID_SKIRT_CLR) / 2                       # 66.4 裙边内孔半径
TANK_Z = 3.0
TRIM = TANK_Z + TANK_H            # 123 桶口
LID_T = 4.0
LID_TOP = TRIM + LID_T            # 127 盖顶
TUBE_XY = (TANK[0], TANK[1] - 22.0)   # 盖顶水管孔 φ10（-Y 22）
WIRE_XY = (TANK[0], TANK[1] - 45.0)   # 盖顶过线孔 φ8（-Y 45，与水管同侧，电缆不横跨盖顶）

# 桶体：外锥台 − 内腔锥台，再切 90° 观察口（朝 +Y，露出泵/水体/浮子）
_bucket = trimesh.boolean.difference(
    [frustum(BOT_R, TOP_R, TANK_H),
     place(frustum(BOT_R - TANK_T, TOP_R - TANK_T, TANK_H - TANK_T), 0, 0, TANK_T)],
    engine="manifold")
# 加强翻边: 口沿外凸 4mm 到 phi132, 高 BUCKET_LIP_H (盖板压它顶面, 裙边套它外径)
_lip = place(frustum(BUCKET_MOUTH_OD / 2, BUCKET_MOUTH_OD / 2, BUCKET_LIP_H), 0, 0, TANK_H - BUCKET_LIP_H)
_lip = trimesh.boolean.difference(
    [_lip, place(frustum(TOP_R, TOP_R, BUCKET_LIP_H), 0, 0, TANK_H - BUCKET_LIP_H)], engine="manifold")
_bucket = trimesh.boolean.union([_bucket, _lip], engine="manifold")
_bucket = place(_bucket, TANK[0], TANK[1], TANK_Z)
_sec = np.linspace(-np.pi / 4, np.pi / 4, 25)
_wedge = prism_xy([(0.0, 0.0)] + [(85.0 * np.cos(t), 85.0 * np.sin(t)) for t in _sec],
                  TANK_Z - 6.0, TRIM + 2.0)
_wedge.apply_translation([TANK[0], TANK[1], 0.0])
add(trimesh.boolean.difference([_bucket, _wedge], engine="manifold"), "tank", "水箱")

# 水体：内腔半径随高度线性，水深 85mm（满口 1.2L ≈ 101mm，留气隙）
# 与桶壁同楔形剖开，否则不透明水体把泵整个挡住
_r_at = lambda h: (BOT_R - TANK_T) + (TOP_R - BOT_R) * h / TANK_H
_water = place(frustum(_r_at(0) - 0.6, _r_at(85.0) - 0.6, 85.0, 72),
               TANK[0], TANK[1], TANK_Z + TANK_T)
add(trimesh.boolean.difference([_water, _wedge], engine="manifold"), "water", "水体")

# 第 10 件替换盖：phi138.4x4 板 + 裙边内 phi132.8x6（套翻边） + phi20x0.8 螺母凸台，三孔 [按实测最外侧132]
_lid = trimesh.boolean.union([
    _cyl(LID_FLANGE_R, LID_T, 96, z=TRIM + LID_T / 2, x=TANK[0], y=TANK[1]),
    _cyl(LID_FLANGE_R, LID_SKIRT_H, 96, z=TRIM - LID_SKIRT_H / 2, x=TANK[0], y=TANK[1]),
    _cyl(10.0, 0.8, 48, z=TRIM - 0.4, x=TANK[0], y=TANK[1]),
], engine="manifold")
_lid = trimesh.boolean.difference([_lid,
    _cyl(LID_SKIRT_IR, LID_SKIRT_H + 0.4, 96, z=TRIM - LID_SKIRT_H / 2, x=TANK[0], y=TANK[1]),  # 裙边内孔（套桶口外壁124）
    _cyl(5.25, 70.0, 32, z=LID_TOP - 25.0, x=TANK[0], y=TANK[1]),                 # 浮球杆孔 φ10.5
    _cyl(5.0, LID_T + 4, 24, z=TRIM + LID_T / 2, x=TUBE_XY[0], y=TUBE_XY[1]),     # 水管孔 φ10
    _cyl(4.0, LID_T + 4, 24, z=TRIM + LID_T / 2, x=WIRE_XY[0], y=WIRE_XY[1]),     # 过线孔 φ8
    _cyl(13.0, 14.0, 40, z=TRIM - 1.0, x=TANK[0] + LID_FLANGE_R, y=TANK[1]),    # 指位缺口（+X）
    _cyl(13.0, 14.0, 40, z=TRIM - 1.0, x=TANK[0] - LID_FLANGE_R, y=TANK[1]),    # 指位缺口（−X）
], engine="manifold")
add(_lid, "white", "水箱盖")

# P52 浮球开关：法兰坐盖顶，杆有效长 52，浮子随水面（水满时半浸）
add(_cyl(11.0, 3.0, 40, z=LID_TOP + 1.5, x=TANK[0], y=TANK[1]), "white", "浮球法兰")
add(_cyl(8.0, 18.0, 32, z=LID_TOP + 12.0, x=TANK[0], y=TANK[1]), "white", "浮球本体")
add(_cyl(2.5, 52.0, 20, z=LID_TOP - 26.0, x=TANK[0], y=TANK[1]), "metal", "浮球杆")
_float = trimesh.boolean.difference(
    [_cyl(14.0, 18.0, 48, z=0.0), _cyl(3.3, 20.0, 32, z=0.0)], engine="manifold")
add(place(_float, TANK[0], TANK[1], 84.0), "float", "浮子")

# ---------- 5. 水泵（自带吸盘，直接吸在桶底；固定座已作废）----------
PUMP = (85.0, 32.0)
INNER_FLOOR = TANK_Z + TANK_T      # 5.0 桶内底（槽底3 + 壁厚2）
# 2026-10-24：泵自带吸盘，固定座作废（02 件不打印）—— 吸盘本身就把泵垫高约 2~3mm，
#               吸水口仍有间隙，所以下面的 _PZ 不用改（那 3mm 现在由吸盘提供）
# 实物泵体 41 × 39 × 30（含出水嘴 37），底脚 32 × 28 —— 方块 + 顶面出水嘴
_PZ = INNER_FLOOR + 3.0            # 8.0 泵体底面
add(place(box([41.0, 39.0, 30.0]), PUMP[0], PUMP[1], _PZ + 15.0), "pump", "水泵")
add(place(cylinder(radius=6.0, height=7.0, sections=32), PUMP[0] - 2.0, PUMP[1], _PZ + 33.5),
    "pump", "泵出水嘴")

# ---------- 6. 水管（v2：末端竖直穿过夹孔，孔径 8.6 / 管径 8，全程不蹭夹壁）----------
# 管孔世界坐标在夹子放置后算出（第 8 节），这里先按 AZ_CLIP 推导
_AZR = np.deg2rad(-12.0)
_RIM_R = (30.0 + 40.0) / 2
_CLIP_X = -111.0 + _RIM_R * np.cos(_AZR)
_CLIP_Y = 60.0 + _RIM_R * np.sin(_AZR)
_HOLE_X = _CLIP_X + (-11.0) * np.cos(_AZR)
_HOLE_Y = _CLIP_Y + (-11.0) * np.sin(_AZR)
tube_pts = [
    (83.0, 32.0, 44.0),             # 泵出水嘴顶
    (84.0, 22.0, 50.0),             # 先偏向 -Y（让开中心浮球杆 φ5）
    (TUBE_XY[0], TUBE_XY[1], 58.0),    # 到盖孔正下方，之后竖直（距杆轴 22 > 浮子半径 14+管 4）
    (TUBE_XY[0], TUBE_XY[1], 120.0),
    (TUBE_XY[0], TUBE_XY[1], 145.0),   # 竖直穿盖孔（123~127 同轴）
    (40.0, 4.0, 152.0),             # 出盖后向左上抬
    (-35.0, 40.0, 150.0),
    (_HOLE_X, _HOLE_Y, 136.0),      # 到盆沿管孔正上方
    (_HOLE_X, _HOLE_Y, 81.0),       # 竖直下穿管孔（全程同轴，不蹭壁）
]
add(tube_path(tube_pts, r=5.0), "tube", "水管")   # 外径 10 (实测)

# ---------- 7. 土壤传感器: 土插式支架（两腿插土，板槽在土面上方 36）----------
RIM_R = (30.0 + 40.0) / 2          # 盆沿壁中线半径(内30=壁厚10/外40, 8x8x8 直筒盆)
RIM_Z = 2.0 + POT_H                 # 盆沿顶面 = 82 (8x8x8 直筒盆)
PLANT_AZ = np.degrees(np.arctan2(PLANT[1] - POT[1], PLANT[0] - POT[0]))
AZ = PLANT_AZ + 180.0               # 挂在植株对面
# 方案B：架子插在【盆内土里】不在盆沿 —— 板身必须完全落在盆内腔中
_HOOK_R_OFF = 12.0   # 距盆心 12mm（内腔 r30 − 板半宽 11.5，安全）
rim_pt = (POT[0] + _HOOK_R_OFF * np.cos(np.deg2rad(AZ)),
          POT[1] + _HOOK_R_OFF * np.sin(np.deg2rad(AZ)))

# 方案B土插式（2026-10-23）：架子坐在【土面】上，两腿插入土中，不再夹盆沿
hook, gc, haxis = M_P0B.build()          # build 内部已落床，土面高度记在 metadata
hook_rot = trimesh.transformations.rotation_matrix(np.deg2rad(AZ - 90.0), [0, 0, 1])
hook.apply_transform(hook_rot)
hook.apply_translation([rim_pt[0], rim_pt[1], SOIL_TOP - hook.metadata["soil_top_z"]])
add(hook, "white", "传感器土插支架")

brow = M_P0B.board_mesh(gc=gc, axis=haxis, rim_top_z=hook.metadata["rim_top_z"])
brow.apply_transform(hook_rot)
brow.apply_translation([rim_pt[0], rim_pt[1], SOIL_TOP - hook.metadata["soil_top_z"]])
add(brow, "pcb_green", "土壤传感器板")

# ---------- 8. P0: 水管末端固定夹（土插式，两针插土，管环在土面上方）----------
AZ_CLIP = 40.0                      # 方案B：管夹插在盆内土里，避开传感器架(207°)
clip_rot = trimesh.transformations.rotation_matrix(np.deg2rad(AZ_CLIP - 90.0), [0, 0, 1])
# 方案B土插式：管夹插在盆内土里，按【盆心 + 半径偏移】算（不再贴盆沿）
_CLIP_R_OFF = 18.0   # 窄版管夹(15×15)，贴盆边放，让开中间给薄荷
clip_pt = (POT[0] + _CLIP_R_OFF * np.cos(np.deg2rad(AZ_CLIP)),
           POT[1] + _CLIP_R_OFF * np.sin(np.deg2rad(AZ_CLIP)))
clip_mesh = M_P0.build_tube_clip(M_P0.PARAMS["clip"])
clip_mesh.apply_transform(clip_rot)
clip_mesh.apply_translation([clip_pt[0], clip_pt[1], SOIL_TOP - clip_mesh.metadata["soil_top_z"]])
add(clip_mesh, "white", "水管末端夹(土插)")
# 管孔世界坐标：局部 (0, col_y) 经旋转平移到落点
CLIP_RY = M_P0.PARAMS["clip"]["col_y"]
hole_xy = (clip_pt[0] + CLIP_RY * np.cos(np.deg2rad(AZ_CLIP)),
           clip_pt[1] + CLIP_RY * np.sin(np.deg2rad(AZ_CLIP)))

# ---------- 9. P1: OLED 支架 + 屏 ----------
OLED = (-45.0, 38.0)
add(place(M_P1.build_oled_stand(M_P1.PARAMS["oled"]), OLED[0], OLED[1], PT), "white", "OLED 45°支架")
scr = box([27.3, 27.3, 1.6])          # 板面在斜面内, 厚度沿法线
scr.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(-45), [1, 0, 0]))
# 斜面中心在 (y = -5, z = PT+15); 屏底落在槽底(深2.4), 屏心沿法线内缩 0.8
scr.apply_translation([OLED[0], OLED[1] + 0.11, PT + 14.75])
add(scr, "screen", "OLED 屏")

# ---------- 10. 双色 LED（裸灯珠，灯罩已取消：无半透明耗材）----------
LED = (-22.0, 18.0)
add(place(cylinder(radius=2.5, height=7.7, sections=32), LED[0], LED[1], PT + 0.9 + 3.85), "led", "LED 灯珠")
add(place(cylinder(radius=2.95, height=0.9, sections=32), LED[0], LED[1], PT + 0.45), "led", "LED 法兰")

# ---------- 11. 面包板 + ESP32 + 继电器 ----------
SEAT = PT - 3.5                      # 槽深 3.5 -> 槽底 z=4.5, 件必须坐进去
BB_TOP = SEAT + 10.0                 # 面包板顶面 = 14.5
add(place(box([84.0, 55.0, 10.0]), -105.0, -55.0, SEAT + 5.0), "breadboard", "面包板")
# ESP32 实测 51.5×28（含 Type-C 突出 53），PCB 厚 1.5；竖直插在面包板上，
# 厚度方向 11 = PCB 1.5 + 两侧排针塑料座，故整体按 51.5 × 11 × 28 画
add(place(box([51.5, 11.0, 28.0]), -100.0, -50.0, BB_TOP + 14.0), "mcu", "ESP32")
add(place(box([34.0, 25.0, 15.0]), -45.0, -20.0, SEAT + 7.5), "relay", "继电器")

# ---------- 12. P2: DHT11 座 + 模块 ----------
# DHT11 从 (-52,92) 移到 (-45,-60)：原位置正对屏幕视线, 正面遮挡 42%/高角度 47%
DHT = (-45.0, -60.0)
add(place(M_P1.build_dht_holder(M_P1.PARAMS["dht"]), DHT[0], DHT[1], PT), "white", "DHT11 座")
add(place(box([29.0, 12.0, 7.0]), DHT[0], DHT[1] - 17.0 + 9.0, PT + 55.0 + 9.0), "pcb_green", "DHT11")

# ---------- 13. P2: 扎线固定座 ----------
add(place(M_P1.build_cable_clip(M_P1.PARAMS["clip3"]), -75.0, 8.0, PT, rz=8), "white", "扎线座")


# ============================================================
# ============================================================
# 细节层 v1.7 —— 电子件特征 / 螺丝 / 跳线（只加几何，不动 STL）
#   预算：新增 ≤10k 面；所有件仍用布尔过的 STL，细节件仅作渲染
# ============================================================
def _cat(parts):
    """渲染用合并：直接拼接，不做布尔（细节件不需要封闭单体）"""
    return trimesh.util.concatenate(parts)


def _bx(x, y, z, sx, sy, sz):
    return box(extents=[sx, sy, sz]).apply_translation([x, y, z])


def make_screw(x, y, z_top, head_d=6.0, head_h=1.8, shaft_d=3.0, shaft_l=5.0):
    """M3×6 盘头自攻：头坐在 φ6.2 沉窝里，头面与板面齐平"""
    head = _cyl(head_d / 2, head_h, 20, z=z_top - head_h / 2, x=x, y=y)
    shaft = _cyl(shaft_d / 2, shaft_l, 14, z=z_top - head_h - shaft_l / 2, x=x, y=y)
    return _cat([head, shaft])


# ---------- 14. 面包板表面特征（孔阵 / 中央沟 / 电源轨） ----------
holes = []
for bx0 in (-133.0, -95.0):     # 左/右两块孔区（中间让出中央沟）
    for i in range(12):
        for j in range(4):
            holes.append(_cyl(0.95, 0.5, 8, z=BB_TOP - 0.2, x=bx0 + i * 3.0, y=-70.0 + j * 3.0))
add(_cat(holes), "mcu", "面包板孔阵")
add(_bx(-105.0, -55.0, BB_TOP - 0.15, 3.2, 53.0, 0.4), "mcu", "面包板中央沟")
rails = [_bx(-105.0, yy, BB_TOP - 0.12, 80.0, 1.0, 0.3) for yy in (-80.0, -76.0, -34.0, -30.0)]
add(_cat(rails), "wire", "面包板电源轨")

# ---------- 15. ESP32 板载件（USB-C / 按键 / 天线 / 屏蔽罩） ----------
# 板载件贴在模组朝 +Y 的一侧（面在 y=-44.5）
MCU_TOP = BB_TOP + 28.0          # = 42.5
add(_bx(-124.5, -50.0, BB_TOP + 4.5, 3.0, 13.0, 9.0), "mcu", "ESP32 USB-C")
add(_bx(-118.0, -43.9, BB_TOP + 6.0, 4.0, 1.2, 3.0), "mcu", "ESP32 按键")
add(_bx(-113.0, -43.9, BB_TOP + 6.0, 4.0, 1.2, 3.0), "mcu", "ESP32 EN键")
add(_bx(-82.0, -43.9, MCU_TOP - 7.0, 16.0, 0.8, 11.0), "gold", "ESP32 天线")
add(_bx(-100.0, -43.0, BB_TOP + 15.0, 18.0, 2.0, 13.0), "metal", "ESP32 屏蔽罩")

# ---------- 16. 继电器端子 / 指示灯 / 光耦 ----------
RL_TOP = SEAT + 15.0            # = 19.5
terms = [_bx(x, -29.0, RL_TOP + 3.0, 6.0, 6.0, 6.0) for x in (-56.0, -49.0, -42.0)]
add(_cat(terms), "pcb_green", "继电器端子")
add(_cyl(1.6, 1.4, 12, z=RL_TOP + 0.7, x=-38.0, y=-14.0), "led", "继电器指示灯")
add(_bx(-52.0, -14.0, RL_TOP + 1.0, 6.0, 5.0, 2.0), "mcu", "继电器光耦")

# ---------- 17. OLED 排线 / 排针 / 驱动 IC ----------
add(_bx(-45.0, 24.0, 17.5, 16.0, 0.5, 7.0), "mcu", "OLED FPC 排线")
add(_bx(-45.0, 22.4, 13.4, 12.0, 1.6, 1.2), "metal", "OLED 排针")
add(_bx(-45.0, 41.5, 21.0, 9.0, 9.0, 1.2), "mcu", "OLED 驱动 IC")

# ---------- 18. 土壤传感器：铜探头 / 排针 ----------
add(_bx(-137.1, 42.6, 30.0, 0.35, 4.0, 26.0), "gold", "传感器铜探头 L")
add(_bx(-138.7, 33.6, 30.0, 0.35, 4.0, 26.0), "gold", "传感器铜探头 R")
add(_bx(-137.9, 49.0, 112.0, 9.0, 1.4, 1.4), "metal", "传感器排针")

# ---------- 19. DHT11 格栅 ----------
for k in range(3):
    add(_bx(-45.0, -45.4, 66.0 + k * 3.0, 9.0, 0.5, 1.1), "mcu", "DHT11 格栅%d" % k)

# ---------- 20. 水泵进水格栅 / 出水嘴 / 电源线 ----------
# 底吸口：泵体正下方的方形格栅（泵座底板中间已开 34×30 的孔）
_g = [_bx(PUMP[0], PUMP[1] - 12.0 + k * 6.0, _PZ - 0.6, 30.0, 2.0, 1.2) for k in range(5)]
add(_cat(_g), "mcu", "水泵进水格栅")

# ---------- 21. 8 颗 M3×6 螺丝（底盘连接块，头面齐平 z=8） ----------
for jy in (70.0, -70.0):
    for sx in (-14.0, 14.0):
        for sy in (-7.0, 7.0):
            add(make_screw(sx, jy + sy, PT), "metal", "M3×6 螺丝")

# ---------- 22. 跳线 20 根（单色灰，避免彩线糊成一片） ----------
# ⚠️ 盖顶相关 z 一律用 LID_TOP 派生（桶高/盖高变了自动跟随），不要硬编码
def wire(points, r=1.05, sec=12):
    parts = []
    pts = [np.asarray(p, dtype=float) for p in points]
    for a, b in zip(pts[:-1], pts[1:]):
        v = b - a
        L = float(np.linalg.norm(v))
        if L < 1e-6:
            continue
        seg = cylinder(radius=r, height=L, sections=sec)
        seg.apply_translation([0, 0, L / 2])
        seg.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
        seg.apply_translation(a)
        parts.append(seg)
    return _cat(parts)


WIRES = [
    # ① ESP32 → OLED（4 根）：从板右缘出，绕过继电器上方，进屏架前下方
    [(-71.0, -40, 24), (-66, -8, 17), (-56, 14, 15), (-49, 20.4, 18)],
    [(-71.0, -43, 24), (-67, -6, 17), (-57, 15, 15), (-50, 20.4, 18)],
    [(-71.0, -46, 24), (-68, -4, 17), (-58, 16, 15), (-51, 20.4, 18)],
    [(-71.0, -49, 24), (-69, -2, 17), (-59, 17, 15), (-52, 20.4, 18)],
    # ② ESP32 → DHT11（1 根）：从正面进 DHT 座（端头停在座壁外 0.5，不在座内）
    [(-71.0, -44, 24), (-64, -38, 16), (-50, -38, 12), (-45, -42.4, 11.0)],
    # ③ ESP32 → 土壤传感器（3 根）：绕花盆南侧，沿盆沿外侧上行
    # 方案B土插式：盆是实体壁(z=5~82)，线必须【从盆口上方越过】再降到板头
    # 路径：沿底板到盆外 -> 竖直升到盆沿以上(z>82) -> 水平跨过盆口 -> 板头上方落下
    [(-68.0, -38, 22), (-66, -20, 12), (-70, 2, 12), (-95, 10, 12),
     (-95, 10, 95), (-136, 54, 115), (-122, 54, 118)],
    [(-68.0, -35, 22), (-65, -18, 12), (-69, 4, 12), (-95, 11, 12),
     (-95, 11, 96), (-137, 55, 116), (-123, 55, 119)],
    [(-68.0, -32, 22), (-64, -16, 12), (-68, 6, 12), (-95, 12, 12),
     (-95, 12, 97), (-138, 56, 117), (-124, 56, 120)],
    # ④ ESP32 → 继电器 IN（1 根）：从上方落到端子
    [(-71.0, -45, 24), (-64, -32, 24), (-52, -29, 25.4)],
    # ⑤ 继电器 → 水泵（2 根）：沿底板 -Y 侧走，抬到盖顶上方，从 φ8 过线孔（-Y45）进桶
    [(-27.4, -18, 19), (0, -34, 26), (40, -42, 48), (74, -47, 104),
     (78, -46, LID_TOP + 2), (WIRE_XY[0], WIRE_XY[1], LID_TOP + 2), (WIRE_XY[0], WIRE_XY[1], 120.0),
     (88.0, -6, 112), (92.0, 16, 78), (86.0, 38, 46)],
    [(-27.4, -21, 19), (2, -36, 26), (42, -44, 48), (76, -49, 104),
     (80, -47, LID_TOP + 2), (WIRE_XY[0] + 1.5, WIRE_XY[1] - 1.5, LID_TOP + 2),
     (WIRE_XY[0] + 1.5, WIRE_XY[1] - 1.5, 120.0),
     (89.5, -8, 112), (93.5, 14, 78), (87.0, 37, 46)],
    # ⑥ ESP32 → 面包板电源轨（2 根）
    [(-76, -35.2, 20), (-84, -32, 16), (-92, -30, 14.8)],
    [(-80, -35.2, 20), (-88, -31, 16), (-100, -30, 14.8)],
    # ⑦ ESP32 → 面包板信号（3 根）
    [(-84, -35.2, 20), (-96, -33, 16), (-110, -31, 14.8)],
    [(-88, -35.2, 20), (-104, -34, 16), (-120, -31, 14.8)],
    [(-92, -35.2, 20), (-112, -35, 16), (-130, -30, 14.8)],
    # ⑧ ESP32 → LED（2 根）：跨继电器上方，避开屏架
    [(-71.0, -50, 24), (-58, -38, 20), (-40, -15, 22), (-26, 8, 18), (-23, 15, 10)],
    [(-71.0, -53, 24), (-59, -41, 20), (-41, -18, 22), (-27, 6, 18), (-24, 13, 10)],
    # ⑨ 面包板 → 继电器供电（2 根）
    [(-92, -29, 14.8), (-74, -26, 17), (-58, -29, 24)],
    [(-98, -29, 14.8), (-76, -27, 17), (-56, -29, 25)],
    # ⑩ 浮球开关 → GPIO32（2 根）：本体顶部出线，走桶 -Y 侧（与电缆同侧）回面包板
    [(95, 32, 144), (100, 24, LID_TOP + 6), (100, -12, LID_TOP + 4), (90, -42, LID_TOP + 3), (79, -52, 112),
     (55, -56, 72), (20, -56, 38), (-20, -52, 25), (-60, -60, 18), (-90, -66, 16)],
    [(96, 33, 141), (102, 25, LID_TOP + 5), (102, -13, LID_TOP + 4), (92, -44, LID_TOP + 3), (81, -54, 112),
     (58, -58, 72), (23, -58, 38), (-17, -54, 25), (-57, -62, 18), (-87, -68, 16)],
]
for k, w in enumerate(WIRES):
    add(wire(w), "wire", "跳线%02d" % (k + 1))



# ============================================================
# 烘焙 AO（环境光遮蔽）—— 一次算好，PNG 渲染与 HTML 共用
#   面级余弦半球采样 + 邻面平滑；结果缓存到 ao_cache.npz
# ============================================================
AO_LIST = None
AO_CACHE = os.path.join(HERE, "ao_cache.npz")


def _scene_sig(meshes):
    b = trimesh.util.concatenate(meshes).bounds.ravel()
    return "%d_%s" % (sum(len(m.faces) for m in meshes),
                      "_".join("%.2f" % v for v in b))


def bake_ao(meshes, rays=12):
    """返回每个 mesh 的逐面 AO（1=完全受光，0=完全遮蔽）"""
    sig = _scene_sig(meshes)
    if os.path.exists(AO_CACHE):
        try:
            z = np.load(AO_CACHE, allow_pickle=True)
            if str(z["sig"]) == sig:
                print("AO 命中缓存")
                return [z["a%d" % i] for i in range(len(meshes))]
        except Exception:
            pass

    scene = trimesh.util.concatenate(meshes)
    tri = scene.triangles
    cen = tri.mean(axis=1)
    nrm = scene.face_normals
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)

    # 每个面一套切线基
    up = np.where(np.abs(nrm[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]]))
    t = np.cross(up, nrm); t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    b = np.cross(nrm, t)

    rng = np.random.default_rng(7)
    ga = np.pi * (3.0 - np.sqrt(5.0))
    acc = np.zeros(len(cen))
    for k in range(rays):
        r = np.sqrt((k + 0.5) / rays)
        phi = ga * k
        d = (t * (np.cos(phi) * r) + b * (np.sin(phi) * r)
             + nrm * float(np.sqrt(max(0.0, 1.0 - r * r))))
        d += rng.normal(scale=0.02, size=d.shape)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        o = cen + nrm * 0.25
        acc += scene.ray.intersects_any(o, d)
    ao = 1.0 - acc / rays

    # 邻面平滑 2 轮，压掉采样噪点
    adj = scene.face_adjacency
    for _ in range(2):
        s = ao.copy(); c = np.ones_like(ao)
        np.add.at(s, adj[:, 0], ao[adj[:, 1]]); np.add.at(c, adj[:, 0], 1)
        np.add.at(s, adj[:, 1], ao[adj[:, 0]]); np.add.at(c, adj[:, 1], 1)
        ao = s / c
    ao = np.clip(ao, 0.05, 1.0)

    # 切回每个 mesh
    out, i0 = [], 0
    for m in meshes:
        n = len(m.faces)
        out.append(ao[i0:i0 + n]); i0 += n
    try:
        np.savez_compressed(AO_CACHE, sig=sig, **{"a%d" % i: a for i, a in enumerate(out)})
    except Exception as e:
        print("AO 缓存写入失败:", e)
    return out


def get_ao():
    """逐面 AO；大面积面（>120mm²）用该件中位数，避免"皱纸"斑块"""
    global AO_LIST
    if AO_LIST is None:
        meshes = [m for m, _, _ in items]
        raw_ao = bake_ao(meshes)
        AO_LIST = []
        # 结构件（大而简单）：AO 压缩到 0.80~1.0，只留微弱层次。
        # 原因：布尔会把大平面切成大量碎片面，逐面 AO 会形成"皱纸"斑块；
        # 细节件（螺丝/排针/跳线/孔阵）保留全强度，小特征才读得出来。
        STRUCT = ("底盘", "花盆", "土壤", "水箱", "水体", "面包板", "ESP32", "继电器",
                  "OLED 45°支架", "DHT11 座", "扎线座", "连接块", "水泵", "水泵固定座",
                  "土壤传感器板", "传感器盆沿挂钩", "水管末端夹", "水管",
                  "水箱盖", "浮球", "浮子")
        for (m, ck, nm), a in zip(items, raw_ao):
            a = np.array(a, dtype=float).copy()
            if (nm or "").startswith(STRUCT):
                a = 0.80 + 0.20 * a
            else:
                a = np.clip(a, 0.12, 1.0)
            AO_LIST.append(a)
    return AO_LIST


def render_scene(azim=42.0, elev=26.0, size=1100, bg=(1, 1, 1)):
    tri_list, col_list = [], []
    light = np.array([0.40, 0.55, 0.73])
    light /= np.linalg.norm(light)
    ao_all = get_ao()
    for idx, (mesh, ck, _) in enumerate(items):
        n = mesh.face_normals
        ao = ao_all[idx]
        shade = 0.46 * ao + 0.54 * np.clip(n @ light, 0, 1) * (0.75 + 0.25 * ao)
        tri_list.append(mesh.triangles)
        col_list.append(np.array(C[ck])[None, :] * shade[:, None])
    tris = np.concatenate(tri_list)
    cols = np.concatenate(col_list)

    a, e = np.deg2rad(azim), np.deg2rad(elev)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross([0, 0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)

    v = tris.reshape(-1, 3)
    tx = (v @ right).reshape(-1, 3)
    ty = (v @ up).reshape(-1, 3)
    tz = (v @ fwd).reshape(-1, 3)
    x0m, x1m, y0m, y1m = tx.min(), tx.max(), ty.min(), ty.max()
    pad = 0.05 * max(x1m - x0m, y1m - y0m)
    sc = (size - 1) / max(x1m - x0m + 2 * pad, y1m - y0m + 2 * pad)
    sx = (tx - x0m + pad) * sc
    sy = (size - 1) - (ty - y0m + pad) * sc

    img = np.ones((size, size, 3), dtype=np.float32) * np.array(bg)
    zbuf = np.full((size, size), -1e9, dtype=np.float32)
    for i in np.argsort(tz.min(axis=1)):
        ax0, ay0, az = sx[i], sy[i], tz[i]
        bx0 = max(int(np.floor(ax0.min())), 0)
        bx1 = min(int(np.ceil(ax0.max())), size - 1)
        by0 = max(int(np.floor(ay0.min())), 0)
        by1 = min(int(np.ceil(ay0.max())), size - 1)
        if bx1 < bx0 or by1 < by0:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1 + 1), np.arange(by0, by1 + 1))
        d = (ax0[1] - ax0[0]) * (ay0[2] - ay0[0]) - (ax0[2] - ax0[0]) * (ay0[1] - ay0[0])
        if abs(d) < 1e-12:
            continue
        w0 = ((ax0[1] - gx) * (ay0[2] - gy) - (ax0[2] - gx) * (ay0[1] - gy)) / d
        w1 = ((ax0[2] - gx) * (ay0[0] - gy) - (ax0[0] - gx) * (ay0[2] - gy)) / d
        w2 = 1.0 - w0 - w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not ins.any():
            continue
        depth = w0 * az[0] + w1 * az[1] + w2 * az[2]
        sub_z = zbuf[by0:by1 + 1, bx0:bx1 + 1]
        closer = ins & (depth > sub_z)
        if not closer.any():
            continue
        sub_z[closer] = depth[closer]
        img[by0:by1 + 1, bx0:bx1 + 1][closer] = cols[i]
    return np.clip(img, 0, 1)


def main():
    scene = trimesh.Scene()
    for i, (mesh, ck, nm) in enumerate(items):
        m = mesh.copy()
        col = np.array(list(C[ck]) + [1.0])
        ao = get_ao()[i]
        face_col = np.tile(col, (len(m.faces), 1))
        face_col[:, :3] *= (0.35 + 0.65 * ao)[:, None]
        m.visual = trimesh.visual.ColorVisuals(mesh=m, face_colors=face_col)
        scene.add_geometry(m, geom_name=f"{i:02d}_{nm or ck}")

    glb = os.path.join(HERE, "花房整机示意模型.glb")
    with open(glb, "wb") as f:
        f.write(trimesh.exchange.gltf.export_glb(scene))
    print("glb: %s  %.2f MB  几何体 %d 个" % (glb, os.path.getsize(glb) / 1024 / 1024, len(items)))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    views = [((42, 26), "整体轴测  42°/26°"),
             ((8, 16), "正前视角  8°/16°"),
             ((0, 89.5), "俯视 TOP"),
             ((-58, 24), "左后轴测  −58°/24°")]

    for (az, el), _ in views:
        plt.imsave(os.path.join(OUT_PREVIEW, f"view_az{az:+.0f}_el{el:+.0f}.png"),
                   render_scene(az, el, 1000))

    fig, axes = plt.subplots(2, 2, figsize=(16, 16), facecolor="white")
    for ax, ((az, el), name) in zip(axes.ravel(), views):
        ax.imshow(render_scene(az, el, 780))
        ax.set_title(name, fontsize=15, color="#222")
        ax.axis("off")
    fig.suptitle("智能花房养护站 Smart GreenHouse · 整机示意图", fontsize=20, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT_PREVIEW, "00_整机四视图.png"), dpi=150, facecolor="white")
    plt.close(fig)
    print("preview:", OUT_PREVIEW)


if __name__ == "__main__":
    main()
