# -*- coding: utf-8 -*-
"""S4-12.3 全量长跑曲线（四段拼接）。只读 48h全量.csv，所有标注数字现算，不引用文档。

用法（必须在项目根目录运行，路径为项目根相对路径）：
    python outputs/代码/工具/plot_48h_full.py
输出：outputs/素材/素材整理_2026-11-22/S4-12.3-48h全量曲线_四段拼接.png

判据说明：土壤"有效时长"取段 2 中最后一个 <100% 的记录时刻（起表时土壤饱和，开头几行 100% 属正常，
不能用"首个=100"判定）。段 4 仅 5 条（修板后首 50 s），不占主轴，以插图呈现。
"""
import csv, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
SRC = 'outputs/素材/素材整理_2026-11-22/48h全量.csv'
OUT = 'outputs/素材/素材整理_2026-11-22/S4-12.3-48h全量曲线_四段拼接.png'
rows = list(csv.DictReader(open(SRC, encoding='utf-8')))
segs, cur = [], []
for r in rows:
    if r['sec'] == '#BOOT':
        if cur: segs.append(cur); cur = []
    else: cur.append(r)
if cur: segs.append(cur)
def arr(s, k, f=int):
    return np.array([f(r[k]) if r[k] not in ('-999', '') else np.nan for r in s])
dur = [int(s[-1]['sec']) / 3600 for s in segs]
total, longest, reboots = sum(dur), max(dur), len(segs) - 1
n_all = sum(len(s) for s in segs)
soil2 = arr(segs[1], 'soil_pct'); sec2 = np.array([int(r['sec']) for r in segs[1]]) / 3600
lv = int(np.where(soil2 < 100)[0][-1]); soil_valid_h = sec2[lv]
lo_s, hi_s = soil2[:lv + 1].min(), soil2[:lv + 1].max()
print(f"累计 {total:.2f}h | 最长单段 {longest:.2f}h | 重启 {reboots} | {n_all} 条 | 土壤有效 {soil_valid_h:.2f}h ({lo_s:.0f}-{hi_s:.0f}%)")
GAP = 0.6; main = segs[:3]; x = []; bounds = []; t0 = 0.0
for s in main:
    sec = np.array([int(r['sec']) for r in s]) / 3600.0
    x.append(sec + t0); bounds.append((t0, t0 + sec[-1])); t0 += sec[-1] + GAP
GREEN, RED = "#16a34a", "#dc2626"
fig = plt.figure(figsize=(16, 13.5), facecolor="white")
gs = fig.add_gridspec(4, 1, height_ratios=[1.25, 1, 1, 0.55], hspace=0.16, left=0.06, right=0.985, top=0.93, bottom=0.065)
ax = [fig.add_subplot(gs[i]) for i in range(4)]
# ===== 土壤 =====
a = ax[0]; a.axhspan(0, 15, color="#fecaca", alpha=.7)
a.text(bounds[0][1] + 0.8, 7.5, "浇水触发阈值（记录期间 3%；2026-11-22 定稿 15%）", fontsize=9, color="#b91c1c")
for i in range(3):
    so = arr(main[i], 'soil_pct')
    if i == 1:
        a.plot(x[i][:lv + 1], so[:lv + 1], color=GREEN, lw=0.9)
        a.plot(x[i][lv:], so[lv:], color=RED, lw=1.3)
    else:
        a.plot(x[i], so, color=(RED if so.min() >= 100 else GREEN), lw=1.0)
a.set_ylim(-3, 108); a.set_ylabel("土壤湿度 %", fontsize=11)
a.set_title("智能花房养护站 · 本地长跑记录（板端 LittleFS CSV，按时间拼接）", fontsize=15, loc="left", pad=10)
k = int(lv * 0.5)
a.annotate(f"土壤有效 {soil_valid_h:.1f} h（中位 {np.median(soil2[:lv+1]):.0f}%，{lo_s:.0f}–95% 波动）", xy=(x[1][k], soil2[k]), xytext=(19.5, 60),
           fontsize=9.5, color="#166534", va="top", arrowprops=dict(arrowstyle="->", color="#166534", lw=1.1))
a.annotate("11-20 12:00 后锁死 100%\n面包板 GND 轨接触不良", xy=(bounds[1][1] - 0.15, 100), xytext=(bounds[1][1] + 3.5, 84),
           fontsize=9.5, color="#991b1b", va="top", arrowprops=dict(arrowstyle="->", color="#991b1b", lw=1.1))
