# -*- coding: utf-8 -*-
"""
花房 Final Project · P1 + P2 三件参数化建模脚本 (v1 占位版)
------------------------------------------------------------
P1 (答辩加分件): 04 OLED 45°斜面支架
   (05 双色LED灯罩 / 06 整合底板 已作废删除: 05 无半透明耗材取消, 06 被两片式底盘取代)
P2 (时间富余件): 07 DHT11 小座 / 08 扎线固定座

产出: STL (mm) + 三视图预览 + 校验数据

设计原则同 P0 批次:
1. 尺寸全集中在 PARAMS, 到货实测后只改数字重跑
2. 全部走 manifold 布尔, 保证 watertight / 单体 / z_min=0
3. 打印朝向即建模朝向 (Z 向上); 免支撑优先
"""
import os
import json
import numpy as np
import trimesh
import trimesh.transformations as tft
from trimesh.creation import box, cylinder, icosphere
from trimesh.boolean import difference, union

OUT = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(OUT, "STL")
PREVIEW_DIR = os.path.join(OUT, "preview")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# ============================================================
# 参数区
# ============================================================
PARAMS = {
    # ---------- 件 4: OLED 45 度斜面支架 ----------
    "oled": {
        "oled_w": 26.9,          # [实测 2026-11-08] 模块宽
        "oled_h": 28.5,          # [实测 2026-11-08] 模块高（丝印正读方向）
        "pcb_t": 1.6,            # [市售常见值 PCB 厚]
        "tilt": 45.0,            # 屏面倾角 [设计决策: 隔桌可读]
        "base_x": 36.0,          # 底盘宽
        "base_y": 34.0,          # 底盘深
        "base_t": 3.0,           # 底盘厚
        "slope_y": 26.5,         # 斜面投影深度（24→26.5：加长斜面给下沿留挡边）
        "slope_z": 26.5,         # 斜面投影高度
        "pocket_clear": 0.5,     # 板槽单边间隙 [实测 2026-11-08]
        "pocket_depth": 2.4,     # 板槽深 (= PCB 1.6 + 余量), 板面与斜面齐平
        "open_ext": 0.5,         # 板槽下端延长（下端做挡边防板下滑）
        # ---- 2026-11-07 走线位（原设计板背只留 0.8mm，排针+杜邦头塞不进）----
        "leg_h": 10.0,           # 腿高：底座抬高，排针/杜邦头从底座下方出线
        "leg_w": 8.0,            # 腿截面
        "lift": 0.0,             # 模块沿斜面上移量（斜面已加长，靠斜面自身留挡边）
        # 2026-11-08 实测：排针在**上缘**（丝印正读时），过线口改到上缘、从托背上方穿出
        "wire_w": 13.0,          # 排针过线口宽（4P 排针 10.2 + 余量）
        "wire_len": 5.5,         # 过线口沿斜面长度（覆盖上缘挡边）
        "wire_depth": 14.0,      # 过线口深度（打穿上缘并通到托背外）
        "claw_x": 10.5,          # 防脱爪横向位置（让开中间 13 宽的过线口）
    },
    # ---------- 件 5: 双色 LED 灯罩 [已作废删除 2026-10-20: 无半透明耗材, 项目取消] ----------
    # ---------- 件 6: 整合底板 [已作废删除 2026-10-20: 被两片式底盘 06a/06b/06c 取代] ----------
    # ---------- 件 7: DHT11 小座 ----------
    # 2026-11-07 改版（领导：原造型太丑）：
    #   原版 = 10×10 细方杆 + 35×18 平板头 + 三角撑，头底还有 12.5mm 悬空（免支撑打不好）。
    #   新版 = 台锥底座 + 16→12.5 收腰柱 + 45° 喇叭口展开到托盘（把悬空变成斜裙）。
    "dht": {
        "mod_w": 30.0,           # [市售常见值 DHT11 模块板宽, 实物卡尺待测]
        "mod_h": 13.0,           # [市售常见值 模块板深]
        "mod_t": 1.6,
        "base_bot": 28.0,        # 底座下平面（台锥小端）
        "base_top": 34.0,        # 底座上平面（台锥大端）
        "base_t": 4.5,           # 底座高（33.7° 斜面，免支撑）
        "post_b": 16.0,          # 柱底截面
        "post_t": 12.5,          # 柱顶截面（收腰 2.4°）
        "head_w": 35.0,          # 托盘宽（比模块宽 30 每侧留 2.05 壁）
        "head_d": 18.0,          # 托盘深
        "head_t": 4.3,           # 托盘厚
        "total_h": 62.8,         # 总高（与旧版一致，装配不用重摆）
        "pocket_clear": 0.9,
        "pocket_depth": 2.5,     # 模块 1.6 厚, 槽深 2.5 留 0.9 余量
        "wire_w": 12.0,          # 背面过线口宽
        "wire_d": 5.2,           # 过线口深（切穿背壁）
        "wire_h": 4.8,           # 过线口高
    },
    # ---------- 件 8: 扎线固定座 ----------
    "clip3": {
        "n": 3,                  # 线槽数
        "pitch": 9.0,            # 槽间距
        "body_h": 14.0,          # 座体高
        "body_y": 12.0,          # 座体深
        "pad_h": 16.0,           # 底座高 (含边缘余量)
        "wire_d": 5.5,           # 线孔直径 [市售常见值 杜邦线/硅胶线束 5~6]
        "neck_w": 3.4,           # 顶部收口宽 < 线径 => 卡进去不脱 [公差]
        "base_t": 2.0,
    },
    # ---------- 件 11: 光敏电阻小柱（2026-11-08 新增） ----------
    # 光敏模块是 4P 板（VCC/GND/AO/DO，DO 不接），板上无安装孔 → 用托盘 + 卡边。
    # 放在花盆脚边 (-110,-5)：到 ESP32 约 50mm，离双色 LED 90mm，上方无遮挡。
    "ldr": {
        "mod_w": 32.0,           # [市售常见值 光敏模块板宽，实物卡尺待测]
        "mod_d": 14.0,           # 板深
        "mod_t": 1.6,
        "base_bot": 24.0,
        "base_top": 30.0,
        "base_t": 4.0,
        "post_b": 11.0,
        "post_t": 10.0,
        "post_top": 26.0,        # 柱顶中心高度（45° 斜切成托盘的支撑面）
        "head_w": 34.0,
        "head_d": 18.0,
        "head_t": 4.2,
        "tilt": 45.0,            # 托盘仰角（与屏架同语言）
        "pocket_clear": 0.6,     # 单边间隙
        "pocket_depth": 2.6,     # 板 1.6 + 1.0
        "pin_slot_w": 12.0,      # 排针过线槽宽（4P 10.2 + 余量）
        "pin_slot_l": 4.5,       # 槽沿斜面长度（排针段 2.54 + 余量）
        "head_shift": 0.0,       # [弃用] 试过 1.4 会让托盘与柱分离（bodies=2）
    },
}


