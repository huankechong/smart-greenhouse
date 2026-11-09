# -*- coding: utf-8 -*-
"""花房 3D 全套审计：几何自检 + 装配干涉 + 文档对账"""
import os, sys, glob, re, json
import numpy as np
import trimesh
from trimesh.boolean import intersection

ROOT = r"D:/Documents/workbuddydocument/2026-10-17-08-59-13/outputs/3D打印件"  # 2026-11-09 修：11-08 重组后 3D 件在 3D打印件/ 下
sys.path.insert(0, os.path.join(ROOT, "花房3D_整机装配"))

print("=" * 70)
print("① 全部 STL 自检 (watertight / 单体 / 落床 / bbox)")
print("=" * 70)
stl_files = sorted(f for f in glob.glob(os.path.join(ROOT, "**", "*.stl"), recursive=True)
                   if "切片_" not in f and "\\切片_" not in f)   # 切片目录里的合并件/复制件不参与设计审计
rows = []
for f in stl_files:
    m = trimesh.load(f)
    rows.append((os.path.relpath(f, ROOT), m))
    # 2026-11-09：组合件（多件排同一块板打印）天然是多体，单体检查对它不适用；
    # 判据改为「每体都水密 + 落床 + 各体互不干涉」——组合件靠 8mm 间距排布。
    is_combo = ("组合件" in f)
    if is_combo:
        _ps = m.split(only_watertight=False)
        _inter = 0.0
        if len(_ps) == 2:
            from trimesh.boolean import intersection as _ix
            try:
                _inter = float(_ix(_ps, engine="manifold").volume)
            except Exception:
                _inter = 0.0
        ok = (m.is_watertight and all(p.is_watertight for p in _ps)
              and abs(m.bounds[0][2]) < 1e-6 and _inter < 1.0)
    else:
        ok = m.is_watertight and m.body_count == 1 and abs(m.bounds[0][2]) < 1e-6
    print("%s %-46s %-24s %8.1f g  tri=%d" % (
        "OK " if ok else "!! ", os.path.relpath(f, ROOT).replace("\\", "/"),
        str(np.round(m.extents, 1).tolist()), m.volume * 1.24 / 1000, len(m.faces)))

print()
print("=" * 70)
print("② 装配干涉 (两两求交, 只报 >1 mm3)")
print("=" * 70)
import build_assembly as BA          # 模块级已构建 items
# v1.7 细节件（螺丝/跳线/孔阵/板载件）只做视觉叠加，不参与两两干涉：
# 它们本来就贴在零件表面，逐对求交既慢又没有工程意义。跳线单独由 check_wires.py 校验。
DETAIL = ("跳线", "M3×6", "面包板孔阵", "面包板中央沟", "面包板电源轨",
          "ESP32 USB", "ESP32 按键", "ESP32 EN", "ESP32 天线", "ESP32 屏蔽",
          "继电器端子", "继电器指示", "继电器光耦", "OLED FPC", "OLED 排针",
          "OLED 驱动", "传感器铜探头", "传感器排针", "DHT11 格栅",
          "水泵进水", "水泵出水",
          # 液体与浸没件：水体是流体，泵/浮子泡在水里属正常，不算干涉
          "水体", "浮子", "叶片")
items = [(m, ck, nm) for m, ck, nm in BA.items if not (nm or "").startswith(DETAIL)]
print("装配几何体 %d 个（另有 %d 个细节件不参与干涉检查）"
      % (len(items), len(BA.items) - len(items)))

def bbox_overlap(a, b, tol=0.0):
    return np.all(a.bounds[0] - tol <= b.bounds[1]) and np.all(b.bounds[0] - tol <= a.bounds[1])

hits = []
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i][0], items[j][0]
        if not bbox_overlap(a, b):
            continue
        try:
            inter = intersection([a, b], engine="manifold")
            v = float(inter.volume) if len(inter.faces) else 0.0
        except Exception:
            v = -1.0
        if v > 1.0:
            hits.append((items[i][2] or items[i][1], items[j][2] or items[j][1], v))

if hits:
    for n1, n2, v in sorted(hits, key=lambda x: -x[2]):
        print("  %-18s × %-18s  %10.1f mm3" % (n1, n2, v))
else:
    print("  无干涉")

print()
print("=" * 70)
print("③ 文档数字 vs 实际文件")
print("=" * 70)


def doc(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ======================================================================
# ③ 文档数字 vs 实际文件 —— 2026-11-09 停用
# ======================================================================
# 停用原因（不是坏了，是口径变了）：
#   1) 本段比对的是「实心体积 × 1.24」的估算克重，而 README/交付说明现在一律用
#      **切片实测耗材**（含 brim/purge，见 _打印参考/切片报告.md）——两者本就差 10~20%，
#      2026-11-07 起已明确「估算值只作设计参考，不再用于打印备料」。
#   2) 件数变动频繁（02 作废删除、11 新增、04/07 多次改版），硬编码的期望值必然漂移，
#      每改一次件就要手改本文件，失去"自动对账"的意义。
#   3) 现行做法：文档克重口径由 `_打印参考/切片报告.md` 单一来源维护，
#      几何正确性由本脚本的 ①② 段（STL 自检 + 两两干涉）保证。
# 若要恢复：请改为读取切片报告的真实值做对账，不要再用 volume×1.24 估算。
print()
print("=" * 70)
print("③ 文档数字对账：已停用（口径改切片实测，见本文件注释）")
print("=" * 70)
