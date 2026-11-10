# -*- coding: utf-8 -*-
"""
花房 Final Project · P0 三件参数化建模脚本 (v1 占位版)
------------------------------------------------------
产出: STL (mm) + 预览渲染图 + 尺寸/校验报告

设计原则
1. 全部尺寸集中在 PARAMS 里 —— 到货实测后只改数字, 重跑即得 v2
2. 所有实体走 CSG 布尔 (manifold3d 内核), 保证 watertight / manifold, 可直接切片
3. 打印朝向即建模朝向 (Z 向上 = 热床上表面法向), 无需在切片软件里翻转
4. 每条关键尺寸标注来源: [实测待填] / [市售常见值] / [设计决策]

运行:
    python p0_models.py
"""
import os
import json
import numpy as np
import trimesh
from trimesh.creation import box, cylinder
from trimesh.boolean import difference, union

TRIMESH_OK = True
OUT = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(OUT, "STL")
PREVIEW_DIR = os.path.join(OUT, "preview")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# ============================================================
# 参数区 —— 实物到货后只改这里
# ============================================================
PARAMS = {
    # ---------- 件 1: 土壤传感器 L 型支架 ----------
    "sensor": {
        "board_w": 23.0,         # [市售常见值 v2.0 电容式板宽, 实物卡尺待测]
        "board_t": 1.6,          # [市售常见值 PCB 厚, 实物卡尺待测]
        "arm_x": 30.0,           # 立臂宽 [设计决策]
        "arm_t": 3.0,            # 立臂厚
        "arm_h": 52.0,           # 立臂高 [设计决策: 留板子上下调节空间]
        "boss_x": 30.0,          # 板槽座宽 = 立臂宽, 板槽两侧各留 3.2 壁厚
        "boss_t": 10.0,          # 板槽座厚 (Y 向) —— 要能容纳板槽
        "groove_x": 23.6,        # 板槽 X 向净宽 = 板宽 23 + 0.6
        "groove_top": 1.5,       # 板槽 Y 向间隙 (板厚 1.6 -> 0.1 过盈, 任意深度都能压紧)
        "groove_bot": 1.5,       # 恒定间隙, 不用锥度: 1.8 的锥口永远夹不住 1.6 的板
        "groove_z0": -2.0,       # 板槽贯通底板 (原来封底在 z=8, 板子进不了土)
        "foot_x": 30.0,          # 底板宽
        "foot_y": 46.0,          # 底板深 [设计决策: 跨土面稳定]
        "foot_t": 3.0,           # 底板厚
        "clear_x": 24.0,         # 底板让位槽宽 (板子穿过底板入土)
        "clear_y": 4.0,          # 底板让位槽深 (Y 向)
        "m3_d": 3.2,             # M3 过孔 [设计决策: FDM 热缩, 比 3.0 放大 0.2]
        "m3_x": 10.0,            # 两孔 X 间距的一半
        "m3_y": 12.0,            # 孔心距立臂的 Y 位置
    },
    # ---------- 件 2: 水泵固定座（2026-10-19 按实物改：方形泵体）----------
    # 实物：3W USB 底吸泵，泵体 41 × 39 × 30，含出水嘴高 37；底脚（吸盘）32 × 28
    # v1 按"φ38 圆柱泵"做的圆筒座，实物是方的，整套重做
    "pump": {
        "body_x": 41.0,          # [实测] 泵体长
        "body_y": 39.0,          # [实测] 泵体宽
        "body_h": 30.0,          # [实测] 泵体高（不含出水嘴）
        "clear": 0.5,            # 单边间隙
        "wall": 3.5,             # 座壁厚
        "wall_h": 22.0,          # 座壁高（覆盖泵体 2/3，防倾倒且不挡出水嘴）
        "base_t": 3.0,           # 底板厚
        "base_margin": 4.0,      # 底板比外壁外扩
        "intake_x": 34.0,        # 底部进水开孔（让底吸口触水）
        "intake_y": 30.0,
        "rib_w": 6.0,            # 角部加强筋宽
        "rib_h": 16.0,           # 加强筋高
        "m3_d": 3.2,             # 底板安装孔
        "m3_dx": 23.0,           # 孔位 X（外壁外，避免被壁堵死）
        "m3_dy": 21.5,
    },
    # ---------- 件 3: 水管末端固定夹 ----------
    # v2 设计（2026-10-19，AR05）：原方案"立板跨盆壁 + 锥形楔紧槽"在锥形盆上必然咬入盆壁
    # （审计实测 花盆×夹 12.3mm³、土壤×夹 381mm³）。改为复刻 01b 已验证的"盆沿双爪"夹持
    # （01b 与花盆干涉 = 0），爪只下探 7mm（土面在盆沿下 8mm），管环上置，管孔竖直贯穿。
    "clip": {
        # ---------- 2026-10-23 改方案 B：土插式（不夹盆沿）----------
        # 与 01b 同理：实盆壁厚 10~20mm 范围太宽，刚性双爪无法覆盖 → 改插土针
        "tube_od": 10.0,         # [2026-10-23 实测] 硅胶管外径 10mm (内径 8.5)
        "ring_inner_d": 10.6,    # 管孔内径 = 管外径 10 + 0.6
        # 插土针：细长方条，插进土里把管环架高
        "pin_t": 4.0,            # 针厚（X）—— 窄版
        "pin_w": 6.0,            # 针宽（Y）
        "pin_depth": 25.0,       # 插土深度
        "pin_x": 5.0,            # 针中心 X（±），紧贴管环两侧
        "pin_y": 0.0,            # 针的 Y 中心
        # 管环：立在土面上方，孔竖直贯穿
        "ring_rise": 16.0,       # 管孔中心离土面高度（管子出水口要在土面上方）
        "col_x": 15.0,           # 管环柱宽 X（窄版：孔径10.6 + 两侧壁2.2）→ 占地 15×15
        "col_y": 0.0,            # 管环柱中心 Y
        "col_d": 15.0,           # 管环柱深 Y
        "col_h": 16.0,           # 管环柱高
        "bridge_h": 6.0,         # 顶桥厚
    },
}


