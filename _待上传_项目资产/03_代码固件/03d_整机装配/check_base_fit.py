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

# 每件应该坐的高度: (槽底 z, 说明)
EXPECT = {
    "花盆":        (2.0, "φ62 凹槽 深6 -> 槽底 z=2"),
    "水箱":        (3.0, "矩形槽 深5 -> 槽底 z=3"),
    "面包板":      (4.5, "槽 深3.5 -> 槽底 z=4.5"),
    "继电器":      (4.5, "槽 深3.5 -> 槽底 z=4.5"),
    "ESP32":       (4.5, "随面包板 (插在面包板上)"),
    "OLED 45°支架": (8.0, "无槽, 直接坐板面"),
    "LED 法兰":    (8.0, "无槽, 座圈坐板面"),
    "DHT11 座":    (8.0, "无槽, 自带底板坐板面"),
    "扎线座":      (8.0, "无槽, 坐板面"),
    "土壤":        (5.0, "在花盆内底上"),
    "水体":        (6.0, "在水箱内底上"),
    "水泵固定座":  (6.0, "在水箱内底上"),
    "水泵":        (9.0, "坐在水泵座内底"),
    "连接块":      (4.5, "沉槽 深3.5 -> 与板面齐平"),
    "LED 灯珠":    (8.9, "坐在 LED 座圈上"),
}

print("=" * 84)
print("① 落座高度核对")
print("=" * 84)
fails = []
seen = {}
for m, ck, nm in BA.items:
    lo, hi = m.bounds
    if lo[2] > PT + 1.0 or not nm or nm.startswith("底盘"):
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
for nm in ("花盆", "水箱", "面包板", "继电器", "LED 灯珠", "LED 法兰", "DHT11 座", "OLED 45°支架", "扎线座"):
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
    ("LED 安装孔 φ5.2 通孔 @(-22,18)",        not in_solid(-22, 18, 3.0), "z=3 处应是空(孔)"),
    ("LED 孔周边仍是实体 @(-30,18)",           in_solid(-30, 18, 3.0), "z=3 处应是实体"),
    ("ESP32 空槽已删除 @(-45,98)",             in_solid(-45, 98, 5.5), "z=5.5 处应已是实体"),
    ("面包板槽仍在 @(-140,-55)",               not in_solid(-140, -55, 5.5), "z=5.5 处应是空(槽)"),
    ("继电器槽仍在 @(-45,-20)",                not in_solid(-45, -20, 5.5), "z=5.5 处应是空(槽)"),
    ("花盆凹槽 @(-125,60)",                    not in_solid(-125, 60, 5.5), "z=5.5 处应是空(槽)"),
    ("水箱槽 @(120,20)",                       not in_solid(120, 20, 5.5), "z=5.5 处应是空(槽)"),
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