a.legend(handles=[Patch(color=GREEN, label="数据有效"), Patch(color=RED, label="失效（锁死量程端点）")],
         loc="lower right", fontsize=9, frameon=False, ncol=2)
# ===== 光照 =====
a = ax[1]
for i in range(3): a.plot(x[i], arr(main[i], 'lux'), color="#d97706", lw=0.7)
a.axhline(4000, color="#9ca3af", ls="--", lw=1)
a.text(bounds[0][1] + 0.8, 3700, "暗态 ADC 饱和（≈4095）：夜间平顶，仅白天可定量", fontsize=9, color="#6b7280", va="bottom", bbox=dict(boxstyle="round,pad=0.25",fc="white",ec="none",alpha=.85))
a.set_ylim(0, 4300); a.set_ylabel("光照 raw", fontsize=11)
# ===== 温湿度 =====
a = ax[2]
for i in range(3):
    a.plot(x[i], arr(main[i], 'temp', float), color="#ea580c", lw=1.0, label="温度 ℃" if i == 0 else None)
    a.plot(x[i], arr(main[i], 'hum'), color="#0d9488", lw=1.0, label="环境湿度 %" if i == 0 else None)
T = [arr(s, 'temp', float) for s in main]; H = [arr(s, 'hum') for s in main]
ylo, yhi = min(np.nanmin(t) for t in T) - 4, max(np.nanmax(h) for h in H) + 4
a.set_ylim(ylo, yhi); a.set_ylabel("温度 ℃ / 气湿 %", fontsize=11)
a.legend(loc="lower right", bbox_to_anchor=(0.80, 0.02), fontsize=9, ncol=2, frameon=True, framealpha=.95, edgecolor="none")
# ===== 状态带 =====
a = ax[3]; cols = {"待命": "#86efac", "等土吸水": "#fde047"}
for i in range(3):
    a.fill_between(x[i], 0, 1, color=[cols.get(r['state'], "#e5e7eb") for r in main[i]], step="mid", lw=0)
a.set_yticks([]); a.set_ylim(0, 2.05); a.set_ylabel("状态", fontsize=11)
a.legend(handles=[Patch(color="#86efac", label="待命（未触发浇水）")], loc="upper left", fontsize=9, frameon=False)
for (_, e) in bounds[1:]:
    for kk in range(4): ax[kk].axvspan(e - GAP, e, color="#fca5a5", alpha=(.75 if kk == 3 else .3), lw=0)
for i, (s, e) in enumerate(bounds):
    lab = f"段 {i + 1}　{e - s:.2f} h" + ("　← 最长单段" if abs((e - s) - longest) < 1e-6 else "")
    ax[3].text((s + e) / 2, 1.58, lab, ha="center", va="center", fontsize=9.5, color="#374151", clip_on=False)
    if i < 2: ax[3].text(e - GAP / 2, 1.58, "重启", ha="center", va="center", fontsize=8.5, color="#b91c1c", clip_on=False)
ax[3].set_xlabel(f"运行时间（h）　累计 {total:.1f} h = 四段之和；红色竖缝 = 重启（共 {reboots} 次）", fontsize=11)
fig.text(0.985, 0.985, f"数据 {n_all:,} 条 · 累计约 {total:.0f} h（跨 {reboots} 次重启）· 最长单段连续 {longest:.2f} h · 土壤通道有效 {soil_valid_h:.1f} h",
         ha="right", va="top", fontsize=10.5, color="#374151")
# ===== 插图：段 4 =====
ins = ax[0].inset_axes([0.655, 0.30, 0.235, 0.46])
s4 = segs[3]; t4 = np.array([int(r['sec']) for r in s4]); so4 = arr(s4, 'soil_pct')
ins.plot(t4, so4, "o-", color="#7c3aed", lw=1.4, ms=4)
for xx, yy in zip(t4, so4): ins.annotate(f"{yy:.0f}", (xx, yy), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
ins.set_ylim(-6, 66); ins.set_title("段 4：修板后重插传感器首 50 s", fontsize=8.5, color="#6d28d9", pad=4)
ins.set_xlabel("秒", fontsize=8); ins.tick_params(labelsize=7.5); ins.set_facecolor("#faf5ff")
for sp in ins.spines.values(): sp.set_color("#d8b4fe")
fig.savefig(OUT, dpi=150, facecolor="white"); plt.close(fig); print("已重画:", OUT)
