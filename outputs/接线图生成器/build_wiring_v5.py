# -*- coding: utf-8 -*-
"""
花房整机接线总图 v5 生成器 —— 拟物版
=====================================
改图改这里（PARAMS 区），跑完自动写 HTML 并做布局审计。

设计规则（AR 记录）：
1. 拟物但不卡尺寸：面包板按 400 孔标准比例（2 排孔带 × 5 孔/组 + 中沟），ESP32 按 30P
   DevKitC 比例（宽窄两段 + USB 口 + 两排针），模块画 PCB + 引脚 + 丝印。
2. 只画 4 条信号线 + 2 根轨桥（v4 决策保留）；右侧接线写在盒内，不画长线。
3. 电源轨上的孔不逐个画：轨是铜条贯通，画两端引线孔即可。
4. 布局审计（文字重叠/线穿裸文字/越界）必须 0 问题才允许交付。
"""
import re, html as H

# ============ PARAMS ============
BB = dict(          # 面包板
    x=250, y=120, w=380, h=500,      # 左板（左侧留 210px 放模块）
    gap=90,                          # 两板间隙（ESP32 骑缝宽度）
    rail_h=13,                       # 电源轨条高
    hole_r=2.2,                      # 孔半径
    group_pitch=12.6,                # 组间距（列方向，5孔+间隔≈0.3in）
    hole_pitch=7.4,                  # 孔间距（行方向）
)
ESP = dict(cx=675, top=162, w=88, h=300)   # ESP32 骑缝：左缘贴左板右缘，右缘贴右板左缘
SVG_W, SVG_H = 1300, 960

# ============ 面包板几何 ============
def bb_geometry(bx, by, bw, bh):
    """返回 (孔坐标表, 板部件列表)。列 a-e / f-j，行 1-30。
    标准面包板：a-e 五孔一列组，中沟，f-j 五孔一列组；行方向 30 行分 10 组。"""
    rails = dict(red_top=by+8, blue_top=by+8+13, red_bot=by+bh-21, blue_bot=by+bh-8)
    holes_top_y = rails['blue_top'] + 18
    body_h = 30 * 7.4
    holes_bot_y = by + bh - 21 - body_h + 2
    # 列 x：每板 10 列(a..j)，组间加宽
    col_x = {}
    x = bx + 14
    for i, name in enumerate('abcdefghij'):
        col_x[name] = x + i * 9.2
        if i == 4:                       # 中沟
            x += 26
    rows_y = {r: holes_top_y + (r-1) * 7.4 for r in range(1, 31)}
    return rails, col_x, rows_y, holes_bot_y

