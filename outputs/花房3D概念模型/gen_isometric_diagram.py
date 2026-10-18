# -*- coding: utf-8 -*-
"""
花房 Final Project 系统等轴测概念图生成器
复用 v3.3 已审计的 3D 布局坐标，等轴测投影生成精确 SVG 矢量图。
用法: python gen_isometric_diagram.py -> 花房系统等轴测图.svg + .html
坐标: 与 3D 模型一致 (Y向上, 底板顶面y=0)
投影: sx=(x-z)*cos30*S+cx, sy=(cy-(x+z)*sin30+y)*S  (屏幕y向下)
"""
import math

COS30, SIN30 = math.cos(math.radians(30)), 0.5
S = 2.3          # 缩放
CX, CY = 780, 560   # 画布中心锚点
W, H = 1560, 1150

def proj(x, y, z):
    return (CX + (x - z) * COS30 * S,
            CY - ((x + z) * SIN30 + y) * S)

# ---------- 配色 ----------
PAL = {
    "base":  ("#8f99a3", "#6f7982", "#5b646d"),   # top, left(z+), right(x+)
    "bread": ("#e8eaee", "#c9cdd6", "#b3b8c4"),
    "esp":   ("#3a3d44", "#2b2d33", "#1f2126"),
    "tank":  ("#cfe3f7", "#b3cdec", "#9cc0e2"),
    "water": ("#7db8f0", "#5da3e8", "#4a92dd"),
    "pump":  ("#4a4e57", "#383c44", "#2c2f36"),
    "pot":   ("#c9773f", "#b0622f", "#985426"),
    "soil":  ("#5d4530", "#4c3826", "#3f2e20"),
    "rim":   ("#d98a4d", "#c2743a", "#a86330"),
    "brk":   ("#f7f8fa", "#dfe3e9", "#cdd3dc"),    # 白色打印件
    "oled":  ("#f7f8fa", "#dfe3e9", "#cdd3dc"),
    "scr":   ("#14161a", "#0e1013", "#0a0c0f"),
    "leaf":  ("#4caf50", "#43a047", "#388e3c"),
    "stem":  ("#3d8b40", "#33763a", "#2a6230"),
    "tube":  "#2f7fd6",
    "w": {"红": "#d84a3f", "黑": "#3a3f46", "黄": "#e6b422", "蓝": "#3b6fd6", "棕": "#8a5a34"},
    "ink":   "#2b3440",
    "sub":   "#5f6b78",
    "line":  "#9aa7b4",
    "accent":"#e8722a",
}

svg = []
def tag(s): svg.append(s)

def iso_box(name, c, size, pal, opacity=1.0, stroke="#00000022"):
    """c=中心(x,y,z) size=(w,h,d) 画top/left(z+)/right(x+)三面"""
    w2, h2, d2 = size[0]/2, size[1]/2, size[2]/2
    x, y, z = c
    top = [proj(x-w2, y+h2, z-d2), proj(x+w2, y+h2, z-d2), proj(x+w2, y+h2, z+d2), proj(x-w2, y+h2, z+d2)]
    left = [proj(x-w2, y+h2, z+d2), proj(x+w2, y+h2, z+d2), proj(x+w2, y-h2, z+d2), proj(x-w2, y-h2, z+d2)]
    right = [proj(x+w2, y+h2, z-d2), proj(x+w2, y+h2, z+d2), proj(x+w2, y-h2, z+d2), proj(x+w2, y-h2, z-d2)]
    op = f' opacity="{opacity}"' if opacity < 1 else ''
    for face, pts, shade in ((top, top, 0), (left, left, 1), (right, right, 2)):
        p = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        tag(f'<polygon points="{p}" fill="{pal[shade]}" stroke="{stroke}" stroke-width="1"{op}/>')

