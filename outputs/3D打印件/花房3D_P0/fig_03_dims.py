# -*- coding: utf-8 -*-
"""03 水管末端固定夹 · 带尺寸三视图（数据直接读 p0_models.PARAMS["clip"]，不手抄）

用法： python fig_03_dims.py            # 出 preview/03_尺寸图.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

import p0_models as M

PLT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

C_COL, C_PIN, C_RED, C_GREY, C_OR = "#c9d3de", "#dfe4ea", "#c0392b", "#7f8c8d", "#e67e22"


def dim(ax, x0, y0, x1, y1, t="", off=(0, 0), fs=9, rot=0, color="black"):
    ax.annotate("", xy=(x0, y0), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", lw=0.9, color=color))
    if t:
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], t,
                ha="center", va="center", fontsize=fs, rotation=rot, color=color)


def mass_g():
    """从已出的 STL 现算克重，避免图和件脱节"""
    import json
    rep = os.path.join(PLT, "check_report.json")
    if os.path.exists(rep):
        with open(rep, encoding="utf-8") as f:
            for r in json.load(f):
                if r["name"].startswith("03_tube_clip"):
                    return r["est_mass_g_PLA"]
    return float("nan")


def main():
    p = M.PARAMS["clip"]
    bore_r = p["ring_inner_d"] / 2
    pt, pw, pd = p["pin_t"], p["pin_w"], p["pin_depth"]
    tt, tw, tl = p["pin_tip_t"], p["pin_tip_w"], p["pin_tip_len"]
    px, ch, cx = p["pin_x"], p["col_h"], p["col_x"]
    cd = p["col_d"]
    total = pd + ch
    wall = (cx - p["ring_inner_d"]) / 2

    fig, axs = plt.subplots(1, 3, figsize=(15.0, 7.6), facecolor="white")

    # ================= 正视 X-Z =================
    ax = axs[0]
    ax.set_title("正视（X-Z，看针厚）", fontsize=12)
    for sx in (-1, 1):
        x = sx * px
        ax.add_patch(Polygon(
            [(x - pt / 2, pd), (x + pt / 2, pd), (x + pt / 2, tl),
             (x + tt / 2, 0), (x - tt / 2, 0), (x - pt / 2, tl)],
            closed=True, facecolor=C_PIN, edgecolor="#333", lw=0.8))
    ax.add_patch(Rectangle((-cx / 2, pd), cx, ch, facecolor=C_COL, edgecolor="#333", lw=1))
    for sx in (-1, 1):
        ax.plot([sx * bore_r, sx * bore_r], [pd, pd + ch], ls=(0, (3, 2)), color=C_RED, lw=1.2)
    ax.axhline(pd, color=C_GREY, ls="--", lw=1)
    ax.text(-cx / 2 - 7.4, pd + 0.9, "土面", fontsize=8.5, color=C_GREY)
    dim(ax, -cx / 2 - 3.4, 0, -cx / 2 - 3.4, total, "%d" % total, off=(-1.5, 0), rot=90)
    dim(ax, cx / 2 + 2.2, pd, cx / 2 + 2.2, total, "%d" % ch, off=(1.5, 0))
    dim(ax, cx / 2 + 2.2, 0, cx / 2 + 2.2, pd, "针 %d" % pd, off=(2.3, 0))
    ax.annotate("", xy=(cx / 2 + 2.2, 0), xytext=(cx / 2 + 2.2, tl),
                arrowprops=dict(arrowstyle="<->", lw=1.2, color=C_RED))
    ax.text(cx / 2 + 4.6, tl / 2, "锥段 %d" % tl, fontsize=8.5, color=C_RED, va="center")
    ax.text(0, -6.5, "针厚 %.1f（尖端收至 %.1f）" % (pt, tt), ha="center", fontsize=9, color="#444")
    ax.text(0, total + 4.8, "红线 = 管孔 φ%.1f 隐藏线" % p["ring_inner_d"],
            ha="center", fontsize=8.5, color=C_RED)
    ax.set_xlim(-cx / 2 - 11, cx / 2 + 12)
    ax.set_ylim(-11, total + 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # ================= 侧视 Y-Z =================
    ax = axs[1]
    ax.set_title("侧视（Y-Z，看针宽）", fontsize=12)
    ax.add_patch(Polygon(
        [(-pw / 2, pd), (pw / 2, pd), (pw / 2, tl),
         (tw / 2, 0), (-tw / 2, 0), (-pw / 2, tl)],
        closed=True, facecolor=C_PIN, edgecolor="#333", lw=0.8))
    ax.add_patch(Rectangle((-cd / 2, pd), cd, ch, facecolor=C_COL, edgecolor="#333", lw=1))
    for sy in (-1, 1):
        ax.plot([sy * bore_r, sy * bore_r], [pd, pd + ch], ls=(0, (3, 2)), color=C_RED, lw=1.2)
    ax.axhline(pd, color=C_GREY, ls="--", lw=1)
    dim(ax, -cd / 2 - 3.4, pd, -cd / 2 - 3.4, total, "%d" % ch, off=(-1.5, 0), rot=90)
    ax.text(cd / 2 + 2.0, pd + ch / 2, "柱体深 %d" % cd, fontsize=8.5, va="center")
    dim(ax, -cd / 2, total + 6.5, cd / 2, total + 6.5, "%d" % cd, off=(0, 1.5))
    ax.text(0, -6.5, "针宽 %.1f（尖端收至 %.1f）" % (pw, tw), ha="center", fontsize=9, color="#444")
    ax.set_xlim(-cx / 2 - 11, cx / 2 + 12)
    ax.set_ylim(-11, total + 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # ================= 俯视 X-Y =================
    ax = axs[2]
    ax.set_title("俯视（X-Y，看管孔）", fontsize=12)
    ax.add_patch(Rectangle((-cx / 2, -cd / 2), cx, cd, facecolor=C_COL, edgecolor="#333", lw=1))
    ax.add_patch(Circle((0, 0), bore_r, facecolor="white", edgecolor=C_RED, lw=1.8))
    for sx in (-1, 1):
        ax.add_patch(Rectangle((sx * px - pt / 2, -pw / 2), pt, pw,
                               facecolor="none", edgecolor=C_OR, lw=1.1, ls=(0, (4, 2))))
        ax.plot([sx * px, sx * px], [cd / 2 + 0.3, cd / 2 + 3.2], ls=":", color="#888", lw=0.8)
    ax.annotate("", xy=(-bore_r, 0), xytext=(bore_r, 0),
                arrowprops=dict(arrowstyle="<->", lw=1, color=C_RED))
    ax.text(0, -2.6, "φ%.1f" % p["ring_inner_d"], ha="center", fontsize=9.5, color=C_RED)
    dim(ax, -px, cd / 2 + 3.2, px, cd / 2 + 3.2)
    ax.text(0, cd / 2 + 4.4, "针距 %.1f" % (2 * px), ha="center", fontsize=8.5)
    ax.text(0, -cd / 2 - 5.4,
            "柱体 %d×%d · 单边壁厚 %.1f\n橙虚线 = 柱底以下的插土针（完全在管孔外）" % (cx, cd, wall),
            ha="center", fontsize=8.5, color="#444")
    lim = cx / 2 + 3.5
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim - 2.5, lim + 6)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.suptitle("03 水管末端固定夹 · 尺寸 v2（%.1f g · PLA · %d×%d×%d）"
                 % (mass_g(), cx, cd, total), fontsize=13.5)
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(PLT, "preview", "03_尺寸图.png")
    plt.savefig(out, dpi=150, facecolor="white")
    print("saved", out)


if __name__ == "__main__":
    main()