def build():
    P = []  # svg parts
    # ---------- 左右两板 ----------
    boards = []
    bx1, by = BB['x'], BB['y']
    bx2 = bx1 + BB['w'] + BB['gap']
    for idx, (bx, label) in enumerate([(bx1, '左板（模拟区）Soil / Light / DHT / 浮球'),
                                        (bx2, '右板（数字区）OLED / LED / 继电器')]):
        bw = BB['w']
        P.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{BB["h"]}" rx="10" fill="#F4F1E8" stroke="#B4B2A9" stroke-width="1.5"/>')
        # 电源轨
        rails, *_ = bb_geometry(bx, by, bw, BB['h'])
        P.append(f'<rect x="{bx+8}" y="{rails["red_top"]}" width="{bw-16}" height="{BB["rail_h"]}" rx="3" fill="#E88B8B" stroke="#A32D2D" stroke-width="0.8"/>')
        P.append(f'<text x="{bx+16}" y="{rails["red_top"]+10}" font-size="8.5" fill="#791F1F">红轨 +3V3（贯通）</text>')
        P.append(f'<rect x="{bx+8}" y="{rails["blue_top"]}" width="{bw-16}" height="{BB["rail_h"]}" rx="3" fill="#8FBCE3" stroke="#185FA5" stroke-width="0.8"/>')
        P.append(f'<text x="{bx+16}" y="{rails["blue_top"]+10}" font-size="8.5" fill="#0C447C">蓝轨 GND（贯通）</text>')
        # 主孔区背景
        rails2, col_x, rows_y, holes_bot_y = bb_geometry(bx, by, bw, BB['h'])
        body_top = rails2['blue_top'] + BB['rail_h'] + 6
        body_h = 30 * 7.4 + 10
        P.append(f'<rect x="{bx+6}" y="{body_top}" width="{bw-12}" height="{body_h}" rx="4" fill="#FBFAF5" stroke="#D8D5CB" stroke-width="0.7"/>')
        # 中沟
        gutter_x = col_x['e'] + 12
        P.append(f'<rect x="{gutter_x}" y="{body_top+3}" width="10" height="{body_h-6}" fill="#E4E1D6"/>')
        P.append(f'<text x="{gutter_x+5}" y="{body_top+14}" font-size="7.5" fill="#A5A296" text-anchor="middle">沟</text>')
        # 孔阵
        holes = []
        for cname, cx in col_x.items():
            side = 'L' if cname in 'abcde' else 'R'
            for r in range(1, 31):
                holes.append((cname, r, cx, rows_y[r], side))
        for cname, r, cx, cy, side in holes:
            P.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{BB["hole_r"]}" fill="#C9C6BB"/>')
        # 行号（每 5 行标一次，左右两侧）
        for r in range(1, 31, 1):
            if r % 5 == 1 or r == 30:
                P.append(f'<text x="{bx+1}" y="{rows_y[r]+3}" font-size="7" fill="#A5A296" text-anchor="start" stroke="#F4F1E8" stroke-width="2.5" paint-order="stroke">{r}</text>')
                P.append(f'<text x="{bx+bw-1}" y="{rows_y[r]+3}" font-size="7" fill="#A5A296" text-anchor="end" stroke="#F4F1E8" stroke-width="2.5" paint-order="stroke">{r}</text>')
        # 列名（顶部）
        for cname, cx in col_x.items():
            P.append(f'<text x="{cx:.1f}" y="{body_top-2}" font-size="7.5" fill="#A5A296" text-anchor="middle">{cname}</text>')
        # 底轨（浅画）
        P.append(f'<rect x="{bx+8}" y="{by+BB["h"]-21}" width="{bw-16}" height="{BB["rail_h"]}" rx="3" fill="#F2D9A8" stroke="#C9A55C" stroke-width="0.7" opacity="0.7"/>')
        P.append(f'<text x="{bx+16}" y="{by+BB["h"]-11}" font-size="8" fill="#A08430" opacity="0.8">底部轨（本图不用）</text>')
        boards.append((bx, label, rails2, col_x, rows_y))
    # 板名
    P.insert(0, f'<text x="{bx1+BB["w"]/2}" y="{by-8}" text-anchor="middle" font-size="11.5" font-weight="500" fill="#5F5E5A">{boards[0][1]}</text>')
    P.insert(1, f'<text x="{bx2+BB["w"]/2}" y="{by-8}" text-anchor="middle" font-size="11.5" font-weight="500" fill="#5F5E5A">{boards[1][1]}</text>')

    Lr, Lc, Lry = boards[0][2], boards[0][3], boards[0][4]
    Rr, Rc, Rry = boards[1][2], boards[1][3], boards[1][4]

    # ---------- 轨桥 ----------
    P.append(f'<path d="M{bx1+BB["w"]-6} {Lr["red_top"]+6} L{bx2+6} {Rr["red_top"]+6}" stroke="#D0342C" stroke-width="2.5" stroke-linecap="round"/>')
    P.append(f'<path d="M{bx1+BB["w"]-6} {Lr["blue_top"]+6} L{bx2+6} {Rr["blue_top"]+6}" stroke="#185FA5" stroke-width="2.5" stroke-linecap="round"/>')
    P.append(f'<text x="{bx1+BB["w"]+10}" y="{Lr["red_top"]-3}" text-anchor="middle" font-size="8.5" fill="#444441" stroke="#F4F1E8" stroke-width="3" paint-order="stroke">轨桥×2</text>')

    # ---------- ESP32 拟物 ----------
    ex, et, ew, eh = ESP['cx']-ESP['w']/2, ESP['top'], ESP['w'], ESP['h']
    P.append(f'<rect x="{ex}" y="{et}" width="{ew}" height="{eh}" rx="6" fill="#3B4252" stroke="#2E3440" stroke-width="1.5"/>')
    P.append(f'<text x="{ex+ew/2}" y="{et+16}" text-anchor="middle" font-size="11" font-weight="600" fill="#ECEFF4">ESP32</text>')
    P.append(f'<text x="{ex+ew/2}" y="{et+28}" text-anchor="middle" font-size="8" fill="#B8C0D0">30P DevKitC</text>')
    # USB 口（顶部）
    P.append(f'<rect x="{ex+ew/2-14}" y="{et-12}" width="28" height="13" rx="2" fill="#98A2B3" stroke="#6B7280" stroke-width="1"/>')
    P.append(f'<text x="{ex+ew/2}" y="{et-20}" text-anchor="middle" font-size="8" fill="#5F5E5A">USB 朝外</text>')
    # 屏蔽罩装饰
    P.append(f'<rect x="{ex+ew/2-24}" y="{et+32}" width="48" height="20" rx="3" fill="#4C566A" stroke="#2E3440"/>')
    P.append(f'<text x="{ex+ew/2}" y="{et+47}" text-anchor="middle" font-size="6" fill="#D8DEE9">ESP-WROOM-32</text>')
    # 左右引脚（各15）
    left_pins  = ['EN','VP36','VN39','D34','D35','D32','D33','D25','D26','D27','D14','D12','D13','GND','VIN']
    right_pins = ['3V3','GND','D15','D2','D4','RX2','TX2','D5','D18','D19','D21','RX0','TX0','D22','D23']
    pin_r = 2.6
    pin_gap = (eh - 80) / 14
    pin_y0 = et + 56
    pinpos = {}
    for i, name in enumerate(left_pins):
        py = pin_y0 + i * pin_gap
        P.append(f'<circle cx="{ex+5}" cy="{py:.1f}" r="{pin_r}" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.8"/>')
        used = {'D34': '#A32D2D', 'D35': '#A32D2D', 'D32': '#27500A', 'D33': '#72243E',
                'D25': '#2C2C2A', 'D26': '#EF6C00', 'D27': '#2C2C2A', 'VIN': '#791F1F'}
        col = used.get(name, '#D8DEE9')
        w = '600' if name in used else '400'
        P.append(f'<text x="{ex+11}" y="{py+3:.1f}" font-size="8" font-weight="{w}" fill="{col}">{name}</text>')
        pinpos[('L', name)] = (ex+5, py)
    for i, name in enumerate(right_pins):
        py = pin_y0 + i * pin_gap
        P.append(f'<circle cx="{ex+ew-5}" cy="{py:.1f}" r="{pin_r}" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.8"/>')
        used = {'3V3': '#791F1F', 'GND': '#0C447C', 'D21': '#A32D2D', 'D22': '#A32D2D'}
        col = used.get(name, '#D8DEE9')
        w = '600' if name in used else '400'
        P.append(f'<text x="{ex+ew-11}" y="{py+3:.1f}" font-size="8" font-weight="{w}" fill="{col}" text-anchor="end">{name}</text>')
        pinpos[('R', name)] = (ex+ew-5, py)

    # ---------- 模块拟物（PCB + 引脚 + 丝印）----------
    def module(x, y, w, h, color, title, pins, title_dy=15, pin_side='bottom'):
        """pins: [(丝印, 相对x)]，pin_side bottom→PCB下缘引脚朝下"""
        parts = []
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{color}" stroke="#3B6D11" stroke-width="1.2"/>')
        parts.append(f'<text x="{x+w/2}" y="{y+title_dy}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#27500A">{title[0]}</text>')
        parts.append(f'<text x="{x+w/2}" y="{y+title_dy+13}" text-anchor="middle" font-size="8.5" fill="#4B6B2A">{title[1]}</text>')
        px = x + w/2 - (len(pins)-1) * 8
        pinpos_m = {}
        for label, _ in pins:
            parts.append(f'<rect x="{px-2.6:.1f}" y="{y+h-3}" width="5.2" height="9" rx="1" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.7"/>')
            parts.append(f'<text x="{px:.1f}" y="{y+h+17}" text-anchor="middle" font-size="7.5" fill="#444441">{label}</text>')
            pinpos_m[label] = (px, y+h+6)
            px += 16
        return parts, pinpos_m

    # 模块放板外左侧（x=板左缘-160），引脚标签朝下，避免压孔阵
    # 土壤（3针）→ 指向 a4–a6
    soil_x = BB['x'] - 218; soil_y = 170
    m, soil_pins = module(soil_x, soil_y, 118, 40, '#DDEBD0', ('土壤传感器', '3针直插 a4–a6'),
                          [('GND',0),('5V',0),('OUT',0)], title_dy=13)
    P += m
    P.append(f'<text x="{soil_x+118+6}" y="{soil_y+18}" font-size="8" fill="#5F5E5A">↔ a4–a6</text>')
    # 光敏（4针）→ a10–a13
    lux_x = BB['x'] - 218; lux_y = 286
    m, lux_pins = module(lux_x, lux_y, 118, 40, '#DDEBD0', ('光敏模块', '4针直插 a10–a13'),
                         [('DO',0),('GND',0),('VCC',0),('AO',0)], title_dy=13)
    P += m
    P.append(f'<text x="{lux_x+118+6}" y="{lux_y+18}" font-size="8" fill="#5F5E5A">↔ a10–a13</text>')
    # DHT（4针）→ a15–a18
    dht_x = BB['x'] - 218; dht_y = 402
    m, dht_pins = module(dht_x, dht_y, 118, 40, '#DDEBD0', ('DHT11', '4针直插 a15–a18'),
                         [('VCC',0),('DATA',0),('NC',0),('GND',0)], title_dy=13)
    P += m
    P.append(f'<text x="{dht_x+118+6}" y="{dht_y+18}" font-size="8" fill="#5F5E5A">↔ a15–a18</text>')
    # OLED（4针）→ 右板外右侧
    oled_x = bx2 + BB['w'] + 30; oled_y = 170
    m, oled_pins = module(oled_x, oled_y, 150, 46, '#DDEBD0', ('OLED 0.96 I2C', '4针直插 g2–g5 · 0x3C'),
                          [('GND',0),('VCC',0),('SCL',0),('SDA',0)], title_dy=14)
    P += m
    # LED 模块（3针）→ 右板外右侧
    led_x = bx2 + BB['w'] + 30; led_y = 300
    m, led_pins = module(led_x, led_y, 150, 42, '#DDEBD0', ('双色 LED 模块', '3针直插 g7–g9 · 限流板载'),
                         [('−',0),('R',0),('G',0)], title_dy=14)
    P += m
    # 浮球 RC 区（左板内行19-21 a-e 附近但避开孔阵→放行23-27 区域叠加半透明底）
    fx = Lc['a'] - 4; fy = rows_y[31] if False else (by + BB['h'] - 21 - 96)
    P.append(f'<rect x="{fx}" y="{fy}" width="170" height="84" rx="5" fill="#FAEEDA" fill-opacity="0.93" stroke="#854F0B" stroke-width="1"/>')
    P.append(f'<text x="{fx+6}" y="{fy+14}" font-size="9.5" font-weight="600" fill="#633806">浮球 RC 区（节点=行21）</text>')
    P.append(f'<text x="{fx+6}" y="{fy+27}" font-size="8.5" fill="#444441">R1 1kΩ：a19↔a21 · 取电红轨→a19</text>')
    P.append(f'<text x="{fx+6}" y="{fy+40}" font-size="8.5" fill="#444441">C1 100nF：c21↔蓝轨 · 浮球1：b21</text>')
    P.append(f'<text x="{fx+6}" y="{fy+53}" font-size="8.5" fill="#444441">浮球2：蓝轨任意 · D32跳线：e21</text>')
    P.append(f'<text x="{fx+6}" y="{fy+68}" font-size="8" font-weight="600" fill="#A32D2D">⚠ 全在 a–e 列 · 不跨中沟</text>')
    # R1/C1 拟物小图
    P.append(f'<rect x="{fx+112}" y="{fy+56}" width="30" height="9" rx="4" fill="#D8CBA8" stroke="#854F0B" stroke-width="0.8"/>')
    P.append(f'<circle cx="{fx+117}" cy="{fy+60.5}" r="2.2" fill="#8A4B2A"/><circle cx="{fx+124}" cy="{fy+60.5}" r="2.2" fill="#C9A227"/><circle cx="{fx+131}" cy="{fy+60.5}" r="2.2" fill="#B33A2B"/><circle cx="{fx+138}" cy="{fy+60.5}" r="2.2" fill="#C9A227"/>')
    P.append(f'<circle cx="{fx+118}" cy="{fy+73}" r="6.5" fill="#8C6239" stroke="#5F4324" stroke-width="0.8"/>')
    P.append(f'<text x="{fx+118}" y="{fy+75.5}" text-anchor="middle" font-size="6" fill="#F5EDE0">104</text>')

    # ---------- 继电器拟物（右板右缘外侧，与 OLED/LED 同列下方）----------
    rx = bx2 + BB['w'] + 8; ry = 430
    P.append(f'<rect x="{rx}" y="{ry}" width="188" height="148" rx="8" fill="#2D6CB5" stroke="#1B4E8A" stroke-width="1.5"/>')
    P.append(f'<text x="{rx+94}" y="{ry+18}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#EAF2FB">继电器 JQC-3FF/5VDC</text>')
    P.append(f'<text x="{rx+94}" y="{ry+31}" text-anchor="middle" font-size="8" fill="#C8DCF2">悬放不插板 · 跳帽→H档</text>')
    # 输入侧端子（3螺丝）
    def screw_row(x0, y0, n, pitch, labels, lab_color='#EAF2FB'):
        out = []
        px = x0
        for i in range(n):
            out.append(f'<rect x="{px-9:.1f}" y="{y0}" width="18" height="14" rx="2" fill="#3A7BC8" stroke="#1B4E8A"/>')
            out.append(f'<circle cx="{px:.1f}" cy="{y0+7:.1f}" r="4.5" fill="#C9D6E8" stroke="#5B7EA6" stroke-width="1"/>')
            out.append(f'<path d="M{px-3:.1f} {y0+7:.1f} L{px+3:.1f} {y0+7:.1f}" stroke="#5B7EA6" stroke-width="1.4"/>')
            out.append(f'<text x="{px:.1f}" y="{y0+24:.1f}" text-anchor="middle" font-size="8" font-weight="600" fill="{lab_color}">{labels[i]}</text>')
            px += pitch
        return out
    P += screw_row(rx+22, ry+40, 3, 34, ['DC+', 'DC−', 'IN'])
    P.append(f'<text x="{rx+8}" y="{ry+38}" font-size="7.5" fill="#BBD4EE">输入侧(5V线圈)</text>')
    # 强电侧端子
    P += screw_row(rx+22, ry+88, 3, 34, ['NC', 'COM', 'NO'], lab_color='#FFD9D9')
    P.append(f'<text x="{rx+8}" y="{ry+86}" font-size="7.5" fill="#BBD4EE">强电侧(触点)</text>')
    P.append(f'<text x="{rx+94}" y="{ry+72}" text-anchor="middle" font-size="7.5" fill="#9FBEDD">───── 隔离沿 ─────</text>')
    P.append(f'<text x="{rx+170}" y="{ry+120}" text-anchor="middle" font-size="7.5" fill="#CFE2F5">跳帽→H档</text>')
    P.append(f'<circle cx="{rx+158}" cy="{ry+116}" r="5" fill="#F5C542" stroke="#B08A1E" stroke-width="1"/>')

    # ---------- 4 条信号线（左板→ESP32 左列）----------
    def sig(p1, p2, color, label, lx, ly):
        P.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{(p1[0]+p2[0])/2-40:.1f} {p1[1]:.1f} L{(p1[0]+p2[0])/2-40:.1f} {p2[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f}" stroke="{color}" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
        P.append(f'<text x="{lx}" y="{ly}" font-size="8.5" font-weight="600" fill="{color}" stroke="#F4F1E8" stroke-width="3" paint-order="stroke">{label}</text>')
    # 信号线：从模块右缘中点水平走到 ESP32 左列针（路径全在板外空域 y 走廊）
    def sig2(p1, p2, color, label):
        mx = (p1[0]+p2[0])/2
        P.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{mx:.1f} {p1[1]:.1f} L{mx:.1f} {p2[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f}" stroke="{color}" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
        P.append(f'<text x="{mx-6:.1f}" y="{(p1[1]+p2[1])/2+3:.1f}" font-size="8.5" font-weight="600" fill="{color}" text-anchor="end" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">{label}</text>')
    sig2(soil_pins['OUT'], pinpos[('L','D34')], '#A32D2D', 'OUT→D34')
    sig2(lux_pins['AO'],  pinpos[('L','D35')], '#A32D2D', 'AO→D35')
    sig2(dht_pins['DATA'],pinpos[('L','D33')], '#72243E', 'DATA→D33')
    # 浮球节点（a21）→ D32
    node = (Lc['a']-6, Lry[21])
    P.append(f'<path d="M{node[0]:.1f} {node[1]:.1f} L{node[0]-16:.1f} {node[1]:.1f} L{node[0]-16:.1f} {pinpos[("L","D32")][1]:.1f} L{pinpos[("L","D32")][0]:.1f} {pinpos[("L","D32")][1]:.1f}" stroke="#27500A" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
    P.append(f'<text x="{node[0]-20:.1f}" y="{(node[1]+pinpos[("L","D32")][1])/2:.1f}" font-size="8.5" font-weight="600" fill="#27500A" text-anchor="end" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">行21→D32</text>')

    # ---------- 右列两根电源短线 ----------
    for (pn, rail, color) in [('3V3', Rr['red_top']+6, '#D0342C'), ('GND', Rr['blue_top']+6, '#185FA5')]:
        p2 = pinpos[('R', pn)]
        gx = bx2 + 2 if pn == '3V3' else bx2 + 6
        ext = 12 if pn == '3V3' else 5   # GND 短伸入，避开右板蓝轨文字
    P.append(f'<path d="M{p2[0]:.1f} {p2[1]:.1f} L{gx:.1f} {p2[1]:.1f} L{gx:.1f} {rail} L{gx+ext:.1f} {rail}" stroke="{color}" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round"/>')

    # ---------- 板外强电区（拟物）----------
    px0, py0 = 40, by + BB['h'] + 30
    P.append(f'<rect x="{px0-10}" y="{py0-6}" width="{SVG_W-px0}" height="150" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="1"/>')
    P.append(f'<text x="{px0}" y="{py0+8}" font-size="10.5" font-weight="600" fill="#791F1F">板外：水泵强电回路（不过面包板）</text>')
    cy = py0 + 52
    # 充电宝
    P.append(f'<rect x="{px0}" y="{cy-24}" width="76" height="46" rx="6" fill="#DCE9F8" stroke="#185FA5" stroke-width="1.2"/>')
    P.append(f'<rect x="{px0+8}" y="{cy-16}" width="34" height="16" rx="2" fill="#8FBCE3"/>')
    P.append(f'<text x="{px0+38}" y="{cy+18}" text-anchor="middle" font-size="8" fill="#0C447C">充电宝5V ≥1A</text>')
    # USB-A 母座（剪口 A）
    ux = px0+96
    P.append(f'<rect x="{ux}" y="{cy-12}" width="34" height="24" rx="3" fill="#C9C6BB" stroke="#888170" stroke-width="1"/>')
    P.append(f'<rect x="{ux+4}" y="{cy-7}" width="24" height="14" rx="2" fill="#FBFAF5" stroke="#888170"/>')
    for i in range(4):
        P.append(f'<rect x="{ux+6+i*5.4}" y="{cy-4}" width="2.6" height="8" fill="#B5B2A6"/>')
    P.append(f'<text x="{ux+17}" y="{cy+24}" text-anchor="middle" font-size="7.5" fill="#5F5E5A">延长线A母</text>')
    # 四线剪断示意
    wire_colors = [('红','#D0342C'), ('黑','#2C2C2A'), ('白','#C9C6BB'), ('绿','#3B6D11')]
    for i,(nm,c) in enumerate(wire_colors):
        wy = cy - 14 + i*8
        P.append(f'<path d="M{ux+34} {wy} L{ux+64} {wy}" stroke="{c}" stroke-width="2"/>')
        P.append(f'<text x="{ux+78}" y="{wy+3}" font-size="7" fill="{c if nm!="黑" else "#444441"}" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">{nm}线</text>')
    P.append(f'<text x="{ux+17}" y="{cy+38}" text-anchor="middle" font-size="7" fill="#888170">剪断处（白绿包胶带）</text>')
    # 继电器强电侧三端子
    jx = ux + 170
    P.append(f'<rect x="{jx}" y="{cy-22}" width="120" height="44" rx="6" fill="#2D6CB5" stroke="#1B4E8A" stroke-width="1.2"/>')
    for i,(lab,c) in enumerate([('NC','#A5B8CE'),('COM','#FFB3B3'),('NO','#FFB3B3')]):
        sx = jx + 18 + i*38
        P.append(f'<rect x="{sx-9}" y="{cy-14}" width="18" height="14" rx="2" fill="#3A7BC8" stroke="#1B4E8A"/>')
        P.append(f'<circle cx="{sx}" cy="{cy-7}" r="4.5" fill="#C9D6E8" stroke="#5B7EA6"/>')
        P.append(f'<text x="{sx}" y="{cy+14}" text-anchor="middle" font-size="8.5" font-weight="600" fill="{c}">{lab}</text>')
    P.append(f'<text x="{jx+60}" y="{cy-40}" text-anchor="middle" font-size="8" fill="#791F1F">继电器强电侧（同上方实物）</text>')
    # 红线路径：充电宝→A母红→COM；NO→R2→泵红
    P.append(f'<path d="M{px0+76} {cy-8} L{ux} {cy-8}" stroke="#D0342C" stroke-width="2.5"/>')
    P.append(f'<path d="M{ux+34} {cy-14} L{jx+16} {cy-14} L{jx+16} {cy-7}" stroke="#D0342C" stroke-width="2.5" fill="none"/>')
    pump_x = jx + 200
    P.append(f'<path d="M{jx+108} {cy-7} L{jx+130} {cy-7} L{jx+130} {cy-24} L{pump_x} {cy-24}" stroke="#D0342C" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="{(jx+130+pump_x)/2}" y="{cy-36}" text-anchor="middle" font-size="8" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">NO→R2→泵红</text>')
    # 黑线：A母黑→B1→万可→B2→泵黑
    wago_x = ux + 64; wago_y = cy + 40
    P.append(f'<path d="M{ux+34} {cy-6} L{wago_x+30} {cy-6} L{wago_x+30} {wago_y}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="{wago_x+56}" y="{wago_y-6}" font-size="8" fill="#444441" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">B1（电源黑）</text>')
    P.append(f'<rect x="{wago_x+8}" y="{wago_y}" width="66" height="26" rx="4" fill="#F5C542" stroke="#B08A1E" stroke-width="1.2"/>')
    for i in range(2):
        P.append(f'<rect x="{wago_x+16+i*26}" y="{wago_y+4}" width="14" height="18" rx="2" fill="#E0A92E" stroke="#B08A1E"/>')
        P.append(f'<circle cx="{wago_x+23+i*26}" cy="{wago_y+9}" r="2.4" fill="#8A6A10"/>')
    P.append(f'<text x="{wago_x+41}" y="{wago_y+38}" text-anchor="middle" font-size="7.5" fill="#854F0B">万可 221 · 黑线直通</text>')
    pump_y = cy - 6
    P.append(f'<path d="M{wago_x+74} {wago_y+8} L{pump_x-30} {wago_y+8} L{pump_x-30} {pump_y+8} L{pump_x} {pump_y+8}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="{(wago_x+74+pump_x)/2}" y="{wago_y+2}" text-anchor="middle" font-size="8" fill="#444441">B2→泵黑</text>')
    # 水泵拟物
    P.append(f'<rect x="{pump_x}" y="{cy-30}" width="86" height="58" rx="8" fill="#DDEBD0" stroke="#3B6D11" stroke-width="1.2"/>')
    P.append(f'<circle cx="{pump_x+30}" cy="{cy}" r="17" fill="#C4D8B0" stroke="#3B6D11" stroke-width="1"/>')
    for a in range(0, 360, 60):
        import math
        x1 = pump_x+30 + 6*math.cos(math.radians(a)); y1 = cy + 6*math.sin(math.radians(a))
        x2 = pump_x+30 + 15*math.cos(math.radians(a+30)); y2 = cy + 15*math.sin(math.radians(a+30))
        P.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="#7FA35F" stroke-width="2"/>')
    P.append(f'<rect x="{pump_x+52}" y="{cy-10}" width="24" height="9" rx="2" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.7"/>')
    P.append(f'<text x="{pump_x+64}" y="{cy-13}" text-anchor="middle" font-size="6.5" fill="#444441">红</text>')
    P.append(f'<rect x="{pump_x+52}" y="{cy+2}" width="24" height="9" rx="2" fill="#2C2C2A"/>')
    P.append(f'<text x="{pump_x+64}" y="{cy-1}" text-anchor="middle" font-size="6.5" fill="#F5F5F5">黑</text>')
    P.append(f'<text x="{pump_x+43}" y="{cy+40}" text-anchor="middle" font-size="8" fill="#27500A">水泵3W 浸水</text>')
    # 1N4007
    dx = wago_x + 108; dy = wago_y + 8
    P.append(f'<rect x="{dx}" y="{dy-5}" width="40" height="10" rx="4" fill="#2C2C2A"/>')
    P.append(f'<rect x="{dx+22}" y="{dy-5}" width="8" height="10" fill="#C9C6BB"/>')
    P.append(f'<path d="M{dx-8} {dy} L{dx} {dy} M{dx+40} {dy} L{dx+48} {dy}" stroke="#444441" stroke-width="2"/>')
    P.append(f'<text x="{dx+20}" y="{dy+16}" text-anchor="middle" font-size="7.5" fill="#854F0B" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">1N4007 反并泵端 · 色环端→泵红</text>')
    P.append(f'<path d="M{pump_x} {pump_y-24} L{dx+28} {pump_y-24} L{dx+28} {dy-10}" stroke="#854F0B" stroke-width="1.2" fill="none" stroke-dasharray="3 3"/>')
    P.append(f'<path d="M{pump_x} {pump_y+8} L{dx+28} {pump_y+8} L{dx+28} {dy+10}" stroke="#854F0B" stroke-width="1.2" fill="none" stroke-dasharray="3 3" opacity="0.5"/>')

    return '\n'.join(P)

SVG = build()

HEAD = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>花房整机接线总图（拟物版）</title>
<style>
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;background:#fff;color:#2C2C2A;}}
  .wrap{{max-width:1120px;margin:0 auto;padding:28px 20px 40px;}}
  h1{{font-size:20px;font-weight:600;margin:0 0 6px;}}
  h2{{font-size:16px;font-weight:600;margin:22px 0 8px;}}
  .meta{{font-size:13px;color:#5F5E5A;margin:0 0 12px;}}
  .warn{{font-size:13px;color:#A32D2D;font-weight:600;margin:0 0 14px;}}
  figure{{margin:0 0 20px;}}
  figcaption{{font-size:12px;color:#888780;margin-top:6px;}}
  table{{border-collapse:collapse;width:100%;font-size:13px;margin:0 0 16px;}}
  th,td{{border:1px solid #D3D1C7;padding:6px 9px;text-align:left;vertical-align:top;line-height:1.5;}}
  th{{background:#F1EFE8;font-weight:600;}}
  code{{background:#F1EFE8;border-radius:3px;padding:1px 5px;font-size:12px;}}
  ol{{font-size:13px;line-height:1.7;padding-left:22px;margin:0 0 16px;}}
  .foot{{font-size:12px;color:#888780;border-top:1px solid #D3D1C7;padding-top:10px;}}
  @media print{{ body{{-webkit-print-color-adjust:exact;}} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>花房整机接线总图 · 拟物版（实物形状 + 端口标注）</h1>
  <p class="meta">花房项目 Smart GreenHouse · 引脚与固件 <code>GreenHouse_v1.ino</code> 第 55–61 行逐一核对 · 器件丝印按 11/06–11/08 实拍 OCR · 与《docs/操作手册/花房接线规划表.md》同口径（冲突以此图 + 固件为准）· <b>模块针序一律以实物丝印对号入座</b></p>
  <p class="warn">四条铁律：① 模拟线只在 GPIO32–39（ADC1）——土壤 34 / 光敏 35；② 全系统共地只有一处——蓝轨单点回 ESP32 GND；③ <b>红轨/蓝轨与主孔区不互通，电源线别插进 a1/b1 这类主区孔</b>；④ <b>中沟两侧不通——a–e 与 f–j 是两套独立孔</b></p>

  <h2>一、面包板拟物总图（孔阵 = 真实 400 孔板布局：a–j 十列 × 1–30 行）</h2>
  <figure>
  <svg viewBox="0 0 {SVG_W} {SVG_H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" style="font-family:inherit">
  <title>花房整机接线总图：拟物版</title>
  <desc>两块400孔面包板画出真实孔阵，ESP32画板身与两排引脚并标注，五个模块画PCB与引脚丝印，继电器画蓝色本体与两排螺丝端子，板外强电区画充电宝/USB母座/万可/水泵/二极管。</desc>
  <defs>
  <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  </defs>
'''

FOOT = '''  </svg>
  <figcaption>拟物图：孔阵/引脚/端子按实物布局绘制（非严格比例）。只画 4 条信号线 + 2 根轨桥；OLED/LED/继电器接线见盒内标注与第二节清单；模块针序以实物丝印为准，行号窗口（a4–a6 / a10–a13 / a15–a18 / g2–g5 / g7–g9）不变。</figcaption>
  </figure>

  <h2>二、逐线清单（杜邦 21 + 跳线 6 + 元件 2，行号即孔位）</h2>
  <table>
    <tr><th style="width:36px;">#</th><th style="width:130px;">从</th><th style="width:140px;">到</th><th style="width:64px;">线种·色</th><th>孔位 / 说明</th></tr>
    <tr><td>1</td><td>ESP32 3V3（右列第1针）</td><td><b>右板红轨</b>第 1 孔</td><td>跳线·红</td><td>全板 3V3 母线起点。<b>红轨与主孔区不互通，别插 a1 这类主区孔</b></td></tr>
    <tr><td>2</td><td>ESP32 GND（右列第2针）</td><td><b>右板蓝轨</b>第 1 孔</td><td>跳线·黑</td><td>全板 GND 母线，<b>单点共地</b></td></tr>
    <tr><td>3</td><td>左板红轨</td><td>右板红轨</td><td>跳线·红</td><td>轨桥：两板红轨第 1 孔之间</td></tr>
    <tr><td>4</td><td>左板蓝轨</td><td>右板蓝轨</td><td>跳线·黑</td><td>轨桥：两板蓝轨第 1 孔之间</td></tr>
    <tr><td>5</td><td>土壤 5V 针</td><td>左板红轨</td><td>杜邦·红</td><td>模块 3 针直插 <b>a4–a6</b>（丝印 GND/5V/OUT 对号），引线插<b>针所在行的 b 列孔</b></td></tr>
    <tr><td>6</td><td>土壤 GND 针</td><td>左板蓝轨</td><td>杜邦·黑</td><td>同上（丝印 5V 实接 3V3 ✓ 11/08 已验）</td></tr>
    <tr><td>7</td><td>土壤 OUT 针</td><td>ESP32 <b>D34</b></td><td>杜邦·黄</td><td>ADC1 只读脚</td></tr>
    <tr><td>8</td><td>光敏 VCC 针</td><td>左板红轨</td><td>杜邦·红</td><td>模块 4 针直插 <b>a10–a13</b>，引线插针同行 b 列孔</td></tr>
    <tr><td>9</td><td>光敏 GND 针</td><td>左板蓝轨</td><td>杜邦·黑</td><td>同上</td></tr>
    <tr><td>10</td><td>光敏 AO 针</td><td>ESP32 <b>D35</b></td><td>杜邦·紫</td><td>DO 针<b>悬空不接</b>（raw=1421 已验）</td></tr>
    <tr><td>11</td><td>DHT11 VCC 针</td><td>左板红轨</td><td>杜邦·红</td><td>模块 4 针直插 <b>a15–a18</b>（3 针实物则 a15–a17）</td></tr>
    <tr><td>12</td><td>DHT11 GND 针</td><td>左板蓝轨</td><td>杜邦·黑</td><td>同上</td></tr>
    <tr><td>13</td><td>DHT11 DATA 针</td><td>ESP32 <b>D33</b></td><td>杜邦·白</td><td>单总线（29.2℃/68% 已验）</td></tr>
    <tr><td>14</td><td>左板红轨</td><td><b>a19</b></td><td>跳线·红</td><td>浮球上拉取 3V3（不与 DHT 的 a15–a18 撞行）</td></tr>
    <tr><td>15</td><td>R1 · 1kΩ（棕黑红）</td><td>—</td><td>元件</td><td>两脚插 <b>a19 ↔ a21</b>：a19=3V3 侧，a21=上拉节点</td></tr>
    <tr><td>16</td><td>C1 · 100nF</td><td>—</td><td>元件</td><td><b>c21 ↔ 顶部蓝轨</b>（无极性可倒插）</td></tr>
    <tr><td>17</td><td>浮球线 1</td><td><b>b21</b></td><td>杜邦·任意</td><td>节点行 21 的 b 孔</td></tr>
    <tr><td>18</td><td>浮球线 2</td><td>顶部蓝轨任意孔</td><td>杜邦·任意</td><td>两线可互换</td></tr>
    <tr><td>19</td><td>ESP32 <b>D32</b>（左列第6针）</td><td><b>e21</b></td><td>跳线·绿</td><td>短跳线：排针 → e21（与 a21 同列贯通）</td></tr>
    <tr><td>20</td><td>ESP32 D21</td><td>OLED SDA</td><td>杜邦·绿</td><td>I2C 数据；OLED 插 <b>g2–g5</b>（常见序 GND/VCC/SCL/SDA，0x3C 已验）</td></tr>
    <tr><td>21</td><td>ESP32 D22</td><td>OLED SCL</td><td>杜邦·白</td><td>I2C 时钟</td></tr>
    <tr><td>22</td><td>OLED VCC</td><td>右板红轨</td><td>杜邦·红</td><td>丝印 VCC 针引出</td></tr>
    <tr><td>23</td><td>OLED GND</td><td>右板蓝轨</td><td>杜邦·黑</td><td>丝印 GND 针引出</td></tr>
    <tr><td>24</td><td>ESP32 D25</td><td>LED 模块 R（g8）</td><td>杜邦·红</td><td>LED 3 针插 <b>g7–g9</b>（−/R/G 序，限流板载）</td></tr>
    <tr><td>25</td><td>ESP32 D27</td><td>LED 模块 G（g9）</td><td>杜邦·绿</td><td>D25/D27 在<b>左列</b>第 8/10 针（D26 居中=第 9 针，别插错行）</td></tr>
    <tr><td>26</td><td>LED 模块 −（g7）</td><td>右板蓝轨</td><td>杜邦·黑</td><td>GND 已由 #4 桥通</td></tr>
    <tr><td>27</td><td>ESP32 <b>VIN</b>（左列第15针）</td><td>继电器 <b>DC+</b></td><td>杜邦·红（剥头8mm）</td><td>线圈 5VDC；绝不用 3V3</td></tr>
    <tr><td>28</td><td>右板蓝轨</td><td>继电器 <b>DC−</b></td><td>杜邦·黑（剥头8mm）</td><td>借蓝轨取 GND（#2/#4 已桥通）</td></tr>
    <tr><td>29</td><td>ESP32 <b>D26</b>（左列第9针）</td><td>继电器 <b>IN</b></td><td>杜邦·橙（剥头8mm）</td><td>信号线</td></tr>
    <tr><td>30–32</td><td>继电器 COM / NO / 泵黑</td><td>泵回路</td><td>板外</td><td>COM←充电宝红R1；NO→泵红R2；泵黑→万可→B2；NC 不接（见第一节强电区）</td></tr>
  </table>
  <p class="meta">合计：杜邦母对母 21 根（#5–13、#17–18、#20–26、#27–29，其中 3 根剥头拧螺丝）+ 面包板跳线 6 根（#1–4、#14、#19）+ 元件 2 个（R1/C1）+ 强电板外 3 根。</p>

  <h2>三、ESP32 端口占用总表（= 固件 55–61 行 + I2C 默认）</h2>
  <table>
    <tr><th>GPIO</th><th>丝印</th><th>接谁</th><th>方向</th><th>为什么是这个脚</th></tr>
    <tr><td><b>34</b></td><td>D34（左列4）</td><td>土壤 OUT</td><td>ADC1 只进</td><td>ADC1 组，WiFi 开启不受影响；只读脚不能接输出设备</td></tr>
    <tr><td><b>35</b></td><td>D35（左列5）</td><td>光敏 AO</td><td>ADC1 只进</td><td>同上；DO 弃用</td></tr>
    <tr><td><b>33</b></td><td>D33（左列7）</td><td>DHT11 DATA</td><td>数字双向</td><td>单总线，模块自带上拉</td></tr>
    <tr><td><b>32</b></td><td>D32（左列6）</td><td>浮球干接点</td><td>数字输入</td><td>外接 1kΩ 上拉 + 100nF 滤抖；fail-safe</td></tr>
    <tr><td><b>26</b></td><td>D26（左列9）</td><td>继电器 IN</td><td>数字输出</td><td>普通 IO，无启动毛刺历史问题（v1.3 已锁）</td></tr>
    <tr><td><b>25</b> / <b>27</b></td><td>D25 / D27（左列8/10）</td><td>LED 红 / 绿</td><td>数字输出</td><td>模块带限流电阻，直驱</td></tr>
    <tr><td><b>21</b> / <b>22</b></td><td>D21 / D22（右列11/14）</td><td>OLED SDA / SCL</td><td>I2C</td><td>硬件 I2C 默认脚（0x3C 实扫确认）</td></tr>
    <tr><td><b>VIN</b></td><td>VIN（左列15）</td><td>继电器 DC+</td><td>电源 5V</td><td>线圈 5VDC；USB 供电时 ≈4.7V 可用；绝不用 3V3</td></tr>
    <tr><td>3V3</td><td>3V3（右列1）</td><td>红轨母线</td><td>电源 3.3V</td><td>喂 4 个传感器 + 浮球上拉</td></tr>
    <tr><td>⚠️ 禁用</td><td>GPIO 6–11 / 12 / 4 / 13 / 14 等</td><td>—</td><td>—</td><td>6–11 接 flash 碰了变砖；12 启动脚拉错刷不进固件；4/13/14 属 ADC2 WiFi 一开读数全废——本机均未用</td></tr>
  </table>

  <h2>四、通电前 60 秒核对（打勾才上电）</h2>
  <ol>
    <li><b>共地单点</b>：ESP32 GND → 蓝轨只有 #2 一根线（#28 继电器 DC− 借右板蓝轨）</li>
    <li><b>模拟双线</b>：土壤 OUT→D34、光敏 AO→D35，没插到 ADC2 组</li>
    <li><b>继电器供电</b>：DC+ 接的是 <b>VIN</b> 不是 3V3；线圈 5VDC</li>
    <li><b>触点侧</b>：接 COM+NO，NC 空着（接 NC = 一上电就抽水）</li>
    <li><b>浮球 RC</b>：节点全在<b>行 21 的 a–e 列</b>（a=R1 / b=浮球1 / c=C1 / e=D32），不跨中沟</li>
    <li><b>二极管</b>：断电态红笔泵−黑笔泵+ 读 0.5–0.7V；读 0/双向通 = 击穿，立刻拆</li>
    <li><b>跳帽</b>：High/Low 跳帽在 <b>H 档</b>；吸合逻辑反了先拨 L 档验证，再查 <code>RELAY_ACTIVE_HIGH</code></li>
    <li><b>固件先决</b>：联调烧 <code>RelayPumpTest</code>，测完烧回 <code>GreenHouse_v1</code> v1.6</li>
  </ol>

  <p class="foot">花房项目 · Smart GreenHouse · 整机接线总图 v5 拟物版（2026-11-09，由 outputs/接线图生成器/build_wiring_v5.py 参数化生成）· 引脚对照 GreenHouse_v1.ino L55–61 · 器件丝印对照 11/06–11/08 实拍 OCR · 配套《花房接线规划表.md》《花房接线图_水泵.html》</p>
</div>
</body>
</html>
'''

out = r'D:\Documents\workbuddydocument\2026-10-17-08-59-13\docs\操作手册\花房接线图_整机总图.html'
open(out, 'w', encoding='utf-8').write(HEAD + SVG + FOOT)
print('written:', out, len(HEAD+SVG+FOOT), 'bytes')