def iso_cyl(name, c, r_top, r_bot, h, pal, opacity=1.0):
    """竖直圆柱: 侧面剪影 + 顶椭圆"""
    x, y, z = c
    rxt, ryt = r_top*1.2247*S, r_top*0.7071*S
    rxb, ryb = r_bot*1.2247*S, r_bot*0.7071*S
    tx, ty = proj(x, y+h/2, z)
    bx, by = proj(x, y-h/2, z)
    op = f' opacity="{opacity}"' if opacity < 1 else ''
    tag(f'<path d="M{tx-rxt:.1f},{ty:.1f} L{bx-rxb:.1f},{by:.1f} '
        f'A{rxb:.1f},{ryb:.1f} 0 0 0 {bx+rxb:.1f},{by:.1f} '
        f'L{tx+rxt:.1f},{ty:.1f} Z" fill="{pal[2]}" stroke="#00000022" stroke-width="1"{op}/>')
    # 侧渐变近似: 中间竖条
    tag(f'<path d="M{tx-rxt*0.45:.1f},{ty:.1f} L{bx-rxb*0.45:.1f},{by:.1f} '
        f'A{rxb*0.45:.1f},{ryb*0.45:.1f} 0 0 0 {bx+rxb*0.45:.1f},{by:.1f} '
        f'L{tx+rxt*0.45:.1f},{ty:.1f} Z" fill="{pal[1]}" stroke="none"{op}/>')
    tag(f'<ellipse cx="{tx:.1f}" cy="{ty:.1f}" rx="{rxt:.1f}" ry="{ryt:.1f}" fill="{pal[0]}" stroke="#00000022" stroke-width="1"{op}/>')

def circle(name, c, r, fill, opacity=1.0, stroke="none"):
    px, py = proj(*c)
    op = f' opacity="{opacity}"' if opacity < 1 else ''
    tag(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r*1.2247*S:.1f}" fill="{fill}" stroke="{stroke}"{op}/>')

