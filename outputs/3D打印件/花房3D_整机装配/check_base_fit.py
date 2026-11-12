# -*- coding: utf-8 -*-
"""
底板 × 装配件 一致性核对
========================
查三件事，任何一件不过就打印 !!：
  ① 每个"落在底板上"的件, 底面高度是否等于它该坐的位置(槽底/板面)
  ② 件与底板是否干涉(布尔求交体积)
  ③ 底板上有没有"空槽"(开了槽却没东西) / "该有槽却没有"
"""
import sys
import numpy as np
import trimesh

sys.path.insert(0, ".")
import build_assembly as BA

BASE = "../花房3D_整机底盘/STL/06a_base_left_v1.stl"
BASE_R = "../花房3D_整机底盘/STL/06b_base_right_v1.stl"
PT = 8.0

plate_l = trimesh.load(BASE)
plate_r = trimesh.load(BASE_R)
plate_all = trimesh.util.concatenate([plate_l, plate_r])

# ==== 1L 打包桶【2026-10-23 到货实测·领导量具】—— 期望高度由此推导 ====
# 实测: 桶底直径 105 / 桶口内径 120 / 桶口外径 124
# 商品页原标"上径 136 / 底径 106"是含提手凸缘的最大外径, 桶本体口沿外径只有 124
BUCKET_BOT_OD = 105.0
BUCKET_MOUTH_ID = 120.0
BUCKET_MOUTH_OD = 124.0
BUCKET_WALL = (BUCKET_MOUTH_OD - BUCKET_MOUTH_ID) / 2     # 2.0 侧壁厚(实测推算)
BUCKET_BOT_T = 2.0          # 桶底厚【未实测, 暂按侧壁厚推算】
BUCKET_H = 127.0            # 桶身高 [2026-10-23 实测 127]
BUCKET_LIP_OD = 132.0        # 桶口最外侧（加强翻边外缘）[实测]
LID_SKIRT_H = 6.0           # 裙边高（套翻边）—— 与 p10_tank_lid.py 一致
TANK_FLOOR_Z = 3.0          # 底盘圆槽槽底 z
TANK_SLOT_D = BUCKET_BOT_OD + 2                           # 圆槽直径 107
BUCKET_MOUTH_Z = TANK_FLOOR_Z + BUCKET_H                 # 桶口沿 z = 123
WATER_Z = TANK_FLOOR_Z + BUCKET_BOT_T                    # 桶内底 z = 5.0

# 每件应该坐的高度: (槽底 z, 说明)
EXPECT = {
    "花盆":        (2.0, "φ82 凹槽 深6 -> 槽底 z=2（8x8x8 直筒树脂盆 φ80 落座）"),
    "水箱":        (TANK_FLOOR_Z, f"圆槽 φ{TANK_SLOT_D:.0f} 深5 -> 槽底 z=3（1L 桶底 φ{BUCKET_BOT_OD:.0f} 落座）"),
    "面包板":      (4.5, "槽 深3.5 -> 槽底 z=4.5"),
    "继电器":      (4.5, "槽 深3.5 -> 槽底 z=4.5"),
    "ESP32":       (4.5, "随面包板 (插在面包板上)"),
    "OLED 45°支架": (5.0, "嵌槽 3.0（2026-11-08）"),
    "LED 模块":    (6.4, "嵌槽 1.6（2026-11-08）"),
    "DHT11 座":    (3.5, "嵌槽 4.5（2026-11-08）"),
    # "扎线座":  (6.0, ...)  2026-11-12 领导：理线器取消，底盘不再开槽
    "光敏电阻座":   (4.0, "嵌槽 4.0（2026-11-08）"),
    "土壤":        (5.0, "在花盆内底上"),
    "水体":        (WATER_Z, f"桶内底 {TANK_FLOOR_Z}+底厚{BUCKET_BOT_T}"),
    "水泵":        (WATER_Z + 3.0, "桶内底 + 吸盘垫高约3"),
    "水泵进水格栅": (WATER_Z + 1.8, "泵底吸口栅条（下缘悬水中，设计意图）"),
    "连接块":      (4.5, "沉槽 深3.5 -> 与板面齐平"),
    "LED 灯珠":    (8.0, "坐在模块板上（模块嵌平）"),
    "水箱盖":      (BUCKET_MOUTH_Z - LID_SKIRT_H, f"裙边下探 {LID_SKIRT_H:.0f}（桶口沿 z={BUCKET_MOUTH_Z:.0f}）"),
    "浮球法兰":    (BUCKET_MOUTH_Z + 4.0, f"盖顶 z={BUCKET_MOUTH_Z:.0f}+4"),
    "浮子":        (75.0, "杆尖 z=75，满水时浮至水面"),
}