# ============================================================
# 几何基元
# ============================================================
def B(cx, cy, cz, sx, sy, sz):
    """以中心点定位的长方体"""
    m = box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, cz])
    return m


def C(cx, cy, cz, r, h, axis="z", sections=64):
    """圆柱 / 孔。cz 为轴向中心"""
    m = cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    elif axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([cx, cy, cz])
    return m


def _prism(pts, axis, a0, a1):
    """凸多边形截面沿指定轴拉伸: axis='x' -> pts 为 (y,z); axis='y' -> pts 为 (x,z)"""
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
    """截面 (y,z), 沿 X 拉伸"""
    return _prism(pts, "x", x0, x1)


def prism_xz(pts, y0, y1):
    """截面 (x,z), 沿 Y 拉伸"""
    return _prism(pts, "y", y0, y1)


def tri_prism(profile_yz, x0, x1):
    """三角棱柱: profile 为 (y,z) 三个点, 沿 X 从 x0 拉伸到 x1"""
    return prism_yz(profile_yz, x0, x1)


def cut(base, cutters):
    return difference([base] + list(cutters), engine="manifold")


def add(base, parts):
    return union([base] + list(parts), engine="manifold")


# ============================================================
# 件 1: 土壤传感器 L 型支架
# ============================================================
def build_sensor_bracket(p):
    fy, ft = p["foot_y"], p["foot_t"]
    ax, ah = p["arm_x"], p["arm_h"]
    bx, bt = p["boss_x"], p["boss_t"]
    boss_cy = -fy / 2 + ft / 2 + bt / 2   # 板槽座贴在立臂前表面

    # 底板
    body = B(0, 0, ft / 2, ax, fy, ft)
    # 立臂 (立于底板后缘)
    body = add(body, [B(0, -fy / 2 + ft / 2, ah / 2, ax, ft, ah)])
    # 板槽座 (实心块, 后面挖板槽) —— 同时充当 L 角加强
    body = add(body, [B(0, boss_cy, ah / 2, bx, bt, ah)])

    # 板槽: 上口宽 2.4 / 下口窄 1.8 的锥形槽, 板子插到底即楔紧
    g0, g1 = p["groove_bot"] / 2, p["groove_top"] / 2
    gz = p["groove_z0"]
    groove = prism_yz(
        [(boss_cy - g0, gz), (boss_cy + g0, gz),
         (boss_cy + g1, ah + 8), (boss_cy - g1, ah + 8)],
        -p["groove_x"] / 2, p["groove_x"] / 2,
    )
    body = cut(body, [groove])

    # 底板让位槽: 板子穿过底板继续往下入土
    body = cut(body, [B(0, boss_cy, ft / 2, p["clear_x"], p["clear_y"], ft + 4)])

    # 底板两个 M3 过孔
    body = cut(body, [
        C(sx * p["m3_x"], p["m3_y"], ft / 2, p["m3_d"] / 2, ft + 4)
        for sx in (-1, 1)
    ])
    return body


