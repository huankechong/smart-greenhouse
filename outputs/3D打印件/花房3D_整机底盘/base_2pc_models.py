# -*- coding: utf-8 -*-
"""
花房 Final Project · 整机底盘 (两片式) 参数化建模 v1.2
====================================================
替代原 P1-6 "整合底板(电控托盘)" —— 底盘要托住花盆 + 水箱 + 电控, 一整块 320x230 超出
拓竹 X2D 床面 (256x256), 故拆成两片。

拼接方案: 直缝对接 + 2 颗 φ4 水平定位销 + 2 块顶部连接块 (各 4 颗自攻 M3)
  · 两片全是垂直壁 -> 免支撑
  · 自攻 M3 拧进 φ2.8 引导孔 -> 不需要螺母, 底板底面保持平整
  · 定位销跨缝 -> 拆装后可重复对准, 不靠手感

产出: 06a 左片 / 06b 右片 / 06c 连接块
"""
import os
import json
import numpy as np
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union

OUT = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(OUT, "STL")
PREVIEW_DIR = os.path.join(OUT, "preview")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# ============================================================
# 参数
# ============================================================
P = {
    # 总体
    "plate_x": 320.0,        # [设计决策] 概念模型取值; 可改, 布局不随动
    "plate_y": 230.0,
    "plate_t": 8.0,          # 底板厚 [v1.2: 6->8] 连接块要齐平, 沉槽 3.5 后仍需 4.5mm 咬合, 6mm 板做不到

    # 左片区 (x<0): 花盆 + 电控
    "pot_d": 82.0,           # 2026-11-12 领导：不要缩小 → 恢复 82（盆 80，单边 1.0）
    "pot_pos": (-111.0, 60.0),  # φ82 槽右缘 -70, 距继电器槽(-62)留 8mm; 原 -105 时仅 2mm 太薄
    "pot_depth": 6.0,           # 槽底仍 z=2 (板顶 8 - 6)
    "bb_w": 84.0,            # [市售常见值] 400 孔面包板 84x55
    "bb_h": 55.0,
    "bb_pos": (-110.0, -78.0),   # 2026-11-12 按手绘图：前·远（再往前 8）
    # ESP32 不单独开槽: 它插在面包板上(比躺在 1.5mm 浅槽里稳),
    # 原 (-45, 98) 的 55.6x28.6 槽一直是空的 -> v1.1 删除
    # [实测 2026-11-08] 继电器模块 26.2 × 50（JQC-3FF-S-Z 单路，带 4 位端子）
    # 横向 51 宽放不下（距面包板槽仅 0.2mm）→ 转 90°：26.2 沿 X、50 沿 Y
    "relay_w": 27.2,         # 2026-11-12 领导：不要缩小 → 恢复 27.2
    "relay_h": 51.0,         # 同上：恢复 51.0
    "relay_pos": (-48.0, -68.0),  # 2026-11-12 按手绘图：前·中
    "pocket_clear": 0.6,        # 2026-11-12 领导：不要缩小 → 恢复 0.6（面包板单边 0.3）
    "fit_clear": 0.2,           # 小件嵌槽间隙×2（0.2 = 单边 0.1）——2026-11-09 测试块实测：0.10/边最合适
    "mouth_chamfer": 0.0,       # 槽口导入斜口高度（0 = 直口，2026-11-12 领导定）
    "pocket_depth": 3.5,        # 槽底仍 z=4.5
    # ---- 2026-11-08 小件嵌槽（领导定：完全嵌平 = 槽深取件底座高度）----
    # (x, y, 槽宽, 槽深, 槽深Z, 绕Z旋转°)
    # 直壁槽（零件本身是直壁）：尺寸 = 件外廓 + 0.5（单边 0.25）
    "fits": [
        ("04 屏架", -45.0,  83.8, 36.0, 34.0, 3.0, 0.0),   # 2026-11-12 底端落在花盆**下侧**切线 y=100.9 上   # 底座裙墙 10 高，8mm 板只能沉 3
        # ("08 扎线", -77.0, 8.0, 30.0, 16.0, 2.0, 0.0),   # 2026-11-12 领导：理线器没用，槽**取消**（不再开）
        ("LED 模块", -14.0, 83.8, 18.8, 13.5, 1.6, 0.0),   # 2026-11-12 放在 oled 左侧（靠接缝），同排   # 模块 1.6 厚，齐平（-16→-14：倒角不与 04 槽相交）
    ],
    # 锥形槽（零件底座是倒四棱柱）：(名, x, y, 底宽, 顶宽, 高, 单边间隙)
    "fits_taper": [
        ("07 DHT",  -40.0, 0.0, 28.0, 34.0, 4.5, 0.10),  # 2026-11-12 oled 已后移，回到中排  # 33.7°（测试块定 0.10/边）
        ("11 光敏", -120.0, 0.0, 24.0, 30.0, 4.0, 0.10),   # 2026-11-12 按手绘图：中·远  # 36.9°（同上）
    ],

    # 右片区 (x>0): 水箱 —— 2026-10-20 改 1L 圆桶 (AR08)
    # 圆桶底径 105（2026-10-23 到货实测；商品页原标 106），原矩形槽 120.6×92.6 在
    # Y 向装不进去（105 > 92.6），故改为圆槽（径向余量 1mm）；槽心 +Y 移 12mm 让开 -Y 挡水堤。
    "tank_d": 106.6,         # 圆槽直径（2026-11-12 领导：实测偏松 → 107 → 106.6，桶底 106 单边 0.3）
   # 圆槽直径 = 桶底 105（实测）+ 2
    "tank_pos": (85.0, 32.0),
    "tank_depth": 5.0,          # 槽底仍 z=3

    # 槽底排水孔：水箱漏的水从这里穿板滴到桌面，不进电控区
    "drain_pos": (120.0, 52.0),
    "drain_d": 5.0,
    # 挡水堤（v1.3 AR05）：沿水箱槽的电控侧两边竖起 3mm 高堤，拦住横向漫流
    "dam_w": 3.0,
    "dam_h": 3.0,

    # 拼接
    "joint_y": (60.0, -60.0),   # 2026-11-12 领导：连接槽与花盆/oled 对齐到 y=60
    "block_x": 45.0,
    "block_y": 24.0,
    "block_t": 3.5,             # = 沉槽深 -> 与板面绝对齐平 [v1.2]
    "recess_d": 3.5,            # = block_t, 齐平 [v1.2: 原 1.0 露出 3mm]
    "recess_clear": 0.6,
    "screw_x": 14.0,
    "screw_y": 7.0,
    "screw_d": 3.4,             # 连接块过孔
    "c_bore_d": 6.2,            # 连接块沉头窝
    "c_bore_t": 1.8,            # 盘头 M3 头高 1.8 -> 头面与板面齐平
    "pilot_d": 2.8,             # 底板自攻引导孔
    "pilot_skin": 0.6,          # 孔底留皮 (M3x6 自攻尖落在 0.2, 不穿底)
    "dowel_d": 4.1,             # 定位销孔 (跨缝)
    "dowel_depth": 8.0,

    # 走线
    "slot_w": 3.0,
    "slot_l": 10.0,

    # 状态灯（灯罩已取消, 裸 5mm LED 直接插板上）
    "led_d": 5.2,               # φ5.2 通孔: 灯座圈坐在板面, 引脚穿过 [设计决策]
    "led_pos": (-22.0, 18.0),   # 与 OLED 支架(右缘 x=-27)留 2.5mm
}