# ============================================================
# 几何基元
# ============================================================
def B(cx, cy, cz, sx, sy, sz):
    m = box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, cz])
    return m


def C(cx, cy, cz, r, h, axis="z", sections=64):
    m = cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        m.apply_transform(tft.rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == "y":
        m.apply_transform(tft.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([cx, cy, cz])
    return m


def _prism(pts, axis, a0, a1):
    p = np.asarray(pts, dtype=float)
    n = len(p)

    def mk(a, q):
        if axis == "x":
            return np.column_stack([[a] * n, q[:, 0], q[:, 1]])
        return np.column_stack([q[:, 0], [a] * n, q[:, 1]])

    v = np.vstack([mk(a0, p), mk(a1, p)])
    f = []
    for i in range(1, n - 1):
        f.append([0, i + 1, i])
        f.append([n, n + i, n + i + 1])
    for i in range(n):
        j = (i + 1) % n
        f.append([i, j, n + j])
        f.append([i, n + j, n + i])
    m = trimesh.Trimesh(vertices=v, faces=np.asarray(f), process=True)
    m.fix_normals()
    return m


def prism_yz(pts, x0, x1):
    return _prism(pts, "x", x0, x1)


def prism_xz(pts, y0, y1):
    return _prism(pts, "y", y0, y1)


def cut(base, cutters):
    return difference([base] + list(cutters), engine="manifold")


def add(base, parts):
    return union([base] + list(parts), engine="manifold")


def frame_part(mesh, deg_x, origin):
    """把在局部坐标 (z=0 为贴合面, +z 朝外) 建好的几何, 绕 X 转 deg_x 后移到 origin"""
    m = mesh.copy()
    m.apply_transform(tft.rotation_matrix(np.deg2rad(deg_x), [1, 0, 0]))
    m.apply_translation(origin)
    return m


# ============================================================
# 件 4: OLED 45 度斜面支架
# ============================================================
def build_oled_stand(p):
    bx, by, bt = p["base_x"], p["base_y"], p["base_t"]
    sy, sz = p["slope_y"], p["slope_z"]
    z0 = p["leg_h"]                # 腿高：底座抬离板面，排针+杜邦头从下方出线
    lip = 4.0                      # 斜面下沿距底盘前缘的距离, 避免刀口
    ang = -45.0

    # ---- 1) 底座抬升 10mm：周边裙墙 + 两条内筋 ----
    # 不用四条腿：36×34 的底板底面会变成悬空天花，免支撑打不出来。
    # 裙墙 + 内筋把底面分成 ≤14mm 的小格，全是垂直壁 + 短桥，免支撑可打；
    # 背面裙墙留 13×7 过线口，线从底座下往后出。
    h = z0
    skirt_t = 3.0
    fin_x = 8.5
    outer = B(0, 0, h / 2, bx, by, h)
    inner = B(0, 0, h / 2, bx - 2 * skirt_t, by - 2 * skirt_t, h + 2)
    plinth = cut(outer, [inner])
    plinth = add(plinth, [B(sx * fin_x, 0, h / 2 + 0.3, skirt_t,
                            by - 2 * skirt_t, h + 0.6) for sx in (-1, 1)])
    # 背面过线口（13 宽 × 7 高），与底座竖槽同宽
    wire_gate = B(0, -by / 2 + skirt_t / 2, 3.5, p["wire_w"], skirt_t + 2, 7.0)
    plinth = cut(plinth, [wire_gate])

    # ---- 2) 底盘 + 楔块（整体抬到腿上，打印仍 z_min=0） ----
    body = B(0, 0, z0 + bt / 2, bx, by, bt)

    # 楔块: 先单独切出 45 度斜面, 再与底盘合并 —— 否则切刀会把底盘一起削掉
    wedge = B(0, 0, z0 + bt + sz / 2, bx, by, sz)
    plane_pt = np.array([0.0, by / 2 - lip, z0 + bt])          # 斜面下沿点
    cutter = B(0, 0, 30.0, 120, 120, 60)                  # 局部 z 0..60
    cutter = frame_part(cutter, ang, plane_pt)
    wedge = cut(wedge, [cutter])
    body = add(body, [wedge])
    body = add(body, [plinth])

    # 斜面参数（模块沿斜面整体上移 lift：下沿留 8.7mm 挡边，排针处才有材料开过线口）
    n = np.array([0.0, np.sin(np.deg2rad(45)), np.cos(np.deg2rad(45))])   # 斜面法线(朝上前)
    up = np.array([0.0, -np.sin(np.deg2rad(45)), np.cos(np.deg2rad(45))])  # 上坡方向
    slope_mid = plane_pt + np.array([0, -sy / 2, sz / 2]) + up * p["lift"]  # 斜面中点

    # ---- 3) 板槽: 局部 z=0 为斜面, 向材料内切 pocket_depth; 下端挡边 0.6 防板下滑 ----
    pw = p["oled_w"] + p["pocket_clear"]
    d = p["pocket_depth"]
    pocket_len = p["oled_h"] + p["pocket_clear"] + p["open_ext"]
    upslope_edge = -(p["oled_h"] + p["pocket_clear"]) / 2                 # 板槽上坡端
    pocket = B(0, upslope_edge + pocket_len / 2, 0, pw, pocket_len, d * 2)
    pocket = frame_part(pocket, ang, slope_mid)
    body = cut(body, [pocket])

    # ---- 4) ★ 排针过线位（2026-11-08 实测：4 针在模块**上缘**）----
    # 上缘挡边 + 托盘顶面开 13 宽缺口 → 排针塑壳 + 杜邦头从托盘背上方穿出，线沿屏背往电子件走
    strip = B(0, -((p["oled_h"] + p["pocket_clear"]) / 2) + 1.0,
              1.0 - (1.0 + p["wire_depth"]) / 2,
              p["wire_w"], p["wire_len"], 1.0 + p["wire_depth"])
    body = cut(body, [frame_part(strip, ang, slope_mid)])

    # ---- 5) 防脱卡爪（外移让开中间过线口；上坡端两只 1.2mm 弹性爪）----
    claw_h, claw_w, claw_over = 1.2, 4.0, 1.5
    claws = []
    for sx in (-1, 1):
        c = B(sx * p["claw_x"], upslope_edge + claw_over / 2, -claw_h / 2 + 0.2,
              claw_w, claw_over + 1.2, claw_h)
        claws.append(frame_part(c, ang, slope_mid))
    body = add(body, claws)
    return body


# ============================================================
# 件 5: 双色 LED 灯罩 [已作废删除 2026-10-20]
# 件 6: 整合底板 [已作废删除 2026-10-20]
# 建模函数已随作废件一并移除; 历史版本见 git 记录 (回收站 D:\workbuddy_recycle_bin_花房清理)
# ============================================================


# ============================================================
# 件 7: DHT11 小座
# ============================================================
def loft_rect(z0, z1, w0, d0, w1, d1, cx=0.0, cy=0.0):
    """矩形截面的直纹放样（下 w0×d0 → 上 w1×d1），用于台锥/收腰/喇叭口"""
    v = np.array([
        [cx - w0 / 2, cy - d0 / 2, z0], [cx + w0 / 2, cy - d0 / 2, z0],
        [cx + w0 / 2, cy + d0 / 2, z0], [cx - w0 / 2, cy + d0 / 2, z0],
        [cx - w1 / 2, cy - d1 / 2, z1], [cx + w1 / 2, cy - d1 / 2, z1],
        [cx + w1 / 2, cy + d1 / 2, z1], [cx - w1 / 2, cy + d1 / 2, z1],
    ])
    f = np.array([
        [0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7],
    ])
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    m.fix_normals()
    return m


def build_dht_holder(p):
    """台锥底座 → 收腰柱 → 45° 喇叭口 → 托盘（2026-11-07 重做造型）"""
    H = p["total_h"]
    bt, b0, b1 = p["base_t"], p["base_bot"], p["base_top"]
    pb, pt_ = p["post_b"], p["post_t"]
    hw, hd, ht = p["head_w"], p["head_d"], p["head_t"]
    flare_h = (hw - pt_) / 2.0                 # x 向 45°（略小于 45，斜裙自支撑）
    z_flare = H - ht - flare_h                 # 喇叭口起点

    body = loft_rect(0.0, bt, b0, b0, b1, b1)                                  # 台锥底座
    body = add(body, [loft_rect(bt - 0.3, z_flare + 0.3, pb, pb, pt_, pt_)])   # 收腰柱
    body = add(body, [loft_rect(z_flare - 0.3, z_flare + flare_h + 0.3,
                                pt_, pt_, hw, hd)])                            # 喇叭口
    body = add(body, [B(0, 0, H - ht / 2 - 0.15, hw, hd, ht + 0.3)])           # 托盘

    # 模块沉槽（朝上敞开）
    pocket = B(0, 0, H - p["pocket_depth"] / 2 + 0.5,
               p["mod_w"] + p["pocket_clear"], p["mod_h"] + p["pocket_clear"],
               p["pocket_depth"] + 1.0)
    body = cut(body, [pocket])
    # 背面过线口（切穿背壁，杜邦头能退出）
    body = cut(body, [B(0, -hd / 2 + p["wire_d"] / 2, H - p["wire_h"] / 2 - 0.2,
                        p["wire_w"], p["wire_d"], p["wire_h"] + 1.0)])
    return body


# ============================================================
# 件 8: 扎线固定座
# ============================================================
def build_ldr_stand(p):
    """光敏电阻小柱（2026-11-08）：台锥底 + 收腰柱 + 45° 斜面托盘（排针从上缘穿出）"""
    b0, b1, bt = p["base_bot"], p["base_top"], p["base_t"]
    pb, pt_ = p["post_b"], p["post_t"]
    ztop = p["post_top"]
    hw, hd, ht = p["head_w"], p["head_d"], p["head_t"]
    ang = -p["tilt"]
    n = np.array([0.0, np.sin(np.deg2rad(p["tilt"])),
                  np.cos(np.deg2rad(p["tilt"]))])

    body = loft_rect(0.0, bt, b0, b0, b1, b1)                                  # 台锥底座
    body = add(body, [loft_rect(bt - 0.3, ztop + 1.0, pb, pb, pt_, pt_)])      # 收腰柱（试过前移 2 会与托盘分离，回退）

    # 柱顶沿托盘底面 45° 切平（托盘底下是 45° 斜面，免支撑）
    head_c = np.array([0.0, 0.0, ztop])                    # 托盘中心
    head_c = head_c + np.array([0.0, np.sin(np.deg2rad(p["tilt"])),
                                -np.cos(np.deg2rad(p["tilt"]))]) * p["head_shift"]
    plane_pt = head_c - n * (ht / 2)
    cutter = B(0, 0, 30.0, 120, 120, 60)
    body = cut(body, [frame_part(cutter, ang, plane_pt)])

    # 托盘
    body = add(body, [frame_part(B(0, 0, 0, hw, hd, ht), ang, head_c)])

    # 模块沉槽（板 32×14，单边留 0.6）
    pocket = B(0, 0, ht / 2 - p["pocket_depth"] / 2 + 0.5,
               p["mod_w"] + 2 * p["pocket_clear"],
               p["mod_d"] + 2 * p["pocket_clear"],
               p["pocket_depth"] + 1.0)
    body = cut(body, [frame_part(pocket, ang, head_c)])

    # 上缘排针过线槽（4P 塑壳 2.5 + 杜邦头 2.5 从托盘背面穿出，落在托盘后上方空中）
    slot = B(0, -(p["mod_d"] / 2 - p["pin_slot_l"] / 2 + 1.0), 0,
             p["pin_slot_w"], p["pin_slot_l"], ht + 2.0)
    body = cut(body, [frame_part(slot, ang, head_c)])
    return body


def build_cable_clip(p):
    n, pitch = p["n"], p["pitch"]
    bw = pitch * (n - 1) + pitch
    bh, by = p["body_h"], p["body_y"]
    bt = p["base_t"]

    body = B(0, 0, bt / 2, bw + 3, by + 4, bt)          # 底座
    body = add(body, [B(0, 0, bt + (bh - bt) / 2, bw, by, bh - bt)])

    r = p["wire_d"] / 2
    cz = bh - r - 1.0
    cuts = []
    for i in range(n):
        x = (i - (n - 1) / 2) * pitch
        cuts.append(C(x, 0, cz, r, by + 6, axis="y"))                    # 线孔
        cuts.append(B(x, 0, (cz + r + bh) / 2, p["neck_w"], by + 6,
                      bh - (cz + r) + 2))                                # 顶部收口槽
    body = cut(body, cuts)
    return body


# ============================================================
# 校验 / 渲染
# ============================================================
def validate(mesh, name):
    parts = mesh.split(only_watertight=False)
    return {
        "name": name,
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": round(float(mesh.volume), 1),
        "triangles": int(len(mesh.faces)),
        "bodies": len(parts),
        "bbox_mm": [round(float(x), 2) for x in mesh.extents],
        "z_min": round(float(mesh.bounds[0][2]), 3),
        "est_mass_g_PLA": round(float(mesh.volume) * 1.24 / 1000, 1),
    }


def render(mesh, azim=45.0, elev=28.0, size=900, base_color=(0.62, 0.70, 0.80)):
    tris = mesh.triangles
    n = mesh.face_normals
    a, e = np.deg2rad(azim), np.deg2rad(elev)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross([0, 0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)

    v = tris.reshape(-1, 3)
    tx = (v @ right).reshape(-1, 3)
    ty = (v @ up).reshape(-1, 3)
    tz = (v @ fwd).reshape(-1, 3)

    xmin, xmax, ymin, ymax = tx.min(), tx.max(), ty.min(), ty.max()
    pad = 0.06 * max(xmax - xmin, ymax - ymin)
    sc = (size - 1) / max(xmax - xmin + 2 * pad, ymax - ymin + 2 * pad)
    sx = (tx - xmin + pad) * sc
    sy = (size - 1) - (ty - ymin + pad) * sc

    light = np.array([0.35, 0.55, 0.76])
    light /= np.linalg.norm(light)
    shade = 0.32 + 0.68 * np.clip(n @ light, 0, 1)
    colors = np.array(base_color)[None, :] * shade[:, None]

    img = np.ones((size, size, 3), dtype=np.float32)
    zbuf = np.full((size, size), -1e9, dtype=np.float32)
    for i in np.argsort(tz.min(axis=1)):
        x0, y0, x1 = sx[i], sy[i], tz[i]
        bx0 = max(int(np.floor(x0.min())), 0)
        bx1 = min(int(np.ceil(x0.max())), size - 1)
        by0 = max(int(np.floor(y0.min())), 0)
        by1 = min(int(np.ceil(y0.max())), size - 1)
        if bx1 < bx0 or by1 < by0:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1 + 1), np.arange(by0, by1 + 1))
        d = (x0[1] - x0[0]) * (y0[2] - y0[0]) - (x0[2] - x0[0]) * (y0[1] - y0[0])
        if abs(d) < 1e-12:
            continue
        w0 = ((x0[1] - gx) * (y0[2] - gy) - (x0[2] - gx) * (y0[1] - gy)) / d
        w1 = ((x0[2] - gx) * (y0[0] - gy) - (x0[0] - gx) * (y0[2] - gy)) / d
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        depth = w0 * x1[0] + w1 * x1[1] + w2 * x1[2]
        sub_z = zbuf[by0:by1 + 1, bx0:bx1 + 1]
        closer = inside & (depth > sub_z)
        if not closer.any():
            continue
        sub_z[closer] = depth[closer]
        img[by0:by1 + 1, bx0:bx1 + 1][closer] = colors[i]
    return np.clip(img, 0, 1)


def contact_sheet(mesh, name, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    views = [(render(mesh, 38, 26, 760), "轴测 ISO"),
             (render(mesh, 0, 89.5, 760), "俯视 TOP"),
             (render(mesh, 0, 0, 760), "正视 FRONT")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), facecolor="white")
    for ax, (im, t) in zip(axes, views):
        ax.imshow(im)
        ax.set_title(t, fontsize=13, color="#222")
        ax.axis("off")
    fig.suptitle(f"{name}   (mm, 打印朝向 Z↑)", fontsize=15, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def sheet_all(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, len(rows), figsize=(5 * len(rows), 5.4), facecolor="white")
    if len(rows) == 1:
        axes = [axes]
    for ax, (mesh, title, sub) in zip(axes, rows):
        ax.imshow(render(mesh, 38, 26, 700))
        ax.set_title(f"{title}\n{sub}", fontsize=11, color="#222")
        ax.axis("off")
    fig.suptitle(f"花房 P1+P2 {len(rows)} 件 v1 占位版  (单位 mm, Z↑ 打印朝向)", fontsize=15, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.86])
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


BUILDERS = [
    ("04_oled_stand", "OLED 45°斜面支架", build_oled_stand, PARAMS["oled"]),
    ("07_dht11_holder", "DHT11 小座", build_dht_holder, PARAMS["dht"]),
    ("08_cable_clip", "扎线固定座", build_cable_clip, PARAMS["clip3"]),
    ("11_ldr_stand", "光敏电阻小柱", build_ldr_stand, PARAMS["ldr"]),
]


def main():
    reports = []
    for key, cn, fn, p in BUILDERS:
        mesh = fn(p)
        mesh.merge_vertices()
        try:
            mesh.update_faces(mesh.nondegenerate_faces())
        except Exception:
            pass
        mesh.fix_normals()
        stl = os.path.join(STL_DIR, f"{key}_v1.stl")
        mesh.export(stl)
        rep = validate(mesh, f"{key} | {cn}")
        rep["stl"] = stl
        rep["preview"] = os.path.join(PREVIEW_DIR, f"{key}.png")
        contact_sheet(mesh, f"{key}  {cn}", rep["preview"])
        reports.append(rep)
        print(json.dumps(rep, ensure_ascii=False))

    with open(os.path.join(OUT, "check_report.json"), "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=1)

    print("\n=== 汇总 ===")
    for r in reports:
        flag = "OK " if (r["watertight"] and r["bodies"] == 1) else "!! "
        print(f"{flag}{r['name']}: bbox={r['bbox_mm']} ~{r['est_mass_g_PLA']}g "
              f"tri={r['triangles']} bodies={r['bodies']} watertight={r['watertight']}")

    rows = []
    for (key, cn, fn, p), r in zip(BUILDERS, reports):
        bx = r["bbox_mm"]
        rows.append((fn(p), cn, f"{bx[0]}×{bx[1]}×{bx[2]} mm   ~{r['est_mass_g_PLA']} g"))
    sheet_all(rows, os.path.join(PREVIEW_DIR, "00_P1P2_总览.png"))
    print("总览图:", os.path.join(PREVIEW_DIR, "00_P1P2_总览.png"))


if __name__ == "__main__":
    main()
