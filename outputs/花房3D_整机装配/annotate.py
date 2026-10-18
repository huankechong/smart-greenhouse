# -*- coding: utf-8 -*-
"""给整机示意图加标注：花盆周边的白色/绿色结构各是什么"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_assembly as BA

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SIZE, AZ, EL = 1200, 42.0, 26.0

# ---- 复用 render_scene 的投影几何 ----
tri_list, col_list = [], []
light = np.array([0.40, 0.55, 0.73]); light /= np.linalg.norm(light)
for mesh, ck, _ in BA.items:
    n = mesh.face_normals
    shade = 0.42 + 0.58 * np.clip(n @ light, 0, 1)
    tri_list.append(mesh.triangles)
    col_list.append(np.array(BA.C[ck])[None, :] * shade[:, None])
tris = np.concatenate(tri_list)
cols = np.concatenate(col_list)

a, e = np.deg2rad(AZ), np.deg2rad(EL)
fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
right = np.cross([0, 0, 1.0], fwd); right /= np.linalg.norm(right)
up = np.cross(fwd, right)
v = tris.reshape(-1, 3)
tx = (v @ right).reshape(-1, 3)
ty = (v @ up).reshape(-1, 3)
tz = (v @ fwd).reshape(-1, 3)
x0m, x1m, y0m, y1m = tx.min(), tx.max(), ty.min(), ty.max()
pad = 0.05 * max(x1m - x0m, y1m - y0m)
sc = (SIZE - 1) / max(x1m - x0m + 2 * pad, y1m - y0m + 2 * pad)
sx = (tx - x0m + pad) * sc
sy = (SIZE - 1) - (ty - y0m + pad) * sc

img = np.ones((SIZE, SIZE, 3), dtype=np.float32)
zbuf = np.full((SIZE, SIZE), -1e9, dtype=np.float32)
for i in np.argsort(tz.min(axis=1)):
    ax0, ay0, az = sx[i], sy[i], tz[i]
    bx0 = max(int(np.floor(ax0.min())), 0); bx1 = min(int(np.ceil(ax0.max())), SIZE - 1)
    by0 = max(int(np.floor(ay0.min())), 0); by1 = min(int(np.ceil(ay0.max())), SIZE - 1)
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
    sub = zbuf[by0:by1 + 1, bx0:bx1 + 1]
    closer = ins & (depth > sub)
    if not closer.any():
        continue
    sub[closer] = depth[closer]
    img[by0:by1 + 1, bx0:bx1 + 1][closer] = cols[i]


def proj(p):
    p = np.asarray(p, dtype=float)
    return (p @ right - x0m + pad) * sc, (SIZE - 1) - (p @ up - y0m + pad) * sc


# ---- 标注：编号徽标 + 左侧图例块（不用长箭头，避免全挤到一处）----
MARKS = [
    (1, (-135, 40, 96), "土壤湿度传感器",
     "白：盆沿挂钩（打印件，跨在盆沿上）\n绿：传感器板斜插入土，盆里不占位置", "#3fa15a"),
    (2, (-45, -52, 66), "DHT11 温湿度",
     "白：立柱小座（打印件）\n绿：DHT11 模块，已移到继电器后方不挡屏", "#3fa15a"),
    (3, (-69.6, 47.1, 86), "水管末端夹",
     "白：卡在盆沿的小夹子\n把出水口固定在土面上方", "#6b7280"),
    (4, (-90, 78, 112), "植株",
     "绿色叶片是真植物示意\n不是打印件，仅作场景", "#3fa15a"),
]

fig, ax = plt.subplots(figsize=(13, 11), facecolor="white")
ax.imshow(img)
ax.set_xlim(0, SIZE); ax.set_ylim(SIZE, 0)
ax.set_aspect("equal"); ax.axis("off")

# 编号徽标
for num, p3, _, _, _ in MARKS:
    px, py = proj(p3)
    ax.plot([px], [py], "o", ms=26, mfc="white", mec="#1b2028", mew=2.0, zorder=5)
    ax.text(px, py + 1, str(num), fontsize=15, weight="bold", color="#1b2028",
            ha="center", va="center", zorder=6)

# 左侧图例块
x0, y0, w = 40, 110, 545
row_h = 108
h = 68 + len(MARKS) * row_h
ax.add_patch(plt.Rectangle((x0, y0), w, h, fc="white", ec="#c9d2df", lw=1.4, zorder=3))
ax.text(x0 + 28, y0 + 34, "花盆周边结构", fontsize=17, weight="bold", color="#111",
        va="center", zorder=4)
for i, (num, _, title, desc, _c) in enumerate(MARKS):
    yy = y0 + 88 + i * row_h
    ax.plot([x0 + 36], [yy], "o", ms=24, mfc="white", mec="#1b2028", mew=1.8, zorder=5)
    ax.text(x0 + 36, yy + 1, str(num), fontsize=13.5, weight="bold", color="#1b2028",
            ha="center", va="center", zorder=6)
    ax.text(x0 + 72, yy - 11, title, fontsize=14, weight="bold", color="#111",
            va="center", zorder=4)
    ax.text(x0 + 72, yy + 9, desc, fontsize=11, color="#4a5563", va="top",
            linespacing=1.6, zorder=4)

fig.suptitle("花盆周边的白色 / 绿色结构是什么", fontsize=20, color="#111", y=0.972)
fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)
out = os.path.join(HERE, "preview", "01_花盆周边结构标注.png")
fig.savefig(out, dpi=150, facecolor="white")
plt.close(fig)
print("saved:", out)
