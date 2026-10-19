# -*- coding: utf-8 -*-
"""高清出图 + 爆炸图（复用 build_assembly 的几何与 AO，不重复烘焙）"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import build_assembly as BA

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# 爆炸图分三层：0=底盘（不动）/ 1=容器+自然物 / 2=电控与走线
LAYER_CONTAINER = ("花盆", "土壤", "主茎", "叶片", "水箱", "水体", "水泵")
LAYER_ELEC = ("面包板", "ESP32", "继电器", "OLED", "DHT11", "双色 LED", "LED",
              "土壤传感器板", "传感器盆沿挂钩", "扎线座", "水管", "跳线",
              "面包板孔阵", "面包板中央沟", "面包板电源轨", "M3×6 螺丝")
DZ = (0.0, 55.0, 110.0)


def _layer(nm):
    nm = nm or ""
    if nm.startswith("底盘") or nm == "连接块" or nm.startswith("M3×6"):
        return 0      # 拼接件属于第①步：拼成整块板
    if nm.startswith(LAYER_CONTAINER):
        return 1
    return 2


def render_explode(size, az, el):
    """三层语义爆炸：底盘 → 容器 → 电控（同层整体平移，不散件）"""
    dz_list = []
    for m, ck, nm in BA.items:
        dz = DZ[_layer(nm)]
        dz_list.append(dz)
        m.apply_translation([0, 0, dz])
    try:
        img = BA.render_scene(az, el, size)
    finally:
        for (m, ck, nm), dz in zip(BA.items, dz_list):
            m.apply_translation([0, 0, -dz])
    return img


def crop(img, pad=0.05):
    """按非白像素裁边，留 pad 比例白边（PPT 直接贴不发虚）"""
    m = (img < 0.995).any(axis=2)
    ys, xs = np.where(m)
    if len(ys) == 0:
        return img
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    h, w = y1 - y0, x1 - x0
    py, px = int(h * pad), int(w * pad)
    return img[max(0, y0 - py):min(img.shape[0], y1 + py),
               max(0, x0 - px):min(img.shape[1], x1 + px)]


def save(img, name):
    p = os.path.join(OUT, name)
    img = crop(np.clip(img, 0, 1))
    plt.imsave(p, img)
    print("  %-28s %4d x %-4d  %d KB" % (name, img.shape[1], img.shape[0],
                                         os.path.getsize(p) // 1024))


print("高清图（2000px 白底）:")
for az, el, name in [(42, 26, "01_高清_轴测.png"),
                     (8, 16, "02_高清_正视.png"),
                     (0, 89.5, "03_高清_俯视.png"),
                     (-58, 24, "04_高清_左后.png")]:
    save(BA.render_scene(az, el, 2000), name)

print("爆炸图:")
save(render_explode(1700, 34, 52), "05_爆炸图.png")


def render_stage(size, az, el, layers):
    """只渲染指定层（几何顺序与 AO 索引保持对齐）"""
    full_items, full_ao = BA.items, BA.get_ao()
    sel = [(i, it) for i, it in enumerate(full_items) if _layer(it[2]) in layers]
    BA.items = [it for _, it in sel]
    BA.AO_LIST = [full_ao[i] for i, _ in sel]
    try:
        return BA.render_scene(az, el, size)
    finally:
        BA.items = full_items
        BA.AO_LIST = full_ao


fig, axes = plt.subplots(1, 3, figsize=(21, 8.6), facecolor="white")
stages = [((0,), "① 整机底盘（两片 + 连接块 + 8 颗 M3×6）"),
          ((0, 1), "② 装入容器：花盆 + 土 + 水箱 + 水泵"),
          ((0, 1, 2), "③ 装入电控与走线：面包板 / ESP32 / 继电器 / 传感器")]
for ax, (layers, title) in zip(axes, stages):
    ax.imshow(crop(render_stage(1100, 38, 30, layers)))
    ax.set_title(title, fontsize=15, color="#111", pad=12)
    ax.axis("off")
fig.suptitle("装配顺序 · 一台板子三层", fontsize=20, color="#111")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fp = os.path.join(OUT, "06_装配三步.png")
fig.savefig(fp, dpi=150, facecolor="white")
plt.close(fig)
print("  06_装配三步.png           %d KB" % (os.path.getsize(fp) // 1024))