# ============================================================
def B(cx, cy, cz, sx, sy, sz):
    m = box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, cz])
    return m


def C(cx, cy, cz, r, h, axis="z", sections=64):
    m = cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([cx, cy, cz])
    return m


def cut(base, cutters):
    return difference([base] + list(cutters), engine="manifold")


def add(base, parts):
    return union([base] + list(parts), engine="manifold")


def half_plate(p, side):
    """side=-1 左片(x<0) / +1 右片(x>0)"""
    px, py, pt = p["plate_x"], p["plate_y"], p["plate_t"]
    plate = B(0, 0, pt / 2, px, py, pt)
    far = 40.0
    w = px / 2 + far
    cx = side * (px / 2 + far / 2 - (px / 2) / 2)  # 覆盖到接缝之外
    cutter = B(side * (w / 2), 0, pt / 2, w, py + 20, pt + 10)
    return cut(plate, [cutter]), plate


def build_half(p, side):
    px, py, pt = p["plate_x"], p["plate_y"], p["plate_t"]
    plate = B(0, 0, pt / 2, px, py, pt)
    far = 60.0
    # 半空间切刀: 左片(side=-1) 切掉全部 x>0, 右片反之
    w = px + 2 * far
    cutter = B(-side * w / 2, 0, pt / 2, w, py + 40, pt + 10)
    body = cut(plate, [cutter])

    holes = []
    # --- 连接块沉槽 (接缝两侧各半个) ---
    for jy in p["joint_y"]:
        hw = p["block_x"] / 2 + p["recess_clear"] / 2      # 半个沉槽宽
        # 2026-11-11 修正：切槽盒高度 recess_d+2 原来是"上下各多 1"，导致槽深 = recess_d+1（实测 4.5，块沉 1mm）。
        # 现在改成 recess_d+1 并把中心抬 0.5 → 槽底准确落在 pt-recess_d，块与板面齐平。
        body = cut(body, [B(side * hw / 2, jy, pt - p["recess_d"] + (p["recess_d"] + 1) / 2,
                           hw, p["block_y"] + p["recess_clear"], p["recess_d"] + 1)])
        # 自攻引导孔: 从槽底打到距板底 pilot_skin 处
        mat = pt - p["recess_d"]                      # 槽下实心厚度
        pz0 = p["pilot_skin"]
        for sy in (-1, 1):
            holes.append(C(side * p["screw_x"], jy + sy * p["screw_y"], (pz0 + mat) / 2,
                           p["pilot_d"] / 2, mat - pz0, sections=48))
        # 跨缝定位销孔 (沿 X, 从接缝面向内)
        holes.append(C(side * p["dowel_depth"] / 2, jy, pt / 2,
                       p["dowel_d"] / 2, p["dowel_depth"] + 2, axis="x", sections=48))

    # --- 功能槽 ---
    if side < 0:
        holes.append(C(p["pot_pos"][0], p["pot_pos"][1], pt + 1.0 - p["pot_depth"] / 2,
                       p["pot_d"] / 2, p["pot_depth"] + 2, sections=96))   # 槽底 = pt-pot_depth（原少 +1，槽深多 1mm）
        for (w, h, pos) in ((p["bb_w"], p["bb_h"], p["bb_pos"]),
                            (p["relay_w"], p["relay_h"], p["relay_pos"])):
            holes.append(B(pos[0], pos[1], pt + 1.0 - p["pocket_depth"] / 2,
                           w + p["pocket_clear"], h + p["pocket_clear"],
                           p["pocket_depth"] + 2))   # 槽底 = pt-pocket_depth
        # 电控区扎带槽：2026-11-12 20:58 领导「都去了」→ 四个全部取消（不再开任何扎带过孔）
        # 锥形槽（07/11：与零件同角度的倒四棱柱）
        for _nm, fx, fy, wb, wt, hh, cl in p["fits_taper"]:
            v = np.array([
                [fx-(wb/2+cl), fy-(wb/2+cl), pt-hh], [fx+(wb/2+cl), fy-(wb/2+cl), pt-hh],
                [fx+(wb/2+cl), fy+(wb/2+cl), pt-hh], [fx-(wb/2+cl), fy+(wb/2+cl), pt-hh],
                [fx-(wt/2+cl), fy-(wt/2+cl), pt], [fx+(wt/2+cl), fy-(wt/2+cl), pt],
                [fx+(wt/2+cl), fy+(wt/2+cl), pt], [fx-(wt/2+cl), fy+(wt/2+cl), pt],
            ])
            f = np.array([[0,3,2],[0,2,1],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                          [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
            cutter = trimesh.Trimesh(vertices=v, faces=f, process=True)
            cutter.fix_normals()
            holes.append(cutter)
        # 小件嵌槽（完全嵌平）
        for _nm, fx, fy, fw, fh, fd, fr in p["fits"]:
            box_cut = box(extents=[fw + p["fit_clear"], fh + p["fit_clear"], fd + 2])
            if fr:
                box_cut.apply_transform(trimesh.transformations.rotation_matrix(
                    np.deg2rad(fr), [0, 0, 1]))
            box_cut.apply_translation([fx, fy, pt + 1.0 - fd / 2])   # 底面正好落在 pt-fd
            holes.append(box_cut)
            # 槽口斜口：2026-11-12 领导定为「直口」→ 不再切倒角（保留代码，开关 mouth_chamfer）
            if p.get("mouth_chamfer", 0) > 0:
                # 槽口 0.6×45° 导入倒角（07/11 锥形槽自带导入；08 槽变小后两侧墙足够，恢复倒角）
                # 2026-11-12 修 bug：原来 X/Y 都用了宽度的一半 → 槽口被切成正方形；
                # 现改为分别用宽/深的一半，槽口斜口与槽本体同为矩形。
                hx = (fw + p["fit_clear"]) / 2.0
                hy = (fh + p["fit_clear"]) / 2.0
                hh = 1.6
                v = np.array([[-hx, -hy, pt-0.6], [hx, -hy, pt-0.6], [hx, hy, pt-0.6], [-hx, hy, pt-0.6],
                              [-(hx+hh), -(hy+hh), pt-0.6+hh], [(hx+hh), -(hy+hh), pt-0.6+hh],
                              [(hx+hh), (hy+hh), pt-0.6+hh], [-(hx+hh), (hy+hh), pt-0.6+hh]])
                f = np.array([[0,3,2],[0,2,1],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
                              [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
                ch = trimesh.Trimesh(vertices=v, faces=f, process=True)
                ch.fix_normals()
                if fr:
                    ch.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(fr), [0, 0, 1]))
                ch.apply_translation([fx, fy, 0])
                holes.append(ch)
    else:
        # 圆槽：竖壁圆柱切 5 深（1L 桶落座），见参数注释
        holes.append(C(p["tank_pos"][0], p["tank_pos"][1], pt + 1.0 - p["tank_depth"] / 2,
                       p["tank_d"] / 2, p["tank_depth"] + 2, sections=96))   # 槽底 = pt-tank_depth
        # 槽底排水孔（通板，漏水直落桌面）——位置在槽内，桶底下也照排渗水
        holes.append(C(p["drain_pos"][0], p["drain_pos"][1], pt / 2,
                       p["drain_d"] / 2, pt + 4, sections=32))
        for yy in (-80, 75):
            for xx in (45, 125):
                holes.append(B(xx, yy, pt / 2, p["slot_l"], p["slot_w"], pt + 4))

    body = cut(body, holes)

    # 挡水堤：沿圆槽 -Y/-X 两切点外侧竖 3×3（槽外实板上，避开 φ108 圆）
    if side > 0:
        tx, ty = p["tank_pos"]
        d, dw, dh = p["tank_d"] / 2, p["dam_w"], p["dam_h"]
        dam = add(B(tx, ty - d - dw / 2 - 3.0, pt + dh / 2, 2 * d + 8, dw, dh),
                  [B(tx - d - dw / 2 - 3.0, ty, pt + dh / 2, dw, 2 * d + 8, dh)])
        body = add(body, [dam])
    return body


def build_block(p):
    bx, by, bt = p["block_x"], p["block_y"], p["block_t"]
    body = B(0, 0, bt / 2, bx, by, bt)
    cuts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * p["screw_x"], sy * p["screw_y"]
            cuts.append(C(x, y, bt / 2, p["screw_d"] / 2, bt + 4, sections=48))
            cuts.append(C(x, y, bt - p["c_bore_t"] / 2, p["c_bore_d"] / 2,
                          p["c_bore_t"] + 2, sections=48))
    return cut(body, cuts)


# ============================================================
def validate(mesh, name):
    return {
        "name": name,
        "watertight": bool(mesh.is_watertight),
        "bodies": len(mesh.split(only_watertight=False)),
        "volume_mm3": round(float(mesh.volume), 1),
        "triangles": int(len(mesh.faces)),
        "bbox_mm": [round(float(x), 2) for x in mesh.extents],
        "z_min": round(float(mesh.bounds[0][2]), 3),
        "solid_g_PLA": round(float(mesh.volume) * 1.24 / 1000, 1),
        "real_g_at_20pct": round(float(mesh.volume) * 1.24 / 1000 * 0.33, 1),
    }


def render(mesh, azim=45.0, elev=28.0, size=900, base_color=(0.62, 0.70, 0.80)):
    tris, n = mesh.triangles, mesh.face_normals
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
    pad = 0.06 * max(x1m - x0m, y1m - y0m)
    sc = (size - 1) / max(x1m - x0m + 2 * pad, y1m - y0m + 2 * pad)
    sx = (tx - x0m + pad) * sc
    sy = (size - 1) - (ty - y0m + pad) * sc
    light = np.array([0.35, 0.55, 0.76])
    light /= np.linalg.norm(light)
    shade = 0.32 + 0.68 * np.clip(n @ light, 0, 1)
    colors = np.array(base_color)[None, :] * shade[:, None]
    img = np.ones((size, size, 3), dtype=np.float32)
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
        img[by0:by1 + 1, bx0:bx1 + 1][closer] = colors[i]
    return np.clip(img, 0, 1)


def sheet(views, title, path, ncol=3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    n = len(views)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5.2), facecolor="white")
    if n == 1:
        axes = [axes]
    for ax, (im, t) in zip(axes, views):
        ax.imshow(im)
        ax.set_title(t, fontsize=12, color="#222")
        ax.axis("off")
    fig.suptitle(title, fontsize=15, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.89])
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def main():
    reps = []
    specs = [
        ("06a_base_left", "整机底盘·左片", build_half, (-1,)),
        ("06b_base_right", "整机底盘·右片", build_half, (1,)),
        ("06c_joint_block", "连接块 ×2", build_block, ()),
    ]
    for key, cn, fn, args in specs:
        mesh = fn(P, *args)
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
        sheet([(render(mesh, 38, 26, 720), "轴测 ISO"),
               (render(mesh, 0, 89.5, 720), "俯视 TOP"),
               (render(mesh, 0, 0, 720), "正视 FRONT")],
              f"{key}  {cn}   (mm, Z↑)", os.path.join(PREVIEW_DIR, f"{key}.png"))
        reps.append(rep)
        print(json.dumps(rep, ensure_ascii=False))

    with open(os.path.join(OUT, "check_report.json"), "w", encoding="utf-8") as f:
        json.dump(reps, f, ensure_ascii=False, indent=1)

    print("\n=== 汇总 ===")
    for r in reps:
        flag = "OK " if (r["watertight"] and r["bodies"] == 1) else "!! "
        print(f"{flag}{r['name']}: bbox={r['bbox_mm']} 实体~{r['solid_g_PLA']}g "
              f"20%填充~{r['real_g_at_20pct']}g tri={r['triangles']}")

    # 装配总览: 两片 + 连接块一起摆
    left = build_half(P, -1)
    right = build_half(P, 1)
    blk = build_block(P)
    b1 = blk.copy()
    b1.apply_translation([0, P["joint_y"][0], P["plate_t"] - P["recess_d"] + 0.02])
    b2 = blk.copy()
    b2.apply_translation([0, P["joint_y"][1], P["plate_t"] - P["recess_d"] + 0.02])
    asm = union([left, right, b1, b2], engine="manifold")
    asm.apply_translation([0, 0, 0])
    sheet([(render(asm, 38, 30, 980), "装配态 (俯视)"),
           (render(asm, 0, 89.5, 980), "俯视 TOP")],
          "整机底盘 320×230 两片装配态  (mm)", 
          os.path.join(PREVIEW_DIR, "00_底盘装配总览.png"), ncol=2)
    print("装配总览:", os.path.join(PREVIEW_DIR, "00_底盘装配总览.png"))


if __name__ == "__main__":
    main()