# ============================================================
# 件 2: 水泵固定座
# ============================================================
def build_pump_mount(p):
    """方形底吸泵的固定座：底板（中间开孔让底吸口触水）+ 四面围壁 + 角部斜筋。"""
    cx = p["body_x"] + 2 * p["clear"]          # 内腔
    cy = p["body_y"] + 2 * p["clear"]
    wall, bt, h = p["wall"], p["base_t"], p["wall_h"]
    ox, oy = cx + 2 * wall, cy + 2 * wall      # 外壁
    bx, by = ox + 2 * p["base_margin"], oy + 2 * p["base_margin"]

    body = B(0, 0, bt / 2, bx, by, bt)
    body = cut(body, [B(0, 0, bt / 2, p["intake_x"], p["intake_y"], bt + 4)])

    # 四面围壁（用外壳减内腔，避免四块拼接留缝）
    shell = B(0, 0, bt + h / 2, ox, oy, h)
    cavity = B(0, 0, bt + h / 2, cx, cy, h + 4)
    body = add(body, [cut(shell, [cavity])])

    # 角部斜筋从简：四面 3.5 壁 + 3mm 底板已足够防倾倒，避免四角各做一块导致多体
    # 四个 M3 安装孔（落在底板四角、外壁之外）
    holes = [C(sx * p["m3_dx"], sy * p["m3_dy"], bt / 2, p["m3_d"] / 2, bt + 4)
             for sx in (-1, 1) for sy in (-1, 1)]
    body = cut(body, holes)
    return body


# ============================================================
# 件 3: 水管末端固定夹
# ============================================================
def build_tube_clip(p):
    """方案 B 土插式（2026-10-23）：两条插土针 + 管环柱，孔竖直贯穿。
    局部坐标：原点 = 土面(z=0)，+Y 向盆外，+Z 向上。
    """
    pt_, pw, pd = p["pin_t"], p["pin_w"], p["pin_depth"]
    ch = p["col_h"]
    ry = p["col_y"]

    # ---- 1) 两条插土针：从 z=-pd 插到 z=0（与管环柱叠合）----
    pins = [B(sx * p["pin_x"], p["pin_y"], -pd / 2, pt_, pw, pd)
            for sx in (-1, 1)]
    body = union(pins, engine="manifold")

    # ---- 1.5) 根部斜撑：2026-11-10 领导要求去掉（打印出来嫌多余）----
    # 去掉后针又回到"3.2×6、25mm 悬臂"状态 → 取下时根部仍是最脆弱处。
    # 如需再加强：把 pin_t 加到 4.0，或在根部加 R1.5 圆角（改动小、不影响外观）。
    if p.get("brace", False):
        bh = p.get("brace_h", 7.0)
        bx = p["pin_x"] + 0.5
        body = union([body, prism_xz([(-bx, 0.0), (bx, 0.0), (0.0, -bh)], -pw / 2, pw / 2)],
                     engine="manifold")

    # ---- 2) 管环柱：底面坐在土面(z=0)，顶面 z=ch ----
    col = B(0, ry, ch / 2, p["col_x"], p["col_d"], ch)
    body = union([body, col], engine="manifold")

    # ---- 3) 管孔：从土面直通柱顶，管子在孔内全程竖直 ----
    body = cut(body, [C(0, ry, ch / 2, p["ring_inner_d"] / 2, ch + 4, sections=64)])

    # ---- 4) 落床归一化：z_min -> 0；metadata 记录土面高度 ----
    zmin = float(body.bounds[0][2])
    body.apply_translation([0, 0, -zmin])
    body.metadata["rim_top_z"] = -zmin   # 兼容旧字段名（语义 = 土面高度）
    body.metadata["soil_top_z"] = -zmin
    return body


# ============================================================
# 校验
# ============================================================
def validate(mesh, name):
    parts = mesh.split(only_watertight=False)
    ext = mesh.extents
    rep = {
        "name": name,
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": round(float(mesh.volume), 1),
        "surface_mm2": round(float(mesh.area), 1),
        "triangles": int(len(mesh.faces)),
        "bodies": len(parts),
        "bbox_mm": [round(float(x), 2) for x in ext],
        "z_min": round(float(mesh.bounds[0][2]), 3),
        "est_mass_g_PLA": round(float(mesh.volume) * 1.24 / 1000, 1),  # PLA 1.24 g/cm3
    }
    return rep


