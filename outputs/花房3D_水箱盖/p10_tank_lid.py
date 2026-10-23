# -*- coding: utf-8 -*-
"""
花房 Final Project · 第 10 件: 水箱替换盖 (1L 打包桶) 参数化建模 v1
====================================================================
背景: 水箱从 118x90 方盒改为市售 1L PP 打包桶 (圆桶), 浮球开关 P52 (M10/常开)
要垂直装在桶顶 —— 桶原装盖没有安装孔, 故做一块 3D 替换盖, 桶本体不打孔 (可逆)。

商品尺寸 [淘宝官方标注图, 到货复测]:
  商品页标注: 上径 136 / 口内径 120 / 底径 106 / 桶身 104.5 / 含盖高 127 / 满口 1200ml
  ★ 2026-10-23 到货实测（领导量具，优先）: 桶底直径 105 / 桶口内径 120 / 桶身口沿 124 / 桶口最外侧 132
    -> 桶口剖面 = 内壁 φ120 | 桶身口沿 φ124（壁厚 2）| 加强翻边最外 φ132（向外凸 4mm）
       → **盖板压在翻边顶面、裙边套翻边外径 132**。按 124 做盖板会浮空 6.4mm。
       商品页标的 136 与实测 132 接近 → 136 应是含提手座的最大外径。
  ✅ 桶身高 127（实测）。⏳ 仍待实测: **翻边高度**（决定裙边能有多深，暂用 6）

结构 (打印朝向 = 使用朝向翻面, Z0 = 盖顶面贴床):
  · 盖板圆盘  φ138.4 x 4   —— φ138.4 = 翻边外 132 + 裙边壁 2.8x2  [按实测最外侧132]
  · 裙边环    内 φ132.8 x 高 6 —— 套住桶口翻边外径 (直径向隙 0.8, FDM 常规), 防侧移
                裙边高必须 <= 翻边高, 否则裙边底会顶在翻边下的台阶上装不进
  · 螺母凸台  外 φ20 x 高 0.8, 环形, 在盖板下面 (桶内侧) —— M10 螺母对角 19.6 < 20,
    螺母整个坐在凸台环面上 = 替代垫片 (2026-10-19 定版: 免垫片方案)
  · 中心孔    φ10.5 (M10 + 0.5) 贯穿凸台+盖板 —— P52 浮球开关杆
  · 水管孔    φ10 (管 φ8 + 2) @ 距中心 22mm 泵侧 (-Y) —— 水管穿盖入桶
  · 过线孔    φ8 @ 距中心 30mm (+Y) —— 水泵 USB 线穿盖出桶
  · 指位缺口  2 x φ26 半圆, 在 ±X 裙边+板缘 —— 开盖抠手

打印: 顶面朝下贴床 (首层整圆), 凸台/裙边朝上竖 printed, 全程无桥无支撑。
装配: 打印件翻面使用 (凸台/裙边朝下), 开关法兰坐盖板上表面。

几何账 (从参数反算, 非目测):
  · 浮球杆尖端 (使用态) = 盖顶 z + 板 4 + 杆长 52 —— 泵顶 (桶内底 4.5 + 座 3 + 泵 30
    + 嘴 7 = 44.5) 下方余量 >25mm, 不碰泵 [按 build_assembly v3 水箱内参数]
  · 水管孔缘距凸台外缘 7mm, 距裙边内壁 41.4mm —— 均不干涉
  · 浮球环 (φ28) 低点与泵体 XY 重叠但 Z 向隔 30mm —— 不干涉
"""
import os
import sys
import json
import numpy as np
import trimesh
from trimesh.creation import cylinder
from trimesh.boolean import union, difference

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "花房3D_P0"))
from p0_models import validate, render, contact_sheet          # noqa: E402

