# -*- coding: utf-8 -*-
"""
花房追加件：12 LED 灯座（13 理线槽盖板已于 2026-11-13 删除——领导决定不需要）
=====================================================
12_led_stand : 坐在底盘 φ5.2 通孔上，把裸 5mm LED 抬到 24mm 高

尺寸来源
  · 底盘 φ5.2 通孔：(-22, 18)，贯穿 8mm 板（base_2pc_models.py  "led_d": 5.2）
  · 5mm LED：灯体 φ5.0 × 8.6、法兰 φ5.9、引脚长约 27
  · 08 嵌槽：件 30×16 + 0.2 → 槽 30.2×16.2，深 2.0（"fits" 表）
"""
import os
import json
import numpy as np
import trimesh
from trimesh.creation import cylinder, box
from trimesh.boolean import difference, union

OUT = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(OUT, "STL")
os.makedirs(STL, exist_ok=True)


def C(x, y, z, r, h, sec=64):
    return cylinder(radius=r, height=h, sections=sec).apply_translation([x, y, z])


def B(x, y, z, sx, sy, sz):
    return box(extents=[sx, sy, sz]).apply_translation([x, y, z])


def loft_rect(z0, z1, w0, d0, w1, d1):
    """矩形截面直纹放样（下 w0×d0 → 上 w1×d1），用于喇叭托"""
    v = np.array([
        [-w0 / 2, -d0 / 2, z0], [w0 / 2, -d0 / 2, z0], [w0 / 2, d0 / 2, z0], [-w0 / 2, d0 / 2, z0],
        [-w1 / 2, -d1 / 2, z1], [w1 / 2, -d1 / 2, z1], [w1 / 2, d1 / 2, z1], [-w1 / 2, d1 / 2, z1],
    ])
    f = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
         [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
         [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
    m = trimesh.Trimesh(vertices=v, faces=np.array(f), process=True)
    m.fix_normals()
    return m


def frustum(z0, z1, r0, r1, n=48):
    """圆台（上下半径不同）"""
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    v = np.vstack([
        np.column_stack([r0 * np.cos(ang), r0 * np.sin(ang), np.full(n, z0)]),
        np.column_stack([r1 * np.cos(ang), r1 * np.sin(ang), np.full(n, z1)]),
    ])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f.append([i, j, n + j])
        f.append([i, n + j, n + i])
    for i in range(1, n - 1):          # 端盖用扇形三角化（保持全三角面，避免 numpy 参差）
        f.append([0, i + 1, i])
        f.append([n, n + i, n + i + 1])
    m = trimesh.Trimesh(vertices=v, faces=np.array(f), process=True)
    m.fix_normals()
    return m


# ============================================================
# 12 LED 座（适配底盘 18.8×13.5 嵌槽里的双色 LED 模块）
#   底盘实测：LED 模块槽 18.8×13.5，深 1.6（齐平），中心 (-14, 12.5)
#   LED 模块：18.8×13.5×1.6，3 针排针
# ============================================================
LED = {
    "pocket_w": 18.8, "pocket_d": 13.5, "pocket_h": 1.6,   # 底盘嵌槽
    "gap": 0.10,                 # 底座单边间隙（标定值）
    "mouth_ch": 0.0,             # 槽口斜口高度（0 = 直口）
    "mouth_square": False,      # 已弃用（直口不需要颈圈）
    "col_w": 11.0, "col_d": 9.0, # 柱身
    "post_h": 24.0,              # 柱高（板面以上）
    "tray_w": 21.0, "tray_d": 15.7, "tray_t": 3.2,
    "mod_w": 18.8, "mod_d": 13.5, "mod_t": 1.6,           # 模块
    "mod_clear": 0.10,           # 模块槽单边
    "slot_w": 10.0, "slot_l": 5.0  # 排针口：开在**短壁 +X**（壁长 15.7），宽沿 Y=10
}


def build_led_stand(p=LED):
    bw = p["pocket_w"] - 2 * p["gap"]
    bd = p["pocket_d"] - 2 * p["gap"]
    # 底座：直身 + 顶部 0.6×45° 斜口（对齐底盘槽口的导入倒角）
    ch = p["mouth_ch"]
    straight = p["pocket_h"] - ch
    body = B(0, 0, straight / 2, bw, bd, straight)
    if ch > 0.05:                               # 仅当有斜口时才放样；直口就是纯方块
        body = union([body, loft_rect(straight, p["pocket_h"], bw, bd,
                                      bw + 2 * ch, bd + 2 * ch)], engine="manifold")
    z0 = p["pocket_h"]
    body = union([body, B(0, 0, z0 + p["post_h"] / 2,
                          p["col_w"], p["col_d"], p["post_h"])], engine="manifold")   # 柱
    zt = z0 + p["post_h"]
    # 喇叭托：柱顶 11×9 → 托盘底面 19×13.7（斜度约 17°，免支撑），避免托盘底面悬空
    body = union([body, loft_rect(zt - 7.0, zt + 0.4,
                                  p["col_w"], p["col_d"],
                                  p["tray_w"] - 2.0, p["tray_d"] - 2.0)], engine="manifold")
    body = union([body, B(0, 0, zt + p["tray_t"] / 2,
                          p["tray_w"], p["tray_d"], p["tray_t"])], engine="manifold")  # 托盘
    # 模块槽（从托盘顶面下切）
    top = zt + p["tray_t"]
    pocket = B(0, 0, top - p["mod_t"] / 2 + 0.05,
               p["mod_w"] + 2 * p["mod_clear"], p["mod_d"] + 2 * p["mod_clear"],
               p["mod_t"] + 0.1)
    body = difference([body, pocket], engine="manifold")
    # 排针过线口：开在**短壁**（±X，壁长 15.7）——模块的引脚在这条短边
    body = difference([body, B(p["tray_w"] / 2 - p["slot_l"] / 2 + 0.2, 0.0,
                               top - p["tray_t"] / 2,
                               p["slot_l"], p["slot_w"], p["tray_t"] + 0.2)], engine="manifold")
    body.apply_translation([0, 0, -body.bounds[0][2]])
    return body


# ============================================================
# 13 理线槽盖板
# ============================================================
PLUG = {
    "pocket_w": 30.2, "pocket_d": 16.2, "pocket_h": 2.0,   # 底盘实测槽
    "gap": 0.10,          # 单边间隙（测试块标定值）
    "thick": 2.0,         # 与槽同深（2.0）→ 上表面与板面齐平
    "notch_d": 4.0, "notch_h": 1.2,   # 顶面撬孔（M3 螺丝勾出）
    "mouth_ch": 0.0,             # 槽口斜口高度（0 = 直口）
    "mouth_square": False,      # 已弃用
}


if __name__ == "__main__":
    report = []
    for name, disp, fn, fname in (
        ("12_led_stand", "LED 灯座", build_led_stand, "12_led_stand_v1.stl"),
    ):
        m = fn()
        path = os.path.join(STL, fname)
        m.export(path)
        info = {
            "name": "%s | %s" % (name, disp),
            "bbox": [round(float(x), 1) for x in m.extents],
            "mass_g": round(m.volume * 1.24 / 1000, 2),
            "watertight": bool(m.is_watertight),
            "bodies": len(m.split(only_watertight=False)),
            "stl": path,
        }
        report.append(info)
        print("OK %s | bbox=%s ~%.1fg 水密=%s 体=%d" % (
            name, info["bbox"], info["mass_g"], info["watertight"], info["bodies"]))
    with open(os.path.join(OUT, "check_report_extra.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)