# ============================================================
# 预览渲染 (自写 z-buffer 光栅化, 不依赖 OpenGL/显示器)
# ============================================================
def render(mesh, azim=45.0, elev=28.0, size=900, base_color=(0.62, 0.70, 0.80)):
    tris = mesh.triangles  # (n,3,3)
    n = mesh.face_normals

    a, e = np.deg2rad(azim), np.deg2rad(elev)
    # 相机基向量 (正交投影)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    right = np.cross([0, 0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)

    v = tris.reshape(-1, 3)
    px = v @ right
    py = v @ up
    pz = v @ fwd
    # 每三角的 (x, y, depth)
    tx = px.reshape(-1, 3)
    ty = py.reshape(-1, 3)
    tz = pz.reshape(-1, 3)

    xmin, xmax = tx.min(), tx.max()
    ymin, ymax = ty.min(), ty.max()
    pad = 0.06 * max(xmax - xmin, ymax - ymin)
    sc = (size - 1) / max(xmax - xmin + 2 * pad, ymax - ymin + 2 * pad)
    sx = (tx - xmin + pad) * sc
    sy = (size - 1) - (ty - ymin + pad) * sc

    # 光照
    light = np.array([0.35, 0.55, 0.76])
    light /= np.linalg.norm(light)
    lam = np.clip(n @ light, 0, 1)
    shade = 0.32 + 0.68 * lam
    colors = np.array(base_color)[None, :] * shade[:, None]

    img = np.ones((size, size, 3), dtype=np.float32)
    zbuf = np.full((size, size), -1e9, dtype=np.float32)

    order = np.argsort(tz.min(axis=1))  # 远->近, 减少 zbuffer 争用
    for i in order:
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
        sub_c = img[by0:by1 + 1, bx0:bx1 + 1]
        sub_c[closer] = colors[i]

    return np.clip(img, 0, 1)


def contact_sheet(mesh, name, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    iso = render(mesh, azim=38, elev=26, size=760)
    top = render(mesh, azim=0, elev=89.5, size=760)
    side = render(mesh, azim=0, elev=0, size=760)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), facecolor="white")
    for ax, im, t in zip(axes, [iso, top, side], ["轴测 ISO", "俯视 TOP", "正视 FRONT"]):
        ax.imshow(im)
        ax.set_title(t, fontsize=13, color="#222")
        ax.axis("off")
    fig.suptitle(f"{name}   (mm, 打印朝向 Z↑)", fontsize=15, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def sheet_all(rows):
    """总览排布: 一件一格, 标注外形尺寸与估重"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, len(rows), figsize=(5 * len(rows), 5.4), facecolor="white")
    if len(rows) == 1:
        axes = [axes]
    for ax, (mesh, title, sub) in zip(axes, rows):
        ax.imshow(render(mesh, azim=38, elev=26, size=760))
        ax.set_title(f"{title}\n{sub}", fontsize=12, color="#222")
        ax.axis("off")
    fig.suptitle(f"花房 Final Project · P0 {len(rows)} 件 v1 占位版  (单位 mm, Z↑ 为打印朝向)",
                 fontsize=15, color="#111")
    fig.tight_layout(rect=[0, 0, 1, 0.86])
    path = os.path.join(PREVIEW_DIR, f"00_P0_{len(rows)}件总览.png")
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    return path



BUILDERS = [
    # ("01_sensor_L_bracket", ...) 已作废删除 2026-10-20 (被 01b 盆沿挂钩取代, 历史见 git)
    ("02_pump_mount", "水泵固定座", build_pump_mount, PARAMS["pump"]),
    ("03_tube_clip", "水管末端固定夹", build_tube_clip, PARAMS["clip"]),
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
        print(json.dumps(rep, ensure_ascii=False, indent=1))

    with open(os.path.join(OUT, "check_report.json"), "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=1)
    print("\n=== 汇总 ===")
    for r in reports:
        flag = "OK " if (r["watertight"] and r["bodies"] == 1) else "!! "
        print(f"{flag}{r['name']}: bbox={r['bbox_mm']} vol={r['volume_mm3']}mm3 "
              f"~{r['est_mass_g_PLA']}g tri={r['triangles']} bodies={r['bodies']} "
              f"watertight={r['watertight']}")

    # 三件总览图
    rows = []
    for (key, cn, fn, p), r in zip(BUILDERS, reports):
        mesh = fn(p)
        bx = r["bbox_mm"]
        rows.append((mesh, f"{cn}", f"{bx[0]}×{bx[1]}×{bx[2]} mm   ~{r['est_mass_g_PLA']} g"))
    print("总览图:", sheet_all(rows))


if __name__ == "__main__":
    main()