def polyline(name, pts, color, width, dash=None):
    p = " ".join(f"{a:.1f},{b:.1f}" for a, b in (proj(*q) for q in pts))
    d = f' stroke-dasharray="{dash}"' if dash else ''
    tag(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round"{d}/>')

# ================= 部件布局（与 v3.3 审计通过的 3D 模型一致） =================
# 1 底板
iso_box("base", (0, -2.5, 0), (320, 5, 230), PAL["base"])
# 2 OLED 座(左前)
iso_box("oled_base", (-95, 6, -62), (70, 12, 50), PAL["oled"])
iso_box("oled_panel", (-95, 32, -58), (52, 40, 5), PAL["oled"])
iso_box("oled_scr", (-95, 33, -55), (40, 30, 2), PAL["scr"])
# 3 面包板区(左后)
iso_box("bread", (-30, 4, -5), (60, 8, 170), PAL["bread"])
iso_box("esp", (-30, 9.5, -5), (28, 3, 55), PAL["esp"])
# LED ×2 + 灯罩
iso_cyl("led1", (-38, 12, 70), 3, 3, 8, PAL["esp"])
iso_cyl("led2", (-22, 12, 70), 3, 3, 8, PAL["esp"])
circle("shade", (-30, 17, 70), 10, "#ffffff", 0.42, stroke="#c9cdd6")
# 4 水箱区(右后)
iso_box("tank", (80, 55, -50), (150, 110, 90), PAL["tank"], 0.30)
iso_box("water", (80, 31, -50), (134, 55, 74), PAL["water"], 0.62)
iso_cyl("pump", (80, 15, -50), 16, 16, 30, PAL["pump"])
iso_cyl("pump_m", (80, 4, -50), 21, 21, 7, PAL["brk"])
# 5 花盆区(右前)
iso_cyl("pot", (55, 47.5, 55), 55, 40, 95, PAL["pot"])
iso_cyl("soil", (55, 92, 55), 48, 48, 5, PAL["soil"])
iso_cyl("rim", (55, 92, 55), 57, 57, 6, PAL["rim"])
iso_cyl("stem", (55, 120, 55), 3, 4, 55, PAL["stem"])
for (lx, ly, lz, lr) in [(55,152,55,17), (44,138,66,14), (66,142,44,13), (52,164,42,11), (68,158,62,12), (55,172,55,9)]:
    circle("leaf", (lx, ly, lz), lr, PAL["leaf"][0])
# 6 传感器(盆后沿)
iso_box("sen_v", (55, 70, 102), (30, 48, 4), PAL["brk"])
iso_box("sen_b", (55, 74, 99), (22, 30, 3), ("#5b8bd6", "#4a79c4", "#3d67ad"))
iso_box("pr1", (49, 79, 99), (2.5, 26, 1.5), PAL["bread"])
iso_box("pr2", (61, 79, 99), (2.5, 26, 1.5), PAL["bread"])
iso_box("arm", (55, 96, 101), (34, 4, 18), PAL["brk"])
# 7 水路
polyline("tube", [(120,0,25), (120,113,25), (75,124,55), (95,106,75), (70,109,60)], PAL["tube"], 6)
iso_box("clamp", (95, 104, 75), (12, 9, 12), PAL["brk"])
circle("noz", (70, 108, 60), 5, PAL["tube"][0])
# 8 线缆（三束, 简化平行线）
def bundle(pts_list, colors, w=2.4):
    for i, col in enumerate(colors):
        off = (i - (len(colors)-1)/2) * 3.5
        pts = [(x+off, y, z+off*0.5) for x, y, z in pts_list]
        polyline("wire", pts, PAL["w"][col], w)
bundle([(55, 90, 99), (55, 104, 99), (-30, 104, 60), (-30, 10, 60)], ["红", "黄", "黑"])           # 传感器3线
bundle([(-95, 4, -36), (-95, 3, 20), (-50, 9, 50)], ["红", "黑", "黄", "蓝"])                      # OLED 4线
bundle([(80, 30, -50), (80, 114, -50), (10, 114, -78), (10, 6, -78), (-10, 9, -78)], ["蓝", "棕"]) # 水泵2线

# ================= 标注 =================
def label(text, anchor3, lx, ly, sub=None, badge=None):
    ax, ay = proj(*anchor3)
    tag(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="4" fill="{PAL["accent"]}"/>')
    tag(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx}" y2="{ly}" stroke="{PAL["line"]}" stroke-width="1.3"/>')
    tag(f'<circle cx="{lx}" cy="{ly}" r="2.6" fill="{PAL["line"]}"/>')
    tx = lx + (10 if lx >= CX else -10)
    anch = 'start' if lx >= CX else 'end'
    tag(f'<text x="{tx}" y="{ly-2}" font-size="21" font-weight="600" fill="{PAL["ink"]}" text-anchor="{anch}">{text}</text>')
    if sub:
        tag(f'<text x="{tx}" y="{ly+20}" font-size="16" fill="{PAL["sub"]}" text-anchor="{anch}">{sub}</text>')
    if badge:
        bw = 20 + 11*len(badge)
        bx0 = lx + (12 if lx >= CX else -12 - bw)
        tag(f'<rect x="{bx0}" y="{ly+(12 if sub else 6)}" width="{bw}" height="24" rx="12" fill="{PAL["accent"]}"/>')
        tag(f'<text x="{bx0+bw/2}" y="{ly+(12 if sub else 6)+17}" font-size="15" font-weight="700" fill="#fff" text-anchor="middle">{badge}</text>')

label("花盆 · 绿植", (55, 60, 55), 1315, 240, sub="被监控对象")
label("土壤传感器 + L 支架", (55, 88, 100), 1315, 350, sub="M3 孔位×2 · 探针入土", badge="P0-1")
label("出水口 + 水管固定夹", (70, 108, 60), 1315, 470, sub="土面上方固定落水点", badge="P0-3")
label("蓄水箱（透明）", (110, 95, -80), 1315, 610, sub="水箱水位可视")
label("底吸水泵 + 固定座", (80, 15, -50), 1315, 720, sub="防倒防震 · 卡爪固定", badge="P0-2")
label("浇水管路", (110, 100, 30), 1315, 840, sub="泵送 → 立管 → 过顶 → 落水")
label("面包板 + ESP32 主控", (-30, 12, -5), 245, 300, sub="系统控制核心")
label("状态灯 红绿 + 扩散灯罩", (-28, 18, 70), 245, 440, sub="远距可视工况", badge="P1-5")
label("OLED 45° 显示座", (-95, 40, -58), 245, 590, sub="实时数据朝向观众", badge="P1-4")
label("整合底板", (-150, 3, 105), 245, 750, sub="全系统承载 · 四角安装孔", badge="P1-6")
label("三路线缆", (-10, 114, -78), 245, 890, sub="传感器3线 / OLED 4线 / 水泵2线")

# 图例
lx0, ly0 = 470, 1010
tag(f'<text x="{lx0-120}" y="{ly0+5}" font-size="19" font-weight="700" fill="{PAL["ink"]}">图例</text>')
legend = [("#5b646d", "结构"), ("#dfe3e9", "3D 打印件"), ("#2b2d33", "电子件"),
          ("#2f7fd6", "水路"), ("#4caf50", "植物"), ("#e8722a", "P0/P1 = 待打印件")]
xx = lx0
for col, txt in legend:
    if txt.startswith("P0"):
        tag(f'<text x="{xx}" y="{ly0+6}" font-size="17" fill="{PAL["sub"]}">{txt}</text>')
        xx += 26 + 10*len(txt)
    else:
        tag(f'<rect x="{xx}" y="{ly0-12}" width="26" height="16" rx="3" fill="{col}" stroke="#00000030"/>')
        tag(f'<text x="{xx+34}" y="{ly0+2}" font-size="17" fill="{PAL["sub"]}">{txt}</text>')
        xx += 34 + 10*len(txt) + 24

# 标题
tag(f'<text x="60" y="72" font-size="34" font-weight="800" fill="{PAL["ink"]}">花房 Final Project · 系统等轴测概念图</text>')
tag(f'<text x="60" y="104" font-size="18" fill="{PAL["sub"]}">GreenHouse Monitoring System — Isometric Concept Layout · v1.0 · 2026-10-18</text>')

svg_body = "\n".join(svg)
doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="\'Noto Sans SC\','
       f"'Microsoft YaHei', sans-se"
       f'rif">\n<rect width="{W}" height="{H}" fill="#fbfcfe"/>\n{svg_body}\n</svg>')

with open("花房系统等轴测图.svg", "w", encoding="utf-8") as f:
    f.write(doc)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>花房 Final Project · 系统等轴测概念图</title>
<style>
 body {{ margin:0; background:#eef1f5; display:flex; flex-direction:column; align-items:center;
        font-family:'Noto Sans SC','Microsoft YaHei',sans-serif; }}
 .bar {{ width:100%; background:#fff; padding:14px 0; text-align:center;
        box-shadow:0 1px 4px #0001; }}
 .bar h1 {{ margin:0; font-size:18px; color:#2b3440; }}
 .bar p {{ margin:2px 0 0; font-size:12px; color:#7f8c9b; }}
 .card {{ margin:18px; background:#fff; border-radius:12px; padding:8px;
         box-shadow:0 2px 14px #0002; }}
 svg {{ width:min(1500px,96vw); height:auto; display:block; }}
 @media print {{ body {{ background:#fff; }} .bar {{ display:none; }} .card {{ box-shadow:none; margin:0; }} }}
</style></head><body>
<div class="bar"><h1>花房 Final Project · 系统等轴测概念图</h1>
<p>与 3D 概念模型同源布局（两两相交审计通过）· Ctrl+P 可直接打印/导出 PDF</p></div>
<div class="card">{doc}</div>
</body></html>"""
with open("花房系统等轴测图.html", "w", encoding="utf-8") as f:
    f.write(html)
print("OK -> 花房系统等轴测图.svg / .html")