print("=" * 84)
print("① 落座高度核对")
print("=" * 84)
fails = []
seen = {}
for m, ck, nm in BA.items:
    lo, hi = m.bounds
    if lo[2] > PT + 1.0 or not nm or nm == "扎线座" or nm.startswith(("底盘", "M3×6", "跳线", "面包板孔", "面包板中", "面包板电", "ESP32 U", "ESP32 按", "ESP32 E", "ESP32 天", "ESP32 屏", "继电器端", "继电器指", "光耦", "排针", "OLED 排针", "水管")):
        continue
    key = nm
    if key in seen:            # 连接块/叶片等同名件只报一次
        continue
    seen[key] = True
    exp, why = EXPECT.get(nm, (None, "未登记"))
    dz = abs(lo[2] - exp) if exp is not None else 9.9
    ok = exp is not None and dz < 0.05
    if not ok:
        fails.append(f"{nm} 底面 z={lo[2]:.2f}, 应为 {exp}")
    print("%s %-14s z_min=%6.2f  应为 %s  %-30s %s" % (
        "OK " if ok else "!! ", nm, lo[2],
        ("%5.1f" % exp) if exp is not None else "  ?  ", why,
        "" if ok else "← 偏差 %.2f mm" % dz))

print()
print("=" * 84)
print("② 件 × 底板 干涉")
print("=" * 84)
for nm in ("花盆", "水箱", "面包板", "继电器", "LED 模块", "LED 灯珠", "DHT11 座", "OLED 45°支架", "光敏电阻座"):
    for m, ck, n in BA.items:
        if n != nm:
            continue
        inter = trimesh.boolean.intersection([m, plate_all], engine="manifold")
        v = float(inter.volume) if len(inter.faces) else 0.0
        flag = "OK " if v < 5.0 else "!! "
        if v >= 5.0:
            fails.append(f"{nm} 与底板干涉 {v:.0f} mm3")
        print("%s %-14s 干涉 %7.1f mm3" % (flag, nm, v))
        break

print()
print("=" * 84)
print("③ 底板特征核对（空槽 / 缺槽 / 孔）")
print("=" * 84)


def void_at(x, y, z):
    """该点是否在底板实体之外(即空腔/孔)"""
    return not bool(plate_all.contains([np.array([x, y, z])])[0])


def solid_at(x, y, z):
    return bool(plate_all.contains([np.array([x, y, z])])[0])


# contains() 的射线法对 STL 不可靠; to_planar() 会换坐标系也不能用。
# 用 1mm 立方体与底板布尔求交: 体积 ~1mm3 = 实体, 0 = 空
def in_solid(x, y, z, a=1.0):
    probe = trimesh.creation.box(extents=[a, a, a])
    probe.apply_translation([x, y, z])
    it = trimesh.boolean.intersection([probe, plate_all], engine="manifold")
    v = float(it.volume) if len(it.faces) else 0.0
    return v > 0.5 * a ** 3


checks = [
    ("LED 模块嵌槽 @(-14,84)",               not in_solid(-14, 84, 7.0), "z=7 处应是空(槽)"),
    ("LED 槽底仍是实体 @(-14,84)",            in_solid(-14, 84, 5.8), "z=5.8 处应是实体(槽底 6.4)"),
    ("07 嵌槽 @(-45,-67)",                   not in_solid(-45, -67, 5.0), "z=5 处应是空(槽)"),
    ("04 嵌槽 @(-45,84)",                    not in_solid(-45, 84, 6.0), "z=6 处应是空(槽)"),
    ("ESP32 空槽已删除 @(-130,98)",            in_solid(-130, 98, 5.5), "z=5.5 处应已是实体（原空槽区域，现已被花盆槽外占用）"),
    ("面包板槽仍在 @(-140,-55)",               not in_solid(-140, -55, 5.5), "z=5.5 处应是空(槽)"),
    ("继电器槽 @(-48,-68)",                  not in_solid(-48, -68, 5.5), "z=5.5 处应是空(槽)"),
    ("花盆凹槽 @(-111,60) 槽心",               not in_solid(-111, 60, 5.5), "z=5.5 处应是空(φ82 槽)"),
    ("花盆凹槽上缘外 @(-111,104)",              in_solid(-111, 104, 5.5), "槽外应是实体"),
    ("花盆凹槽右缘外 @(-67,60)",               in_solid(-67, 60, 5.5), "槽外应是实体(距继电器槽)"),
    ("水箱槽 @(85,32)",                        not in_solid(85, 32, 5.5), "z=5.5 处应是空(圆槽 φ107)"),
]
for name, got, why in checks:
    flag = "OK " if got else "!! "
    if not got:
        fails.append(name)
    print("%s %-34s %s" % (flag, name, why))

print()
print("=" * 84)
if fails:
    print("未通过 %d 项：" % len(fails))
    for f in fails:
        print("  !! " + f)
else:
    print("全部通过：落座高度、零干涉、槽孔特征一致")
print("=" * 84)
