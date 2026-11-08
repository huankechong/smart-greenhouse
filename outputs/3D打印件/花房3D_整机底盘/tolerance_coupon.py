# -*- coding: utf-8 -*-
"""配合公差测试块（2026-11-08）
用途：0.4 喷嘴 + 0.2 层高下，实测「件能一放就进、又不晃」的间隙。
做法：底板 105×30×5，三个槽按 08 扎线座底板（33×20）放大，
      单边间隙 0.10 / 0.20 / 0.30（从左到右），槽深 2、槽口 0.6×45° 倒角。
"""
import os, numpy as np, trimesh
from trimesh.creation import box
from trimesh.boolean import difference, union

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STL")
os.makedirs(OUT, exist_ok=True)

pw, ph, pt = 30.0, 16.0, 2.0          # 08 底板（实测 30×16×2）
plate_x, plate_y, plate_t = 96.0, 26.0, 5.0
gaps = (0.10, 0.20, 0.30)

body = box(extents=[plate_x, plate_y, plate_t])
body.apply_translation([0, 0, plate_t / 2])

cuts = []
for i, g in enumerate(gaps):
    x = -32.0 + i * 32.0
    w, h = pw + 2 * g, ph + 2 * g
    cuts.append(box(extents=[w, h, pt + 2]).apply_translation([x, 0, plate_t - pt / 2]))
    # 槽口 0.6×45° 倒角
    h0 = w / 2.0
    hh = 1.6
    v = np.array([[-h0, -h0, plate_t - 0.6], [h0, -h0, plate_t - 0.6],
                  [h0, h0, plate_t - 0.6], [-h0, h0, plate_t - 0.6],
                  [-(h0 + hh), -(h0 + hh), plate_t - 0.6 + hh], [(h0 + hh), -(h0 + hh), plate_t - 0.6 + hh],
                  [(h0 + hh), (h0 + hh), plate_t - 0.6 + hh], [-(h0 + hh), (h0 + hh), plate_t - 0.6 + hh]])
    f = np.array([[0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                  [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    ch = trimesh.Trimesh(vertices=v, faces=f, process=True)
    ch.fix_normals()
    ch.apply_translation([x, 0, 0])
    cuts.append(ch)

body = difference([body] + cuts, engine="manifold")
p = os.path.join(OUT, "测试块_配合公差_v1.stl")
body.export(p)
print("bbox", np.round(body.extents, 1).tolist(), " 体积 %.0f mm3 (%.1f g)" %
      (body.volume, body.volume * 1.24 / 1000), " watertight", body.is_watertight, "->", p)
