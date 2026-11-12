# -*- coding: utf-8 -*-
"""
花房整机接线总图 v5 生成器 —— 拟物版
=====================================
改图改这里（PARAMS 区），跑完自动写 HTML 并做布局审计。

设计规则（AR 记录）：
1. 拟物但不卡尺寸：面包板按 400 孔标准比例（2 排孔带 × 5 孔/组 + 中沟），ESP32 按 30P
   DevKitC 比例（宽窄两段 + USB 口 + 两排针），模块画 PCB + 引脚 + 丝印。
2. 画 4 条信号线 + 左板 6 根模块供电短线（b列→轨）+ 2 根电源短线 + 2 根轨桥（v5.3.4）；
   右侧模块接线写在盒内+清单，不画长线。
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
    """返回 (轨坐标表, 孔坐标表, 行号表, 孔区底 y)。列 a-e / f-j，行 1-30。
    v5.3：电源轨按实物移到板两侧竖排（每板中缝侧画红/蓝两条，各 25 孔分 5 群），
    孔阵整体右移给轨让位；行号窗口（a4–a6 等）引用不变。"""
    rail_x = dict(red=bx + bw - 28, blue=bx + bw - 44)   # 竖轨 x（蓝靠孔阵，红靠板缘）
    rail_y0, rail_y1 = by + 16, by + 16 + 209            # 25 孔×7.4 + 4 群间×6 = 209
    holes_top_y = by + 30
    body_h = 30 * 7.4
    holes_bot_y = holes_top_y + body_h
    # 列 x：每板 10 列(a..j)，组间加宽；起点右移 36px 给轨让位
    col_x = {}
    x = bx + 50
    for i, name in enumerate('abcdefghij'):
        col_x[name] = x + i * 9.2
        if i == 4:                       # 中沟
            x += 26
    rows_y = {r: holes_top_y + (r-1) * 7.4 for r in range(1, 31)}
    return rail_x, rail_y0, rail_y1, col_x, rows_y, holes_bot_y

def build():
    P = []  # svg parts
    # ---------- 左右两板 ----------
    boards = []
    bx1, by = BB['x'], BB['y']
    bx2 = bx1 + BB['w'] + BB['gap']
    for idx, (bx, label) in enumerate([(bx1, '左板 · 模拟区（Soil / Light / DHT / 浮球）'),
                                        (bx2, '右板 · 数字区（OLED / LED / 继电器）')]):
        bw = BB['w']
        P.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{BB["h"]}" rx="10" fill="#F4F1E8" stroke="#B4B2A9" stroke-width="1.5"/>')
        # 电源轨（v5.3：按实物移到板两长边竖排；每板只在靠图外侧那一条画轨+标注，靠中缝侧留白）
        rail_x, rail_y0, rail_y1, col_x, rows_y, holes_bot_y = bb_geometry(bx, by, bw, BB['h'])
        rail_side_left = (idx == 0)
        # 主孔区背景（v5.3b：先画背景再画轨——右板孔区原右缘 bx+bw-34 会把蓝轨 rx=bx+bw-41 整条盖掉）
        body_top = by + 22
        body_h = 30 * 7.4 + 10
        body_x = bx + 40 if rail_side_left else bx + 6
        body_w = (bw - 46) if rail_side_left else (bw - 55)   # 右板右缘收到蓝轨外侧(bx+bw-49)-2
        P.append(f'<rect x="{body_x}" y="{body_top}" width="{body_w}" height="{body_h}" rx="4" fill="#FBFAF5" stroke="#D8D5CB" stroke-width="0.7"/>')
        rx_red = bx + 16 if rail_side_left else bx + bw - 24
        rx_blue = rx_red + 17 if rail_side_left else rx_red - 17
        for (rx_col, fill, stroke, lab, tcol) in [
            (rx_red,  '#E88B8B', '#A32D2D', '+', '#791F1F'),
            (rx_blue, '#8FBCE3', '#185FA5', '−', '#0C447C'),
        ]:
            P.append(f'<rect x="{rx_col-6}" y="{rail_y0-8}" width="12" height="{rail_y1-rail_y0+16}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
            for g in range(5):  # 5 群 × 5 孔
                gy0 = rail_y0 + g * (5 * 7.4 + 6)
                for k in range(5):
                    P.append(f'<circle cx="{rx_col}" cy="{gy0 + k*7.4:.1f}" r="{BB["hole_r"]}" fill="#FBFAF5" stroke="{stroke}" stroke-width="0.6"/>')
            P.append(f'<text x="{rx_col}" y="{rail_y1+24}" text-anchor="middle" font-size="8.5" font-weight="600" fill="{tcol}">{lab}</text>')
        # 轨标注放轨底端下方（轨桥线走轨顶，标注在底部避开）；标注朝板外侧、镜像偏移防交叉语义
        side = 1 if rail_side_left else -1   # 左板红轨在最左→标注朝左外；右板红轨在最右→镜像朝右外
        P.append(f'<text x="{rx_red-10*side}" y="{rail_y1+40}" font-size="8" fill="#791F1F" text-anchor="middle">+3V3</text>')
        P.append(f'<text x="{rx_blue+12*side}" y="{rail_y1+52}" font-size="8" fill="#0C447C" text-anchor="middle">GND</text>')
        P.append(f'<text x="{(rx_red+rx_blue)/2}" y="{rail_y1+66}" font-size="7" fill="#888780" text-anchor="middle">贯通待实测</text>')
        # 主孔区背景已提前到轨之前绘制（v5.3b）
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
        # 行号（每 5 行标一次：左板标右缘、右板标左缘——靠中缝，轨侧不标）
        for r in range(1, 31, 1):
            if r % 5 == 1 or r == 30:
                num_x = bx + bw - 2 if rail_side_left else bx + 2
                anch2 = 'end' if rail_side_left else 'start'
                P.append(f'<text x="{num_x}" y="{rows_y[r]+3}" font-size="7" fill="#A5A296" text-anchor="{anch2}" stroke="#F4F1E8" stroke-width="2.5" paint-order="stroke">{r}</text>')
        # 列名（顶部）
        for cname, cx in col_x.items():
            P.append(f'<text x="{cx:.1f}" y="{body_top-4}" font-size="7.5" fill="#A5A296" text-anchor="middle">{cname}</text>')
        boards.append((bx, label, dict(red=rx_red, blue=rx_blue, y0=rail_y0, y1=rail_y1), col_x, rows_y))
    # 板名
    P.insert(0, f'<text x="{bx1+BB["w"]/2}" y="{by-8}" text-anchor="middle" font-size="11.5" font-weight="500" fill="#5F5E5A">{boards[0][1]}</text>')
    P.insert(1, f'<text x="{bx2+BB["w"]/2}" y="{by-8}" text-anchor="middle" font-size="11.5" font-weight="500" fill="#5F5E5A">{boards[1][1]}</text>')

    Lr, Lc, Lry = boards[0][2], boards[0][3], boards[0][4]
    Rr, Rc, Rry = boards[1][2], boards[1][3], boards[1][4]

    # ---------- 轨桥（v5.3：轨在板外侧竖排 → 桥走图顶部，红/蓝各一根，跨两板同色轨）----------
    bridge_y = by - 24
    lx_red = bx1 + 14          # 左板轨朝左外 → 左板红轨 x
    rx_red = bx2 + BB['w'] - 22  # 右板红轨 x
    lx_blue, rx_blue_ = lx_red + 16, rx_red - 16
    P.append(f'<path d="M{lx_red} {Lr["y0"]} V{bridge_y} H{rx_red} V{Rr["y0"]}" stroke="#D0342C" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    P.append(f'<path d="M{lx_blue} {Lr["y0"]+12} V{bridge_y-12} H{rx_blue_} V{Rr["y0"]+12}" stroke="#185FA5" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    P.append(f'<text x="{(lx_red+rx_red)/2}" y="{bridge_y-18}" text-anchor="middle" font-size="8.5" fill="#444441" stroke="#F4F1E8" stroke-width="3" paint-order="stroke">轨桥×2（红↔红 / 蓝↔蓝）</text>')

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
        # 面板 used 色 = 清单线色（深底用亮色变体，v5.3.5 修正：D25/D27 原近黑在深蓝板上不可见
        #   且与清单线色（红/绿）不符；D21/D22 暗红 vs 清单绿/白同理）
        used = {'D34': '#E8B54A', 'D35': '#B98EE8', 'D32': '#7CBF5E', 'D33': '#C9C6BB',
                'D25': '#F0766B', 'D26': '#F5A54B', 'D27': '#6FCF7C', 'VIN': '#F0766B'}
        col = used.get(name, '#D8DEE9')
        w = '600' if name in used else '400'
        P.append(f'<text x="{ex+11}" y="{py+3:.1f}" font-size="8" font-weight="{w}" fill="{col}">{name}</text>')
        pinpos[('L', name)] = (ex+5, py)
    for i, name in enumerate(right_pins):
        py = pin_y0 + i * pin_gap
        P.append(f'<circle cx="{ex+ew-5}" cy="{py:.1f}" r="{pin_r}" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.8"/>')
        # 右列 used 色 = 清单线色亮色变体（v5.3.5：D21=绿#20 D22=白 对齐清单）
        used = {'3V3': '#F0766B', 'GND': '#6FA8DC', 'D21': '#6FCF7C', 'D22': '#E8E6E0'}
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
    # OLED/LED 供电去向小标注（v5.3.5 补：清单#22/#23/#26 图上无对应视觉锚点的问题）
    # y=模块高+34：module() 的引脚丝印带在 y+h+17（7.5px 字），标注再往下挪避开
    P.append(f'<text x="{oled_x+75}" y="{oled_y+46+34}" text-anchor="middle" font-size="8" fill="#5F5E5A">VCC→红轨 / GND→蓝轨（#22/#23）</text>')
    # LED 模块（3针）→ 右板外右侧
    led_x = bx2 + BB['w'] + 30; led_y = 300
    m, led_pins = module(led_x, led_y, 150, 42, '#DDEBD0', ('双色 LED 模块', '3针直插 g7–g9 · 限流板载'),
                         [('−',0),('R',0),('G',0)], title_dy=14)
    P += m
    P.append(f'<text x="{led_x+75}" y="{led_y+42+34}" text-anchor="middle" font-size="8" fill="#5F5E5A">−→蓝轨（#26，GND 共轨）</text>')
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
    sig2(soil_pins['OUT'], pinpos[('L','D34')], '#B8860B', 'OUT→D34')   # 杜邦·黄（对齐清单 #7）
    sig2(lux_pins['AO'],  pinpos[('L','D35')], '#6A3D9A', 'AO→D35')     # 杜邦·紫（对齐清单 #10）
    sig2(dht_pins['DATA'],pinpos[('L','D33')], '#888780', 'DATA→D33')   # 杜邦·白（对齐清单 #13）
    # 浮球节点（a21）→ D32（v5.3.2：贴边走线避行号列——a列→板内顶走廊 y=126（板框120与列名字带131之间）→D32，
    # 全程不过行号数字带（行号 x∈[600,628] y∈[行±4]），不再穿轨/穿行号/穿板名）
    node = (Lc['a']-6, Lry[21])
    cor_x, cor_y = Lc['a'] - 6, 126            # 板内顶走廊
    P.append(f'<path d="M{node[0]:.1f} {node[1]:.1f} L{cor_x:.1f} {cor_y} L{pinpos[("L","D32")][0]-14:.1f} {cor_y} L{pinpos[("L","D32")][0]-14:.1f} {pinpos[("L","D32")][1]:.1f} L{pinpos[("L","D32")][0]:.1f} {pinpos[("L","D32")][1]:.1f}" stroke="#27500A" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
    P.append(f'<text x="{cor_x+8:.1f}" y="{cor_y-4}" font-size="8.5" font-weight="600" fill="#27500A" text-anchor="start" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">行21→D32</text>')

    # ---------- 模块供电短线 ×6（v5.3.4 补画：清单#5/#6/#8/#9/#11/#12，引线插针同行 b 列孔 → 左板红/蓝轨）----------
    # 土壤 直插a4–a6（丝印GND/5V/OUT）: 5V=b5→红轨, GND=b4→蓝轨
    # 光敏 直插a10–a13（丝印DO/GND/VCC/AO）: VCC=b12→红轨, GND=b11→蓝轨
    # DHT11 直插a15–a18（丝印VCC/DATA/NC/GND）: VCC=b15→红轨, GND=b18→蓝轨
    # （b列与针同组贯通=同节点；行y∈[172,276]与黄线走廊y≈216、绿线走廊y=126均不冲突）
    # v5.3.5：终点吸附最近轨孔心——孔阵行网格与轨孔网格不同步（轨孔 y=轨y0+k*7.4+群间隔），
    #   不吸附时线头落在轨条空白处（b4 尤其偏 6.6px 落群间隔带），拟物上=没插进孔
    def snap_rail_y(y, rail_y0):
        """吸附到最近轨孔中心：轨孔组 g∈[0,5)，每组 5 孔步进 7.4，组间隔 +6"""
        best, bd = None, 1e9
        for g in range(5):
            gy0 = rail_y0 + g * (5 * 7.4 + 6)
            for k in range(5):
                cy = gy0 + k * 7.4
                if abs(cy - y) < bd:
                    best, bd = cy, abs(cy - y)
        return best
    for (row, color, tx) in [(5, '#D0342C', Lr['red']), (12, '#D0342C', Lr['red']), (15, '#D0342C', Lr['red']),
                             (4, '#185FA5', Lr['blue']), (11, '#185FA5', Lr['blue']), (18, '#185FA5', Lr['blue'])]:
        y = Lry[row]
        ty = snap_rail_y(y, Lr['y0'] + 8)          # 轨孔中心 y（轨条 y0-8 顶 + 孔从 y0 起步）
        # 实线（供电=实体飞线，区别于虚线信号线）；红线要跨过蓝轨轨条（红轨在板最外侧），
        # 底色光晕表达"飞线跨越、不搭接蓝轨"
        if abs(tx - Lr['red']) < 1:
            P.append(f'<path d="M{Lc["b"]:.1f} {y:.1f} L{tx:.1f} {ty:.1f}" stroke="#F4F1E8" stroke-width="4.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        P.append(f'<path d="M{Lc["b"]:.1f} {y:.1f} L{tx:.1f} {y:.1f} L{tx:.1f} {ty:.1f}" stroke="{color}" stroke-width="2.0" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')

    # ---------- 右列两根电源短线（v5.3：3V3/GND → 右板侧边竖轨孔，v5.3.5 改实线+落第2/4孔）----------
    # 清单 #1/#2 原写"第1孔"，但 #3/#4 轨桥已占两板同色轨第1孔——一孔插不进两根线，
    # 图上精确落第2/4孔（红#2孔、蓝#4孔），清单文字同步改口径
    for (pn, rail_col, color, k_off) in [('3V3', Rr['red'], '#D0342C', 1), ('GND', Rr['blue'], '#185FA5', 3)]:
        p2 = pinpos[('R', pn)]
        ry_target = Rr['y0'] + 8 + k_off * 7.4      # 第 2/4 孔心（轨第1组首孔心=y0+8，步进7.4）
        P.append(f'<path d="M{p2[0]:.1f} {p2[1]:.1f} L{rail_col:.1f} {p2[1]:.1f} L{rail_col:.1f} {ry_target:.1f}" stroke="{color}" stroke-width="2.0" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')

    # ---------- 板外强电区（拟物，v5.2 pigtail 免剪方案）----------
    px0, py0 = 40, by + BB['h'] + 30
    P.append(f'<rect x="{px0-10}" y="{py0-6}" width="{SVG_W-px0}" height="196" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="1"/>')
    P.append(f'<text x="{px0}" y="{py0+8}" font-size="10.5" font-weight="600" fill="#791F1F" stroke="#FCEBEB" stroke-width="4" paint-order="stroke">板外：水泵强电回路（不过面包板）</text>')
    cy = py0 + 52
    # 充电宝（开小电流模式，防轻载自动断电）
    P.append(f'<rect x="{px0}" y="{cy-24}" width="76" height="46" rx="6" fill="#DCE9F8" stroke="#185FA5" stroke-width="1.2"/>')
    P.append(f'<rect x="{px0+8}" y="{cy-16}" width="34" height="16" rx="2" fill="#8FBCE3"/>')
    P.append(f'<text x="{px0+38}" y="{cy+16}" text-anchor="middle" font-size="8" fill="#0C447C" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">充电宝 5V ≥1A</text>')
    P.append(f'<text x="{px0+38}" y="{cy+34}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">⚠ 开小电流模式</text>')
    # 公头线（USB-A 公头插充电宝，尾部出红黑两线）· SKU1
    plugx = px0 + 96
    P.append(f'<rect x="{plugx}" y="{cy-12}" width="34" height="24" rx="2" fill="#B8BCC4" stroke="#6B7280" stroke-width="1"/>')
    P.append(f'<rect x="{plugx+6}" y="{cy-5}" width="22" height="10" rx="1" fill="#FBFAF5" stroke="#888170" stroke-width="0.7"/>')
    for i in range(4):
        P.append(f'<rect x="{plugx+8+i*4.6}" y="{cy-3}" width="2.4" height="6" fill="#C9A227"/>')
    P.append(f'<text x="{plugx+17}" y="{cy+30}" text-anchor="middle" font-size="7.5" font-weight="600" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头线 30cm</text>')
    P.append(f'<text x="{plugx+17}" y="{cy+44}" text-anchor="middle" font-size="7" fill="#888170" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">SKU1 插充电宝</text>')
    # 继电器强电侧端子（NC/COM/NO）
    jx = 300
    P.append(f'<text x="{jx+40}" y="{cy+34}" text-anchor="middle" font-size="7.5" fill="#791F1F" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">常开 · 断电自动停泵</text>')
    P.append(f'<rect x="{jx}" y="{cy-22}" width="120" height="44" rx="6" fill="#2D6CB5" stroke="#1B4E8A" stroke-width="1.2"/>')
    for i,(lab,c) in enumerate([('NC','#A5B8CE'),('COM','#FFB3B3'),('NO','#FFB3B3')]):
        sx = jx + 18 + i*38
        P.append(f'<rect x="{sx-9}" y="{cy-14}" width="18" height="14" rx="2" fill="#3A7BC8" stroke="#1B4E8A"/>')
        P.append(f'<circle cx="{sx}" cy="{cy-7}" r="4.5" fill="#C9D6E8" stroke="#5B7EA6"/>')
        P.append(f'<text x="{sx}" y="{cy+14}" text-anchor="middle" font-size="8.5" font-weight="600" fill="{c}">{lab}</text>')
    # 红1：公头线红 → COM
    P.append(f'<path d="M{plugx+34} {cy-8} L{jx+48} {cy-8}" stroke="#D0342C" stroke-width="2.5"/>')
    P.append(f'<text x="{(plugx+34+jx+48)/2}" y="{cy-16}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头红 → COM</text>')
    # 红2：NO → 母头线红（1N4007 色环端同孔并进）
    P.append(f'<path d="M{jx+103} {cy-8} L500 {cy-8}" stroke="#D0342C" stroke-width="2.5"/>')
    P.append(f'<text x="458" y="{cy-16}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">NO → 母头红</text>')
    # 母头线母座（USB-A 母口，泵公头插入）· SKU2
    P.append(f'<rect x="500" y="{cy-12}" width="34" height="24" rx="3" fill="#C9C6BB" stroke="#888170" stroke-width="1"/>')
    P.append(f'<rect x="504" y="{cy-7}" width="26" height="14" rx="2" fill="#FBFAF5" stroke="#888170" stroke-width="0.7"/>')
    for i in range(4):
        P.append(f'<rect x="{506+i*5.8}" y="{cy-4}" width="2.6" height="8" fill="#B5B2A6"/>')
    P.append(f'<text x="560" y="{cy+30}" text-anchor="middle" font-size="7.5" font-weight="600" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">母头线 30cm</text>')
    P.append(f'<text x="560" y="{cy+44}" text-anchor="middle" font-size="7" fill="#888170" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">SKU2 泵公头插入</text>')
    # 万可 221-413（三孔汇流：公头黑 / 二极管无环端 / 母头黑）
    wago_x, wago_y = 240, 792
    P.append(f'<rect x="{wago_x}" y="{wago_y}" width="106" height="28" rx="4" fill="#F5C542" stroke="#B08A1E" stroke-width="1.2"/>')
    for hx in (262, 293, 324):
        P.append(f'<rect x="{hx-8}" y="{wago_y+4}" width="16" height="9" rx="2" fill="#E0A92E" stroke="#B08A1E" stroke-width="0.7"/>')
        P.append(f'<circle cx="{hx}" cy="{wago_y+21}" r="4.2" fill="#8A6A10"/>')
    # 母头黑：母座下缘 → 万可孔3
    P.append(f'<path d="M508 {cy+12} L508 784 L324 784 L324 {wago_y+21}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="470" y="780" text-anchor="middle" font-size="8" font-weight="600" fill="#444441" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">母头黑</text>')
    # 黑线三路（互不交叉，线头落到孔位圆点）
    P.append(f'<path d="M{plugx+34} {cy+8} L262 {cy+8} L262 {wago_y+21}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="216" y="{cy+2}" text-anchor="middle" font-size="8" font-weight="600" fill="#444441" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头黑</text>')
    P.append(f'<text x="232" y="{wago_y+10}" text-anchor="end" font-size="7.5" font-weight="600" fill="#854F0B">万可 221-413</text>')
    P.append(f'<text x="293" y="{wago_y+40}" text-anchor="middle" font-size="7.5" fill="#854F0B">孔1 公头黑 · 孔2 二极管无环端 · 孔3 母头黑</text>')
    # 1N4007：色环端(阴极)→并进 NO 螺丝同孔；无环端→万可孔2（跨泵续流）
    # v5.3.3：本体下移 cy+26 完全脱离蓝盒（盒底 cy+22），引脚下行接万可孔2；
    # 标注移右侧 x=_dx+34 起（避开"COM→NO 常开"说明行），说明行左移缩短不再被本体截断
    _dx, _dy = jx + 79, cy + 26                      # 二极管本体左上角（NO 端子正下，盒外）
    P.append(f'<rect x="{_dx}" y="{_dy}" width="10" height="15" rx="2" fill="#2C2C2A" stroke="#111111" stroke-width="0.6"/>')
    P.append(f'<rect x="{_dx}" y="{_dy+3.5}" width="10" height="3.5" fill="#C9C6BB"/>')   # 色环(阴极,朝上接NO)
    P.append(f'<path d="M{_dx+5} {_dy+15} L{_dx+5} 772 L293 772 L293 {wago_y+21}" stroke="#444441" stroke-width="1.8" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="{_dx+18}" y="{_dy+8}" font-size="7" font-weight="600" fill="#854F0B" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">1N4007</text>')
    P.append(f'<text x="{_dx+18}" y="{_dy+17}" font-size="6.5" fill="#854F0B" stroke="#FCEBEB" stroke-width="2.5" paint-order="stroke">色环端↑同孔插NO</text>')
    # 泵公头 → 插入母座；水泵拟物
    P.append(f'<rect x="536" y="{cy-6}" width="34" height="12" rx="2" fill="#B8BCC4" stroke="#6B7280" stroke-width="0.9"/>')
    P.append(f'<path d="M570 {cy} L600 {cy}" stroke="#6B7280" stroke-width="3"/>')
    P.append(f'<text x="553" y="{cy-12}" text-anchor="middle" font-size="6.5" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">泵公头</text>')
    pump_x = 600
    P.append(f'<rect x="{pump_x}" y="{cy-30}" width="86" height="58" rx="8" fill="#DDEBD0" stroke="#3B6D11" stroke-width="1.2"/>')
    P.append(f'<circle cx="{pump_x+30}" cy="{cy}" r="17" fill="#C4D8B0" stroke="#3B6D11" stroke-width="1"/>')
    import math
    for a in range(0, 360, 60):
        x1 = pump_x+30 + 6*math.cos(math.radians(a)); y1 = cy + 6*math.sin(math.radians(a))
        x2 = pump_x+30 + 15*math.cos(math.radians(a+30)); y2 = cy + 15*math.sin(math.radians(a+30))
        P.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="#7FA35F" stroke-width="2"/>')
    P.append(f'<text x="{pump_x+43}" y="{cy+42}" text-anchor="middle" font-size="8" fill="#27500A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">水泵 3W 浸水</text>')
    # 采购口径备注框
    P.append(f'<rect x="730" y="672" width="250" height="76" rx="6" fill="#FAEEDA" stroke="#854F0B" stroke-width="1"/>')
    P.append(f'<text x="742" y="688" font-size="9" font-weight="600" fill="#633806">采购口径（11/10 已下单）</text>')
    P.append(f'<text x="742" y="703" font-size="8" fill="#633806">USB母转2P端子 · 0.3mm² 纯铜 · 充电款</text>')
    P.append(f'<text x="742" y="716" font-size="8" fill="#633806">SKU1 公头线 30cm ×1 + SKU2 母头线 30cm ×1</text>')
    P.append(f'<text x="742" y="729" font-size="8" fill="#633806">零剪线零焊接 · 万可压接 · 合计 ≤¥4</text>')

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
  <desc>两块400孔面包板画出真实孔阵，ESP32画板身与两排引脚并标注，五个模块画PCB与引脚丝印，继电器画蓝色本体与两排螺丝端子，板外强电区画充电宝/公头线/母头线/万可/水泵/二极管的免剪pigtail接法。</desc>
  <defs>
  <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  </defs>
'''

FOOT = '''  </svg>
  <figcaption>拟物图：孔阵/引脚/端子按实物布局绘制（非严格比例）。图上一共 4 条信号线（黄/紫/灰白/绿——灰白=实物白线，纯白在米色底上不可见故画灰白）+ 2 根电源短线（3V3→右板红轨第2孔 / GND→右板蓝轨第4孔，避开轨桥占的第1孔）+ <b>6 根模块供电短线（左板 b 列孔→红/蓝轨：土壤 b5/b4 · 光敏 b12/b11 · DHT b15/b18，对应清单 #5/#6/#8/#9/#11/#12）</b> + 2 根轨桥；OLED/LED 的供电短线（清单#22/#23/#26）与继电器接线因走线密集只标清单不画长线；模块针序以实物丝印为准，行号窗口（a4–a6 / a10–a13 / a15–a18 / g2–g5 / g7–g9）不变。</figcaption>
  </figure>

  <h2>二、逐线清单（杜邦 21 + 跳线 6 + 元件 2，行号即孔位）</h2>
  <table>
    <tr><th style="width:36px;">#</th><th style="width:130px;">从</th><th style="width:140px;">到</th><th style="width:64px;">线种·色</th><th>孔位 / 说明</th></tr>
    <tr><td>1</td><td>ESP32 3V3（右列第1针）</td><td><b>右板红轨第 2 孔</b></td><td>跳线·红</td><td>全板 3V3 母线起点（第1孔留给轨桥#3）。<b>红轨与主孔区不互通，别插 a1 这类主区孔</b></td></tr>
    <tr><td>2</td><td>ESP32 GND（右列第2针）</td><td><b>右板蓝轨第 4 孔</b></td><td>跳线·黑</td><td>全板 GND 母线，<b>单点共地</b>（第1孔留给轨桥#4）</td></tr>
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
    <tr><td>16</td><td>C1 · 100nF</td><td>—</td><td>元件</td><td><b>c21 ↔ 左板蓝轨</b>（无极性可倒插）</td></tr>
    <tr><td>17</td><td>浮球线 1</td><td><b>b21</b></td><td>杜邦·任意</td><td>节点行 21 的 b 孔</td></tr>
    <tr><td>18</td><td>浮球线 2</td><td><b>左板蓝轨</b>任意孔</td><td>杜邦·任意</td><td>两线可互换；蓝轨在<b>左板外侧竖排</b>（v5.3 按实物移边）</td></tr>
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
    <tr><td>30–32</td><td>继电器 COM / NO / 万可</td><td>泵回路</td><td>板外</td><td><b>pigtail 免剪</b>：公头线红→COM；NO→母头线红（1N4007 色环端同孔并进）；公头黑+母头黑+二极管无环端 → 万可 221-413 三孔；泵公头插母座；NC 不接（见第一节强电区）</td></tr>
  </table>
  <p class="meta">合计：杜邦母对母 21 根（#5–13、#17–18、#20–26、#27–29，其中 3 根剥头拧螺丝）+ 面包板跳线 6 根（#1–4、#14、#19）+ 元件 2 个（R1/C1）+ 强电板外 = <b>pigtail 两根（公头线 30cm + 母头线 30cm，已下单）</b> + 万可 221-413 ×1 + 1N4007 ×1，全程零剪线零焊接。</p>

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

  <p class="foot">花房项目 · Smart GreenHouse · 整机接线总图 v5.3 拟物版（2026-11-11，电源轨按实物移到板两长边竖排 + 强电区 pigtail 免剪方案：公头线+母头线+万可 221-413+1N4007；供电=充电宝小电流模式；由 outputs/接线图生成器/build_wiring_v5.py 参数化生成）· 引脚对照 GreenHouse_v1.ino L55–61 · 器件丝印对照 11/06–11/08 实拍 OCR · 配套《花房接线规划表.md》《花房接线图_水泵.html》</p>
</div>
</body>
</html>
'''

out = r'D:\Documents\workbuddydocument\2026-10-17-08-59-13\docs\操作手册\花房接线图_整机总图.html'
open(out, 'w', encoding='utf-8').write(HEAD + SVG + FOOT)
print('written:', out, len(HEAD+SVG+FOOT), 'bytes')
