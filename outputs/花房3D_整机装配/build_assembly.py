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
    # —— 水系统 ——
    "tank": (0.659, 0.824, 0.910),    # 水箱（浅青）
    "water": (0.247, 0.557, 0.839),   # 水体（中蓝）
    "pump": (0.420, 0.447, 0.502),    # 水泵（岩灰）
    "tube": (0.059, 0.604, 0.659),    # 水管（青绿）
}


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


def tube_path(points, r=4.0):
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
POT = (-105.0, 60.0)
R_BOT, R_TOP, POT_H, FLOOR = 29.0, 41.0, 85.0, 3.0
pot = trimesh.boolean.difference(
    [frustum(R_BOT, R_TOP, POT_H), place(frustum(24.0, 37.0, POT_H - FLOOR), 0, 0, FLOOR)],
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

# ---------- 4. 水箱 (前壁剖开, 露出内部水泵) ----------
TANK = (85.0, 20.0)
TW, TD, TH, TT = 118.0, 90.0, 60.0, 3.0
parts = [
    place(box([TW, TT, TH]), 0, TD / 2 - TT / 2, TH / 2),
    place(box([TT, TD - TT, TH]), -TW / 2 + TT / 2, -TT / 2, TH / 2),
    place(box([TT, TD - TT, TH]), TW / 2 - TT / 2, -TT / 2, TH / 2),
    place(box([TW, TD, TT]), 0, 0, TT / 2),
]
tank = trimesh.boolean.union(parts, engine="manifold")
add(place(tank, TANK[0], TANK[1], 3.0), "tank", "水箱")
water = box([TW - 2 * TT, TD - 2 * TT, 20.0])
add(place(water, TANK[0], TANK[1] - 1.0, 3.0 + TT + 10.0), "water", "水体")

# ---------- 5. 水泵座 + 水泵 ----------
PUMP = (85.0, 8.0)
add(place(M_P0.build_pump_mount(M_P0.PARAMS["pump"]), PUMP[0], PUMP[1], 3.0 + TT), "white", "水泵固定座")
add(place(cylinder(radius=19.0, height=26.0, sections=64), PUMP[0], PUMP[1], 3.0 + TT + 16.0),
    "pump", "水泵")
add(place(cylinder(radius=12.0, height=4.0, sections=64), PUMP[0], PUMP[1], 3.0 + TT + 31.0),
    "pump", "泵头")

# ---------- 6. 水管 ----------
tube_pts = [
    (85.0, 8.0, 39.0),        # 泵顶出水
    (85.0, 8.0, 58.0),
    (58.0, 8.0, 70.0),
    (15.0, 10.0, 70.0),       # 越过水箱壁 (壁高 62, 走 70)
    (-25.0, 30.0, 55.0),
    (-52.0, 42.0, 80.0),
    (-46.0, 56.0, 112.0),     # 绕到夹子外侧再抬高
    (-65.5, 58.4, 112.0),     # 从正上方对准管孔 (夹子顶面 103)
    (-65.5, 58.4, 96.0),      # 垂直穿进管孔
    (-74.0, 51.0, 87.0),      # 出孔后立刻向内收 (避开夹爪内侧面)
    (-78.0, 50.0, 80.0),
]
add(tube_path(tube_pts, r=4.0), "tube", "水管")

# ---------- 7. 土壤传感器: 盆沿挂钩式 (不在盆里立着) ----------
RIM_R = (37.0 + 41.0) / 2          # 盆沿壁中线半径(内37/外41)
RIM_Z = 2.0 + POT_H                 # 盆沿顶面 = 87
PLANT_AZ = np.degrees(np.arctan2(PLANT[1] - POT[1], PLANT[0] - POT[0]))
AZ = PLANT_AZ + 180.0               # 挂在植株对面
rim_pt = (POT[0] + RIM_R * np.cos(np.deg2rad(AZ)),
          POT[1] + RIM_R * np.sin(np.deg2rad(AZ)))

hook, gc, haxis = M_P0B.build()
hook_rot = trimesh.transformations.rotation_matrix(np.deg2rad(AZ - 90.0), [0, 0, 1])
hook.apply_transform(hook_rot)
hook.apply_translation([rim_pt[0], rim_pt[1], RIM_Z])   # 局部 z=0 = 盆沿顶面
add(hook, "white", "传感器盆沿挂钩")

brow = M_P0B.board_mesh(gc=gc, axis=haxis)
brow.apply_transform(hook_rot)
brow.apply_translation([rim_pt[0], rim_pt[1], RIM_Z])
add(brow, "pcb_green", "土壤传感器板")

# ---------- 8. P0: 水管末端固定夹 ----------
add(place(M_P0.build_tube_clip(M_P0.PARAMS["clip"]), -69.6, 47.1, 69.0, rz=-20), "white",
    "水管末端夹")

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
add(place(box([84.0, 55.0, 10.0]), -105.0, -55.0, SEAT + 5.0), "breadboard", "面包板")
add(place(box([55.0, 28.0, 11.0]), -100.0, -50.0, SEAT + 10.0 + 5.5), "mcu", "ESP32")
add(place(box([34.0, 25.0, 15.0]), -45.0, -20.0, SEAT + 7.5), "relay", "继电器")

# ---------- 12. P2: DHT11 座 + 模块 ----------
# DHT11 从 (-52,92) 移到 (-45,-60)：原位置正对屏幕视线, 正面遮挡 42%/高角度 47%
DHT = (-45.0, -60.0)
add(place(M_P1.build_dht_holder(M_P1.PARAMS["dht"]), DHT[0], DHT[1], PT), "white", "DHT11 座")
add(place(box([29.0, 12.0, 7.0]), DHT[0], DHT[1] - 17.0 + 9.0, PT + 55.0 + 9.0), "pcb_green", "DHT11")

# ---------- 13. P2: 扎线固定座 ----------
add(place(M_P1.build_cable_clip(M_P1.PARAMS["clip3"]), -75.0, 8.0, PT, rz=8), "white", "扎线座")


# ============================================================
def render_scene(azim=42.0, elev=26.0, size=1100, bg=(1, 1, 1)):
    tri_list, col_list = [], []
    light = np.array([0.40, 0.55, 0.73])
    light /= np.linalg.norm(light)
    for mesh, ck, _ in items:
        n = mesh.face_normals
        shade = 0.42 + 0.58 * np.clip(n @ light, 0, 1)
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
        m.visual = trimesh.visual.ColorVisuals(mesh=m, face_colors=np.tile(col, (len(m.faces), 1)))
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