OUT = _HERE
STL_DIR = os.path.join(OUT, "STL")
PREVIEW_DIR = os.path.join(OUT, "preview")
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# ============================================================
# 参数 —— 桶尺寸到货后只改这里
# ============================================================
P10 = {
    # [2026-10-23 到货实测·领导量具] 1L 透明打包桶 —— 实测优先于商品页标注
    #   桶底直径 105 / 桶口内径 120 / 桶身口沿 124 / 桶口最外侧 132 / 桶高 127
    #   桶口有加强翻边（外凸 4mm），盖要压在翻边顶面、裙边套 132
    "bucket_mouth_od": 132.0,   # 桶口【最外侧】外径 = 加强翻边外缘 132（实测）
    #   桶口剖面: 内壁 φ120 | 桶身口沿 φ124（壁厚2）| 翻边最外 φ132（外凸4）
    #   → 盖板压在【翻边顶面】、裙边套【翻边外径132】；按124做盖板会浮空6.4mm
    "bucket_mouth_id": 120.0,   # 桶口内径 [实测120，与商品页一致]
    "bucket_h": 127.0,          # 桶身高 [实测 127] —— 只影响浮球杆尖高度与装配图, 不影响盖子本体几何

    # 替换盖
    "skirt_clear": 0.8,         # 裙边内径向隙 (FDM)
    "skirt_h": 6.0,             # 裙边高（套翻边外径132）—— 必须 <= 翻边高，否则底缘顶在翻边下台阶装不进 [翻边高待实测]
    "skirt_wall": 2.8,          # 裙边壁厚 -> 盖外径 = 132 + 0.8 + 5.6 = 138.4
    "plate_t": 4.0,             # 盖板厚 [定版: 给 M10 螺母留咬合]

    "boss_od": 20.0,            # 螺母凸台外径 (M10 六角对角 19.6 内, 整面承力)
    "boss_h": 0.8,              # 凸台高 = 替代垫片
    "float_hole_d": 10.5,       # 浮球杆孔 = M10 + 0.5

    "tube_hole_d": 10.0,        # 水管孔 (管 φ8 + 2)
    "tube_off": 22.0,           # 水管孔心距盖心, 泵侧 (-Y) [泵在桶心 -Y 12, 折弯可达]
    "wire_hole_d": 8.0,         # 过线孔 (USB 线 φ4 + 余量)
    "wire_off": -45.0,          # 过线孔心距盖心 (−Y，与水管同侧，电缆不再横跨盖顶)

    "notch_d": 26.0,            # 指位缺口直径 (抠手)
    "sections": 96,
}


def C(cx, cy, cz, r, h, sections=96):
    m = cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([cx, cy, cz])
    return m


def build_lid(p):
    """打印朝向建模: z=0 为盖顶面(贴床), 凸台/裙边朝上。"""
    flange_d = p["bucket_mouth_od"] + p["skirt_clear"] + 2 * p["skirt_wall"]
    skirt_id = p["bucket_mouth_od"] + p["skirt_clear"]
    pt = p["plate_t"]
    body = union([
        C(0, 0, pt / 2, flange_d / 2, pt, p["sections"]),                      # 盖板
        C(0, 0, pt + p["boss_h"] / 2, p["boss_od"] / 2, p["boss_h"], 64),      # 凸台
        C(0, 0, pt + p["skirt_h"] / 2, flange_d / 2, p["skirt_h"], p["sections"]),  # 裙外
    ], engine="manifold")
    # 裙边中空
    body = difference([body, C(0, 0, pt + p["skirt_h"] / 2, skirt_id / 2,
                               p["skirt_h"] + 4, p["sections"])], engine="manifold")
    cuts = [
        C(0, 0, pt / 2, p["float_hole_d"] / 2, pt + 2 * p["boss_h"] + 4, 64),  # 中心浮球孔(贯穿凸台)
        C(0, -p["tube_off"], pt / 2, p["tube_hole_d"] / 2, pt + 4, 64),        # 水管孔
        C(0, p["wire_off"], pt / 2, p["wire_hole_d"] / 2, pt + 4, 64),         # 过线孔
    ]
    for sx in (-1, 1):                                                          # 指位缺口
        cuts.append(C(sx * flange_d / 2, 0, (pt + p["skirt_h"]) / 2,
                      p["notch_d"] / 2, pt + p["skirt_h"] + 4, 64))
    return difference([body] + cuts, engine="manifold")


def check_geometry(p, mesh):
    """参数反算校验, 任一不过返回非空错误串。"""
    errs = []
    flange_d = p["bucket_mouth_od"] + p["skirt_clear"] + 2 * p["skirt_wall"]
    skirt_id = p["bucket_mouth_od"] + p["skirt_clear"]
    # ① M10 螺母 (对角 19.6) 必须整个坐在凸台环内
    if 19.6 > p["boss_od"]:
        errs.append(f"螺母对角 19.6 > 凸台外径 {p['boss_od']}")
    # ② 孔间不干涉
    boss_r, tube_r = p["boss_od"] / 2, p["tube_hole_d"] / 2
    gap_tube_boss = p["tube_off"] - tube_r - boss_r
    if gap_tube_boss < 2.0:
        errs.append(f"水管孔缘距凸台 {gap_tube_boss:.1f} < 2")
    if abs(p["wire_off"]) - p["wire_hole_d"] / 2 - boss_r < 2.0:
        errs.append("过线孔距凸台 < 2")
    # ②b 水管孔与过线孔不粘连
    gap_holes = abs(p["wire_off"] - p["tube_off"]) - p["wire_hole_d"] / 2 - p["tube_hole_d"] / 2
    if gap_holes < 6.0:
        errs.append(f"水管孔与过线孔间隙 {gap_holes:.1f} < 6")
    # ③ 所有孔都在裙边内圆里 (含水管孔最远缘)
    if p["tube_off"] + tube_r > skirt_id / 2 - 3.0:
        errs.append("水管孔侵入裙边内壁 3mm 保护区")
    # ④ 浮球杆尖 vs 泵顶 (使用态, 桶坐底盘槽底 z=3)
    pump_top = 3.0 + 1.5 + 3.0 + 30.0 + 7.0        # 槽底+桶底厚+座+泵体+嘴
    stem_tip = 3.0 + p["bucket_h"] + 4.0 + 52.0    # 槽底+桶身+板厚+P52 有效长
    if stem_tip < pump_top + 5.0:
        errs.append(f"浮球杆尖 z={stem_tip:.0f} 距泵顶 {pump_top:.0f} 余量 <5")
    # ⑤ 产物本体
    if not mesh.is_watertight:
        errs.append("not watertight")
    if len(mesh.split(only_watertight=False)) != 1:
        errs.append("not single body")
    if abs(mesh.bounds[0][2]) > 1e-6:
        errs.append(f"z_min={mesh.bounds[0][2]} != 0")
    return errs, gap_tube_boss, stem_tip - pump_top


def main():
    mesh = build_lid(P10)
    mesh.merge_vertices()
    try:
        mesh.update_faces(mesh.nondegenerate_faces())
    except Exception:
        pass
    mesh.fix_normals()
    rep = validate(mesh, "10_tank_lid | 水箱替换盖")
    errs, gap_tb, gap_pump = check_geometry(P10, mesh)

    stl = os.path.join(STL_DIR, "10_tank_lid_v1.stl")
    mesh.export(stl)
    rep["stl"] = stl

    png = os.path.join(PREVIEW_DIR, "10_tank_lid.png")
    contact_sheet(mesh, "10_tank_lid  水箱替换盖 (1L 桶 · P52 浮球 · 顶面朝下打印)", png)
    rep["preview"] = png
    rep["geometry_checks"] = {
        "水管孔缘-凸台间隙": round(gap_tb, 1),
        "浮球杆尖-泵顶间隙": round(gap_pump, 1),
        "errors": errs,
    }
    with open(os.path.join(OUT, "check_report.json"), "w", encoding="utf-8") as f:
        json.dump([rep], f, ensure_ascii=False, indent=1)

    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if errs:
        print("\n!! 几何校验未过:")
        for e in errs:
            print("   !! " + e)
        sys.exit(1)
    print("\nOK  watertight 单体 z0, 几何校验全过 ->", stl)


if __name__ == "__main__":
    main()
