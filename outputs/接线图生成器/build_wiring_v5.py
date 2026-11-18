# -*- coding: utf-8 -*-
"""
花房整机接线总图 v5.5 生成器 —— 板旁翻面版（真实 BB400 几何）
================================================================
v5.4（2026-11-12 拍板 A：ESP32 直插面包板）→ v5.5（2026-11-14 拍板 A：直插作废，
实测针顶露头过短杜邦母头套不进 → ESP32 翻面平放板旁，双排针朝天，母头套针身）
与 v5.3.x 两板展开画法的本质区别：
1. 单块 BB400 真实朝向绘制：1–30 位号沿板长轴，字母 a–j 沿板宽；
   5 孔连通条 = 同位号的 a–e 一条 / f–j 一条（垂直于板长轴）——v5.3.x 的
   "字母×5行" 分组是转了 90° 的抽象，v5.4 起按实物语义画。
2. ESP32 翻面平放板旁（位 1–15 空闲备用）：元件面朝下、双排针朝天；
   12 根用线全从针身套母头（长端 ~6mm 咬得住）。注意翻面视图左右列镜像，以针名对号。
3. 模块照旧直插 16–29 位；RC 区 16–18 不变；线材清单不变（16 杜邦 + 9 跳线）。
4. 电源轨 = 上缘红(外)+蓝(内) 各 50 孔，中点断成 2×25 → 跨段必须桥接（清单#3/#4）。

改图改这里（PARAMS 区），跑完自动写 HTML 并做布局审计（audit_layout.py 单独跑）。
"""
import math

# ============ PARAMS ============
POS_PITCH = 24.0        # 位号间距（1–30 沿板长轴）
LETTER_PITCH = 14.0     # 字母行距（a–j 沿板宽）
BX = 150.0              # 位号1 的 x
ROW_A = 432.0           # 字母 a 行的 y（b–e 依次 +14）
GUTTER_H = 26.0         # 中沟高
RAIL_RED_Y = 396.0      # 红轨（外）
RAIL_BLUE_Y = 410.0     # 蓝轨（内，靠 a 行）
BOARD_X0, BOARD_X1 = 140.0, 880.0
BOARD_Y0, BOARD_Y1 = 384.0, 600.0
ESP_POS0, ESP_POS1 = 1, 15          # ESP32 占位 1–15
ESP_PCB_TOP = 424.0                 # PCB 底边压在 a 行上方（针顶从此出线）
ESP_PCB_BOT = 572.0                 # 不盖 j 行（i=566, +6px）
SVG_W, SVG_H = 1300, 960

def pos_x(n):
    return BX + (n - 1) * POS_PITCH

def letter_y(L):
    seq = 'abcdefghij'
    i = seq.index(L)
    if i < 5:
        return ROW_A + i * LETTER_PITCH
    return ROW_A + 5 * LETTER_PITCH + GUTTER_H + (i - 5) * LETTER_PITCH

LEFT_PINS  = ['EN','VP36','VN39','D34','D35','D32','D33','D25','D26','D27','D14','D12','D13','GND','VIN']
RIGHT_PINS = ['3V3','GND','D15','D2','D4','RX2','TX2','D5','D18','D19','D21','RX0','TX0','D22','D23']

# ============ 位号分配（v5.4）============
# 浮球 RC 16–18（R1: a16↔a18，节点=位18）→ 土壤 19–21 → 光敏 22–25 → DHT 26–29 → 30 备用
RC_FEED, RC_NODE = 16, 18
SOIL_POS  = dict(GND=19, V5=20, OUT=21)
LUX_POS   = dict(AO=22, DO=23, GND=24, VCC=25)   # 11/18 实物：左→右 AO DO GND VCC
DHT_POS   = dict(VCC=26, DATA=27, GND=28)   # 11/18 实物：三针版（正/OUT/负），无 NC
RAIL_BREAK_HOLE = 25   # 轨中断：25↔26 之间

def build():
    P = []
    hx = lambda n: pos_x(n)

    # ---------- 1) 面包板本体 ----------
    P.append(f'<rect x="{BOARD_X0}" y="{BOARD_Y0}" width="{BOARD_X1-BOARD_X0}" height="{BOARD_Y1-BOARD_Y0}" rx="10" fill="#F4F1E8" stroke="#B4B2A9" stroke-width="1.5"/>')
    # 板名（放 SVG 顶部，彻底避开轨桥标/走廊/直插模块区）
    P.append(f'<text x="40" y="30" font-size="11" font-weight="600" fill="#5F5E5A">BB400 ×1（真实朝向：1–30 位号沿板长 · 同位号 a–e / f–j 各成一条 5 孔连通）</text>')

    # 电源轨（11/14 领导实测定稿：BB400 四轨型——上下各红+蓝，每条 25 孔贯通无断口）
    # 25 孔对齐位号 3–27（孔距=位号距 24px）；上轨供电、下轨备用
    n_rail = 25
    rail_x0, rail_x1 = pos_x(3), pos_x(27)
    rsp = (rail_x1 - rail_x0) / (n_rail - 1)
    RAIL_RED2_Y  = BOARD_Y1 - 26   # 下红轨（备用）
    RAIL_BLUE2_Y = BOARD_Y1 - 12   # 下蓝轨（备用）
    lab_x = BOARD_X0 + 6
    for (ry, fill, stroke) in [
        (RAIL_RED_Y,  '#E88B8B', '#A32D2D'),
        (RAIL_BLUE_Y, '#8FBCE3', '#185FA5'),
        (RAIL_RED2_Y, '#E88B8B', '#A32D2D'),
        (RAIL_BLUE2_Y, '#8FBCE3', '#185FA5'),
    ]:
        P.append(f'<rect x="{rail_x0-7}" y="{ry-6}" width="{rail_x1-rail_x0+14}" height="12" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>')
        for k in range(1, n_rail + 1):
            rxk = rail_x0 + (k - 1) * rsp
            P.append(f'<circle cx="{rxk:.1f}" cy="{ry}" r="2.2" fill="#FBFAF5" stroke="{stroke}" stroke-width="0.6"/>')
    P.append(f'<text x="{lab_x}" y="{RAIL_RED_Y-18}" font-size="8.5" font-weight="600" fill="#791F1F">红轨 3V3 ┘</text>')
    P.append(f'<text x="{lab_x}" y="{RAIL_BLUE_Y-2}" font-size="8.5" font-weight="600" fill="#0C447C">蓝轨 GND ┘</text>')
    P.append(f'<text x="{lab_x+70}" y="{RAIL_BLUE_Y-2}" font-size="7.5" fill="#888780">各25孔贯通（11/14 实测 · 无断口）</text>')
    P.append(f'<text x="{rail_x1+10}" y="{RAIL_RED2_Y+3}" font-size="7" fill="#888780">下缘双轨备用</text>')

    # 中沟
    gut_y0 = ROW_A + 5 * LETTER_PITCH + 2
    P.append(f'<rect x="{BOARD_X0+8}" y="{gut_y0}" width="{BOARD_X1-BOARD_X0-16}" height="{GUTTER_H-4}" fill="#E4E1D6"/>')
    P.append(f'<text x="{BOARD_X0+22}" y="{gut_y0+16}" font-size="7.5" fill="#A5A296">中沟（DIP）</text>')

    # 孔阵：每位号两条竖条（a–e / f–j），条底淡色区分连通
    for n in range(1, 31):
        x = pos_x(n)
        for (y0, y1, fill) in [(ROW_A-6, ROW_A+4*LETTER_PITCH+6, '#EDEAE0'),
                               (ROW_A+5*LETTER_PITCH+GUTTER_H-6, ROW_A+9*LETTER_PITCH+GUTTER_H+6, '#E6E3D8')]:
            P.append(f'<rect x="{x-5:.1f}" y="{y0}" width="10" height="{y1-y0}" rx="4" fill="{fill}" stroke="none"/>')
        for L in 'abcdefghij':
            P.append(f'<circle cx="{x:.1f}" cy="{letter_y(L):.1f}" r="2.2" fill="#C9C6BB"/>')
        if n == 1 or n % 5 == 0 or n == 30:
            P.append(f'<text x="{x:.1f}" y="{BOARD_Y1+14}" text-anchor="middle" font-size="7.5" fill="#A5A296">{n}</text>')
    for L in 'abcde':
        P.append(f'<text x="{BOARD_X0-8}" y="{letter_y(L)+3:.1f}" text-anchor="end" font-size="7.5" fill="#A5A296">{L}</text>')
    for L in 'fghij':
        P.append(f'<text x="{BOARD_X1+8}" y="{letter_y(L)+3:.1f}" text-anchor="start" font-size="7.5" fill="#A5A296">{L}</text>')
    P.append(f'<text x="{BOARD_X0-8}" y="{BOARD_Y0-4}" text-anchor="end" font-size="7" fill="#888780">1位端</text>')

    # ---------- 2) ESP32 板旁翻面拟物（v5.5：不插板，元件面朝下、双排针朝天） ----------
    # 11/14 实测：直插后针顶露头过短，杜邦母头套不进 → 翻面平放板旁（右下象限）。
    # 出线规则：上排（原左排 EN–VIN，8 根用线）从针尖向上出盒顶 → 上走廊；
    #          下排（原右排 3V3–D23，4 根用线）向下穿盒底 → 右缘绕上行 → 顶走廊。
    # 针名错侧：上排针名画针下方（y=375），下排针名画针上方（y=428）——防走线穿越。
    ex0, ey0, ex1, ey1 = 940, 340, 1270, 500
    P.append(f'<rect x="{ex0}" y="{ey0}" width="{ex1-ex0}" height="{ey1-ey0}" rx="8" fill="#3B4252" stroke="#2E3440" stroke-width="1.5" fill-opacity="0.97"/>')
    P.append(f'<text x="{(ex0+ex1)/2}" y="{ey0+66}" text-anchor="middle" font-size="11" font-weight="600" fill="#ECEFF4">ESP32 30P DevKitC · 翻面平放</text>')
    P.append(f'<text x="{(ex0+ex1)/2}" y="{ey0+81}" text-anchor="middle" font-size="7.5" fill="#B8C0D0">元件面朝下 · 双排针朝天 · 母头从上套针身</text>')
    P.append(f'<text x="{(ex0+ex1)/2}" y="{ey0+94}" text-anchor="middle" font-size="7.5" font-weight="600" fill="#F5A54B">双面胶固定 · 垫高 2mm · USB 朝外（11/14 定）</text>')
    # USB 口拟物（盒底外右角，避开下排出线区；标注左移避 D22 下行线 x=1222）
    P.append(f'<rect x="{ex1-52}" y="{ey1+4}" width="32" height="14" rx="2" fill="#98A2B3" stroke="#6B7280"/>')
    P.append(f'<text x="{ex1-80}" y="{ey1+16}" text-anchor="middle" font-size="7.5" fill="#5F5E5A">USB 供电入口</text>')
    pinpos = {}
    # 上排 = 原左排 EN–VIN（用到的 8 针高亮，其余灰显）
    strip1_used = {'D34':('#E8B54A','600'),'D35':('#B98EE8','600'),'D32':('#7CBF5E','600'),'D33':('#C9C6BB','600'),'D25':('#F0766B','600'),'D26':('#F5A54B','600'),'D27':('#6FCF7C','600'),'VIN':('#F0766B','600')}
    px = 952
    for name in LEFT_PINS:
        col, w = strip1_used.get(name, ('#8A8F98', '400'))
        P.append(f'<rect x="{px-2.6:.1f}" y="{ey0+6}" width="5.2" height="11" rx="1" fill="#E7D06B" fill-opacity="{"1" if name in strip1_used else "0.45"}" stroke="#8A7A2E" stroke-width="0.7"/>')
        P.append(f'<text x="{px:.1f}" y="{ey0+35}" text-anchor="middle" font-size="6.3" font-weight="{w}" fill="{col}">{name}</text>')
        pinpos[('a', name)] = (px, ey0 + 6)
        px += 20
    # 下排 = 原右排 3V3–D23（用到的 4 针高亮）
    strip2_used = {'3V3':('#F0766B','600'),'GND':('#6FA8DC','600'),'D21':('#6FCF7C','600'),'D22':('#E8E6E0','600')}
    px = 962
    for name in RIGHT_PINS:
        col, w = strip2_used.get(name, ('#8A8F98', '400'))
        P.append(f'<rect x="{px-2.6:.1f}" y="{ey0+96}" width="5.2" height="11" rx="1" fill="#E7D06B" fill-opacity="{"1" if name in strip2_used else "0.45"}" stroke="#8A7A2E" stroke-width="0.7"/>')
        P.append(f'<text x="{px:.1f}" y="{ey0+88}" text-anchor="middle" font-size="6.3" font-weight="{w}" fill="{col}">{name}</text>')
        pinpos[('i', name)] = (px, ey0 + 96)
        px += 20
    P.append(f'<text x="{ex0+8}" y="{ey1-8}" font-size="6.5" fill="#8A8F98">视图=翻面俯视（左右列与元件面视角镜像）· 以针名对号</text>')
    # 位 1–15 空闲标示（板上虚线框）+ 1位端标注（挪入框内防左缘走线穿越）
    P.append(f'<rect x="{pos_x(1)-12}" y="{BOARD_Y0+4}" width="{pos_x(15)-pos_x(1)+24}" height="{BOARD_Y1-BOARD_Y0-8}" rx="6" fill="#FBFAF5" fill-opacity="0.55" stroke="#A5A296" stroke-width="1.2" stroke-dasharray="6 4"/>')
    P.append(f'<text x="{(pos_x(1)+pos_x(15))/2:.1f}" y="{(BOARD_Y0+BOARD_Y1)/2-6}" text-anchor="middle" font-size="9" font-weight="600" fill="#888780" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">位 1–15 空闲备用</text>')
    P.append(f'<text x="{(pos_x(1)+pos_x(15))/2:.1f}" y="{(BOARD_Y0+BOARD_Y1)/2+8}" text-anchor="middle" font-size="7.5" fill="#888780" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">（ESP32 已改板旁翻面 · 11/14）</text>')
    P.append(f'<text x="{pos_x(1)-4:.1f}" y="{BOARD_Y0+30}" font-size="7" fill="#888780">← 1 位端</text>')

    # 针尖出线点（v5.5：上排 (px,346) 出盒顶；下排 (px,436) 穿盒底；GND 取下排，与清单 #2 一致）
    def stub(name):
        if name != 'GND' and ('a', name) in pinpos:
            return pinpos[('a', name)]
        return pinpos[('i', name)]

    # ---------- 3) 直插模块拟物（悬跨在真实位号上方：针脚对齐 a 列孔位 x） ----------
    # 三行式盒：题 / 直插位号 / 针名（针名进盒内防与相邻盒/线相撞）
    # 台阶错开：土壤 y=40 / 光敏 y=84 / DHT y=132
    def module_at(pos_list, y, title, sub):
        xs = [pos_x(n) for (n, _) in pos_list]
        bx0 = min(xs) - 16
        w = (max(xs) - min(xs)) + 32
        h = 34
        P.append(f'<rect x="{bx0:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="4" fill="#DDEBD0" fill-opacity="0.97" stroke="#3B6D11" stroke-width="1.2"/>')
        cx = sum(xs) / len(xs)
        P.append(f'<text x="{cx:.1f}" y="{y+13}" text-anchor="middle" font-size="10" font-weight="600" fill="#27500A">{title}</text>')
        P.append(f'<text x="{cx:.1f}" y="{y+23}" text-anchor="middle" font-size="7.5" fill="#4B6B2A">{sub}</text>')
        pins_out = {}
        for (n, lab) in pos_list:
            px = pos_x(n)
            P.append(f'<text x="{px:.1f}" y="{y+31}" text-anchor="middle" font-size="6.5" font-weight="600" fill="#27500A">{lab}</text>')
            # 短针 + 淡虚引导线 + a 孔插入环
            P.append(f'<rect x="{px-2.6:.1f}" y="{y+h+2}" width="5.2" height="11" rx="1" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.7"/>')
            P.append(f'<path d="M{px:.1f} {y+h+15} L{px:.1f} {ROW_A-10}" stroke="#B9B5A5" stroke-width="1" stroke-dasharray="2 4" fill="none" opacity="0.55"/>')
            P.append(f'<circle cx="{px:.1f}" cy="{ROW_A:.1f}" r="3" fill="#E7D06B" fill-opacity="0.85" stroke="#8A7A2E" stroke-width="0.9"/>')
            pins_out[lab] = (px, ROW_A)
        return pins_out

    soil_pins = module_at([(SOIL_POS['GND'], 'GND'), (SOIL_POS['V5'], '5V'), (SOIL_POS['OUT'], 'OUT')],
                          40, '土壤传感器', '直插 a19–a21')
    lux_pins = module_at([(LUX_POS['AO'], 'AO'), (LUX_POS['DO'], 'DO'), (LUX_POS['GND'], 'GND'), (LUX_POS['VCC'], 'VCC')],
                         84, '光敏模块', '直插 a22–a25 · AO左')
    dht_pins = module_at([(DHT_POS['VCC'], '正/VCC'), (DHT_POS['DATA'], 'OUT'), (DHT_POS['GND'], '负/GND')],
                         132, 'DHT11 三针版', '直插 a26–a28')
    P.append(f'<text x="430" y="42" text-anchor="middle" font-size="7.5" fill="#888780">信号侧另一头插同位号 b 列空孔（D34→b21 · D35→b22 · D33→b27）</text>')

    # ---------- 3b) 板外模块拟物（不插板，放左上空域；三行式：题/sub/接线小注，针名盒内） ----------
    def module(x, y, w, h, title, sub, note, pins):
        P.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#DDEBD0" stroke="#3B6D11" stroke-width="1.2"/>')
        P.append(f'<text x="{x+w/2}" y="{y+13}" text-anchor="middle" font-size="10" font-weight="600" fill="#27500A">{title}</text>')
        P.append(f'<text x="{x+w/2}" y="{y+23}" text-anchor="middle" font-size="7.5" fill="#4B6B2A">{sub}</text>')
        P.append(f'<text x="{x+w/2}" y="{y+31}" text-anchor="middle" font-size="6.8" fill="#888780">{note}</text>')
        px = x + w/2 - (len(pins)-1) * 9
        pins_out = {}
        for lab in pins:
            P.append(f'<rect x="{px-2.6:.1f}" y="{y+h-3}" width="5.2" height="9" rx="1" fill="#E7D06B" stroke="#8A7A2E" stroke-width="0.7"/>')
            P.append(f'<text x="{px:.1f}" y="{y+h-6}" text-anchor="middle" font-size="7" font-weight="600" fill="#27500A">{lab}</text>')
            pins_out[lab] = (px, y + h + 6)
            px += 18
        return pins_out

    oled_pins = module(60, 60, 150, 44, 'OLED 0.96 I2C', '板外 · 04 屏架（丝印 VCC/GND/SCL/SDA）', 'SDA/SCL←D21/D22针顶 · VCC/GND←轨', ['VCC','GND','SCL','SDA'])
    led_pins = module(260, 60, 150, 44, '双色 LED 模块', '板外 · 底盘嵌槽', 'R/G←D25/D27针顶 · −←蓝轨', ['−','R','G'])

    # ---------- 4) 继电器拟物（右侧，板外悬放；输入侧端子台凸出盒顶，线从凸台上方进） ----------
    rx, ry = 940, 84
    P.append(f'<rect x="{rx}" y="{ry}" width="200" height="176" rx="8" fill="#2D6CB5" stroke="#1B4E8A" stroke-width="1.5"/>')
    P.append(f'<text x="{rx+100}" y="{ry+26}" text-anchor="middle" font-size="10.5" font-weight="600" fill="#EAF2FB">继电器 JQC-3FF/5VDC</text>')
    P.append(f'<text x="{rx+100}" y="{ry+38}" text-anchor="middle" font-size="8" fill="#C8DCF2">悬放不插板 · 跳帽→H档</text>')
    def screw_row(x0, y0, n, pitch, labels, lab_color='#EAF2FB'):
        out = []
        px = x0
        for i in range(n):
            out.append(f'<rect x="{px-9:.1f}" y="{y0}" width="18" height="14" rx="2" fill="#3A7BC8" stroke="#1B4E8A"/>')
            out.append(f'<circle cx="{px:.1f}" cy="{y0+7:.1f}" r="4.5" fill="#C9D6E8" stroke="#5B7EA6" stroke-width="1"/>')
            out.append(f'<path d="M{px-3:.1f} {y0+7:.1f} L{px+3:.1f} {y0+7:.1f}" stroke="#5B7EA6" stroke-width="1.4"/>')
            px += pitch
        return out
    # 输入侧凸台（盒顶上方 14px，与盒顶贴合），线从凸台顶入
    P += screw_row(rx+30, ry-14, 3, 36, ['DC+', 'DC−', 'IN'])
    for i, lab in enumerate(['DC+', 'DC−', 'IN']):
        P.append(f'<text x="{rx+30+i*36}" y="{ry+10}" text-anchor="middle" font-size="8" font-weight="600" fill="#EAF2FB">{lab}</text>')
    P.append(f'<text x="{rx-8}" y="{ry-8}" text-anchor="end" font-size="7.5" fill="#BBD4EE">输入侧(5V线圈)</text>')
    # 强电侧触点排（盒内下方）
    P += screw_row(rx+30, ry+96, 3, 36, ['NC', 'COM', 'NO'])
    for i, lab in enumerate(['NC', 'COM', 'NO']):
        P.append(f'<text x="{rx+30+i*36}" y="{ry+120}" text-anchor="middle" font-size="8" font-weight="600" fill="#FFD9D9">{lab}</text>')
    P.append(f'<text x="{rx+16}" y="{ry+94}" font-size="7.5" fill="#BBD4EE">强电侧(触点)</text>')
    P.append(f'<text x="{rx+104}" y="{ry+82}" text-anchor="middle" font-size="7.5" fill="#9FBEDD">─── 隔离沿 ───</text>')
    P.append(f'<circle cx="{rx+180}" cy="{ry+150}" r="5" fill="#F5C542" stroke="#B08A1E" stroke-width="1"/>')
    P.append(f'<text x="{rx+168}" y="{ry+154}" text-anchor="end" font-size="7.5" fill="#CFE2F5" stroke="#2D6CB5" stroke-width="2.5" paint-order="stroke">跳帽→H档</text>')

    # ---------- 5) 浮球 RC 区逐孔明细（位 16–18 · v5.6 细化：左下框 + 孔阵插入环） ----------
    # 明细框挪左下空域（原位与强电区相挤），两列：逐孔表 + 逻辑链
    fx, fy = 40, 624
    P.append(f'<rect x="{fx}" y="{fy}" width="436" height="76" rx="5" fill="#FAEEDA" fill-opacity="0.95" stroke="#854F0B" stroke-width="1"/>')
    P.append(f'<text x="{fx+8}" y="{fy+13}" font-size="9" font-weight="600" fill="#633806">浮球 RC 区 · 逐孔明细（节点 = 位 18 竖条，同条五孔连通）</text>')
    # 左列：逐孔表
    rows = [
        ('a16', 'R1 腿①（上端，3V3 侧）', '#15'),
        ('a18', 'R1 腿②（节点侧）', '#15'),
        ('b16', '红跳线 ← 红轨（公对公）', '#14'),
        ('b18', '浮球线 1（裸线直插）', '#17'),
        ('e18', '绿杜邦 ← D32 针身（公-母）', '#19'),
        ('蓝轨任意', '浮球线 2（裸线直插）', '#18'),
    ]
    for i, (hole, what, no) in enumerate(rows):
        yy = fy + 25 + i * 8.5
        P.append(f'<text x="{fx+10}" y="{yy}" font-size="7.5" font-weight="600" fill="#854F0B">{hole}</text>')
        P.append(f'<text x="{fx+62}" y="{yy}" font-size="7.5" fill="#444441">{what}</text>')
        P.append(f'<text x="{fx+212}" y="{yy}" font-size="7.5" fill="#888780">{no}</text>')
    # 右列：逻辑链 + 警告
    P.append(f'<text x="{fx+248}" y="{fy+25}" font-size="7.5" font-weight="600" fill="#633806">电路逻辑（从上到下）</text>')
    P.append(f'<text x="{fx+248}" y="{fy+36}" font-size="7.5" fill="#444441">红轨 3V3 ─R1─→ 节点 ←浮球─→ 蓝轨 GND</text>')
    P.append(f'<text x="{fx+248}" y="{fy+47}" font-size="7.5" fill="#444441">D32 站在节点上读电平：</text>')
    P.append(f'<text x="{fx+248}" y="{fy+58}" font-size="7.5" fill="#444441">有水(靠盖端)=断开=HIGH=正常；没水(贴杆尖)=闭合=LOW=低</text>')
    P.append(f'<text x="{fx+248}" y="{fy+70}" font-size="7" font-weight="600" fill="#A32D2D">⚠ 三孔必须同竖条 · 位置可整体平移（实物用位 23/27 f–j 条）</text>')
    # 孔阵插入环（a16/a18/b16/b18/e18 五孔黄色环，同直插模块样式）
    for (n, L) in [(16,'a'), (18,'a'), (16,'b'), (18,'b'), (18,'e')]:
        P.append(f'<circle cx="{pos_x(n):.1f}" cy="{letter_y(L):.1f}" r="3" fill="none" stroke="#854F0B" stroke-width="1.4" stroke-dasharray="2 1.5"/>')
    # 五孔微标签（孔左侧，避 D32 竖直段 x=570 与既有线）
    for (n, L, lab) in [(16,'a','R1'), (18,'a','R1'), (16,'b','电'), (18,'b','球1'), (18,'e','D32')]:
        P.append(f'<text x="{pos_x(n)-5:.1f}" y="{letter_y(L)-3:.1f}" text-anchor="end" font-size="5.5" font-weight="600" fill="#854F0B">{lab}</text>')

    # ---------- 6) 信号线（虚线=信号；竖直段跨红/蓝轨处垫板色 halo=跨越不搭接） ----------
    # 直插模块信号：ESP32 针顶 → 同位号 b 列孔（D34→b21 / D35→b25 / D33→b27），从孔右侧 8px 下落
    # 板外件信号：针顶 → 左上 OLED/LED 盒；继电器：针顶 → 右侧绕行 → 凸台顶入
    # ---------- 6) 信号线（虚线=信号；v5.5：全部从板旁 ESP32 针尖出发） ----------
    # 上排 8 针（D34/D35/D33/D32/D25/D27/D26/VIN）→ 针尖上行出盒顶 y=320 → 左行 → 分组进板
    # 下排 4 针（D21/D22/3V3/GND）→ 针尖下行穿盒底 y=530 → 左缘绕上行（x=925） → 顶走廊
    ESP_TOP_LANE = 320          # 上排线走廊（盒顶上方，继电器凸台下）
    ESP_BOT_LANE = 530          # 下排线走廊（盒底下方，板右缘外）
    ESP_UP_LANES  = dict(soil=284, lux=268, dht=252, led_r=236, led_g=220, rel_in=216, rel_vin=228)
    ESP_UP_LANE2  = dict(oled_sda=152, oled_scl=136)
    ESP_TOP_LANE2 = 120         # 下排线折上后的顶部走廊（OLED/LED 盒底下）

    def sig_path(pts, color, halo=False):
        d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for (x, y) in pts)
        if halo:
            P.append(f'<path d="{d}" stroke="#F4F1E8" stroke-width="4.6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
        P.append(f'<path d="{d}" stroke="{color}" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
    def sig_label(x, y, text, color, anchor='middle'):
        P.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="8.5" font-weight="600" fill="{color}" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">{text}</text>')

    # 直插模块 3 根（上排针尖→顶走廊→左行→板顶入 a 孔插入环旁下落 b 孔）
    for (pname, n, lane, color, lab) in [
        ('D34', SOIL_POS['OUT'], ESP_UP_LANES['soil'], '#B8860B', 'D34→b21'),
        ('D35', LUX_POS['AO'],   ESP_UP_LANES['lux'],  '#6A3D9A', 'D35→b22'),
        ('D33', DHT_POS['DATA'], ESP_UP_LANES['dht'],  '#888780', 'D33→b27'),
    ]:
        sx, sy = stub(pname)
        tx, ty = pos_x(n), letter_y('b')
        sig_path([(sx, sy), (sx, lane), (tx + 8, lane), (tx + 8, ty), (tx, ty)], color, halo=True)
        sig_label((sx + tx) / 2, lane - 5, lab, color)

    # LED 2 根（上排针尖→顶走廊→左行至板左外 x=120 → 上行→LED 盒针）
    for (pname, pin, lane, color, lab) in [
        ('D25', led_pins['R'], ESP_UP_LANES['led_r'], '#D0342C', 'D25→R'),
        ('D27', led_pins['G'], ESP_UP_LANES['led_g'], '#27500A', 'D27→G'),
    ]:
        sx, sy = stub(pname)
        tx, ty = pin
        sig_path([(sx, sy), (sx, lane), (tx, lane), (tx, ty)], color, halo=True)
        sig_label((sx + tx) / 2, lane - 5, lab, color)

    # OLED 2 根（下排针尖→底走廊**分道下行**→左缘绕上 → 顶走廊2 分道 → OLED 盒针）
    # v5.6 修重合：底段 SDA y=536 / SCL y=524、左缘 x=920/908；顶段 SDA y=134 / SCL y=124（针名带 y115 下方）
    for (pname, pin, lane_bot, lane_top, color, lab) in [
        ('D21', oled_pins['SDA'], 536, 134, '#27500A', 'D21→SDA'),
        ('D22', oled_pins['SCL'], 524, 124, '#888780', 'D22→SCL'),
    ]:
        sx, sy = stub(pname)
        tx, ty = pin
        sig_path([(sx, sy), (sx, lane_bot), (920 if pname=='D21' else 908, lane_bot), (920 if pname=='D21' else 908, lane_top), (tx, lane_top), (tx, ty)], color, halo=True)
        sig_label(700, lane_top + 11, lab, color)

    # 继电器 2 根（上排针尖→顶走廊→左行至 x=860 → 上行 y=52 → 右折 → 竖入凸台顶 y=68）
    # x=860 在"输入侧"标注 bbox（右端对齐 x=932，左端≈872）左侧 12px
    for (pname, k, lane, color, lab) in [
        ('D26', 2, ESP_UP_LANES['rel_in'],  '#EF6C00', 'D26→IN'),
        ('VIN', 0, ESP_UP_LANES['rel_vin'], '#F0766B', 'VIN→DC+'),
    ]:
        sx, sy = stub(pname)
        tx = rx + 30 + k * 36
        sig_path([(sx, sy), (sx, lane), (860, lane), (860, 52), (tx, 52), (tx, 68)], color, halo=True)
        sig_label((sx + 860) / 2, lane - 5, lab, color)

    def rail_x_near(n):
        return rail_x0 + round((pos_x(n) - rail_x0) / rsp) * rsp
    def wire(p1, p2, color, w=2.0, halo=False):
        if halo:
            P.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f}" stroke="#F4F1E8" stroke-width="4.6" fill="none" stroke-linecap="round"/>')
        P.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f}" stroke="{color}" stroke-width="{w}" fill="none" stroke-linecap="round"/>')
    def wire_elbow(pts, color, halo=False):
        d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for (x, y) in pts)
        if halo:
            P.append(f'<path d="{d}" stroke="#F4F1E8" stroke-width="4.6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
        P.append(f'<path d="{d}" stroke="{color}" stroke-width="2.0" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')

    # ---------- 6b) 板外件供电飞线（v5.6 补画：OLED VCC/GND + LED −，走左缘外廊避信号走廊） ----------
    # OLED VCC 针(108,113)：y124 → 左缘 x=48 → y388 → 轨左1孔(198,396)（跨蓝轨 halo）
    wire_elbow([(108, 113), (108, 124), (48, 124), (48, 388), (198, 388), (198, RAIL_RED_Y)], '#D0342C', halo=True)
    # OLED GND 针(126,113)：y131 汇流 → 左缘 x=40 下行 → y418 → 轨左1孔(198,410)
    wire_elbow([(126, 113), (126, 131), (40, 131), (40, 418), (198, 418), (198, RAIL_BLUE_Y)], '#185FA5')
    # LED − 针(317,113)：y138 → 左缘 x=32 → y426 → 轨左2孔(222,410)
    wire_elbow([(317, 113), (317, 138), (32, 138), (32, 426), (222, 426), (222, RAIL_BLUE_Y)], '#185FA5')
    for (ty2, txt) in [(300, 'OLED VCC→红轨'), (320, 'OLED GND→蓝轨'), (340, 'LED −→蓝轨')]:
        P.append(f'<text x="54" y="{ty2}" text-anchor="start" font-size="7.5" font-weight="600" fill="{"#D0342C" if "VCC" in txt else "#185FA5"}" stroke="#FBFAF5" stroke-width="2.5" paint-order="stroke">{txt}</text>')
    # 模块供电：b 列孔 → 右偏 10px → 轨（红线跨蓝轨段 halo=跨越不搭接）
    for (n, color, rail_y, halo) in [
        (SOIL_POS['GND'], '#185FA5', RAIL_BLUE_Y, False),
        (SOIL_POS['V5'],  '#D0342C', RAIL_RED_Y,  True),
        (LUX_POS['GND'],  '#185FA5', RAIL_BLUE_Y, False),
        (LUX_POS['VCC'],  '#D0342C', RAIL_RED_Y,  True),
        (DHT_POS['VCC'],  '#D0342C', RAIL_RED_Y,  True),
        (DHT_POS['GND'],  '#185FA5', RAIL_BLUE_Y, False),
    ]:
        px = pos_x(n)
        wire_elbow([(px, letter_y('b')), (px+10, letter_y('b')), (px+10, rail_y), (rail_x_near(n), rail_y)], color, halo=halo)
    # ESP32 3V3/GND 针尖（下排）→ 斜飞线到轨右端外孔；起点先下折 6px 避开针名带 y=428
    wire((stub('3V3')[0], stub('3V3')[1] + 6), (896, RAIL_RED_Y), '#D0342C', halo=True)
    P.append(f'<text x="880" y="382" text-anchor="end" font-size="7.5" font-weight="600" fill="#D0342C" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">3V3→红轨</text>')
    wire((stub('GND')[0], stub('GND')[1] + 6), (898, RAIL_BLUE_Y), '#185FA5', halo=True)
    P.append(f'<text x="892" y="422" text-anchor="end" font-size="7.5" font-weight="600" fill="#185FA5">GND→蓝轨</text>')
    # （轨桥已删：11/14 实测四轨各 25 孔贯通，无断口——原 #3/#4 两根跳线不再需要）
    # R1 供电：红轨→b16（公对公；跨蓝轨 → halo；贴 R1 体左缘 3px 通过）
    wire((rail_x_near(RC_FEED), RAIL_RED_Y), (pos_x(RC_FEED), letter_y('b')), '#D0342C', halo=True)
    # R1 电阻拟物：a16↔a18；标号放电阻体内（避开 R1 取电竖线）
    P.append(f'<rect x="{pos_x(16)+4:.1f}" y="{letter_y("a")-5}" width="{POS_PITCH*2-8:.1f}" height="10" rx="5" fill="#D8CBA8" stroke="#854F0B" stroke-width="0.8"/>')
    P.append(f'<text x="{pos_x(17):.1f}" y="{letter_y("a")+3}" text-anchor="middle" font-size="6.5" font-weight="600" fill="#633806">R1 1kΩ</text>')
    # （原 C1 拟物已删：100nF 取消 2026-11-14——固件 100ms×3 连稳软件去抖已实测覆盖，c18 孔空出）
    # 浮球1 → b18（圆点+左置标注，避开 D32 竖直段 x=570）
    P.append(f'<circle cx="{pos_x(RC_NODE):.1f}" cy="{letter_y("b"):.1f}" r="3.2" fill="#EF6C00"/>')
    P.append(f'<text x="{pos_x(RC_NODE)-8:.1f}" y="{letter_y("b")+3:.1f}" text-anchor="end" font-size="7.5" fill="#EF6C00">浮球1</text>')
    # 浮球2 → 蓝轨任意孔（v5.6 补画：从 b18 旁出发走轨——两根裸线，图中画飞线示意到蓝轨）
    fb2x = pos_x(RC_NODE) + 20
    P.append(f'<path d="M{fb2x:.1f} {letter_y("b"):.1f} L{fb2x:.1f} {RAIL_BLUE_Y:.1f} L{rail_x_near(26):.1f} {RAIL_BLUE_Y:.1f}" stroke="#EF6C00" stroke-width="1.8" fill="none" stroke-dasharray="2 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
    P.append(f'<text x="644" y="{RAIL_BLUE_Y+16}" text-anchor="start" font-size="7.5" fill="#EF6C00" stroke="#FBFAF5" stroke-width="2.5" paint-order="stroke">浮球2→蓝轨任意</text>')
    # D32 针顶 → e18（绿，走廊 y=368；标放右段 x=540 避左区竖线）
    dxs, dys = stub('D32')
    cor_y = 368
    P.append(f'<path d="M{dxs:.1f} {dys:.1f} L{dxs:.1f} {cor_y} L{pos_x(RC_NODE)+12:.1f} {cor_y} L{pos_x(RC_NODE)+12:.1f} {letter_y("e"):.1f} L{pos_x(RC_NODE):.1f} {letter_y("e"):.1f}" stroke="#27500A" stroke-width="1.8" fill="none" stroke-dasharray="5 3" stroke-linejoin="round" marker-end="url(#arr)"/>')
    P.append(f'<text x="540" y="{cor_y-4}" text-anchor="middle" font-size="8.5" font-weight="600" fill="#27500A" stroke="#FBFAF5" stroke-width="3" paint-order="stroke">针顶D32→e{RC_NODE}</text>')

    # ---------- 8) 板外强电区（拟物，v5.2 pigtail 免剪方案 · 原样保留） ----------
    px0, py0 = 40, 700
    P.append(f'<rect x="{px0-10}" y="{py0-6}" width="{SVG_W-px0}" height="196" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="1"/>')
    P.append(f'<text x="{px0}" y="{py0+8}" font-size="10.5" font-weight="600" fill="#791F1F" stroke="#FCEBEB" stroke-width="4" paint-order="stroke">板外：水泵强电回路（不过面包板）</text>')
    cy = py0 + 52
    P.append(f'<rect x="{px0}" y="{cy-24}" width="76" height="46" rx="6" fill="#DCE9F8" stroke="#185FA5" stroke-width="1.2"/>')
    P.append(f'<rect x="{px0+8}" y="{cy-16}" width="34" height="16" rx="2" fill="#8FBCE3"/>')
    P.append(f'<text x="{px0+38}" y="{cy+16}" text-anchor="middle" font-size="8" fill="#0C447C" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">充电宝 5V ≥1A</text>')
    P.append(f'<text x="{px0+38}" y="{cy+34}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">⚠ 开小电流模式</text>')
    plugx = px0 + 96
    P.append(f'<rect x="{plugx}" y="{cy-12}" width="34" height="24" rx="2" fill="#B8BCC4" stroke="#6B7280" stroke-width="1"/>')
    P.append(f'<rect x="{plugx+6}" y="{cy-5}" width="22" height="10" rx="1" fill="#FBFAF5" stroke="#888170" stroke-width="0.7"/>')
    for i in range(4):
        P.append(f'<rect x="{plugx+8+i*4.6}" y="{cy-3}" width="2.4" height="6" fill="#C9A227"/>')
    P.append(f'<text x="{plugx+17}" y="{cy+30}" text-anchor="middle" font-size="7.5" font-weight="600" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头线 30cm</text>')
    P.append(f'<text x="{plugx+17}" y="{cy+44}" text-anchor="middle" font-size="7" fill="#888170" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">SKU1 插充电宝</text>')
    jx = 300
    P.append(f'<text x="{jx+40}" y="{cy+34}" text-anchor="middle" font-size="7.5" fill="#791F1F" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">常开 · 断电自动停泵</text>')
    P.append(f'<rect x="{jx}" y="{cy-22}" width="120" height="44" rx="6" fill="#2D6CB5" stroke="#1B4E8A" stroke-width="1.2"/>')
    for i,(lab,c) in enumerate([('NC','#A5B8CE'),('COM','#FFB3B3'),('NO','#FFB3B3')]):
        sx = jx + 18 + i*38
        P.append(f'<rect x="{sx-9}" y="{cy-14}" width="18" height="14" rx="2" fill="#3A7BC8" stroke="#1B4E8A"/>')
        P.append(f'<circle cx="{sx}" cy="{cy-7}" r="4.5" fill="#C9D6E8" stroke="#5B7EA6"/>')
        P.append(f'<text x="{sx}" y="{cy+14}" text-anchor="middle" font-size="8.5" font-weight="600" fill="{c}">{lab}</text>')
    P.append(f'<path d="M{plugx+34} {cy-8} L{jx+48} {cy-8}" stroke="#D0342C" stroke-width="2.5"/>')
    P.append(f'<text x="{(plugx+34+jx+48)/2}" y="{cy-16}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头红 → COM</text>')
    P.append(f'<path d="M{jx+103} {cy-8} L500 {cy-8}" stroke="#D0342C" stroke-width="2.5"/>')
    P.append(f'<text x="458" y="{cy-16}" text-anchor="middle" font-size="8" font-weight="600" fill="#A32D2D" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">NO → 母头红</text>')
    P.append(f'<rect x="500" y="{cy-12}" width="34" height="24" rx="3" fill="#C9C6BB" stroke="#888170" stroke-width="1"/>')
    P.append(f'<rect x="504" y="{cy-7}" width="26" height="14" rx="2" fill="#FBFAF5" stroke="#888170" stroke-width="0.7"/>')
    for i in range(4):
        P.append(f'<rect x="{506+i*5.8}" y="{cy-4}" width="2.6" height="8" fill="#B5B2A6"/>')
    P.append(f'<text x="560" y="{cy+30}" text-anchor="middle" font-size="7.5" font-weight="600" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">母头线 30cm</text>')
    P.append(f'<text x="560" y="{cy+44}" text-anchor="middle" font-size="7" fill="#888170" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">SKU2 泵公头插入</text>')
    wago_x, wago_y = 240, 866
    P.append(f'<rect x="{wago_x}" y="{wago_y}" width="76" height="28" rx="4" fill="#F5C542" stroke="#B08A1E" stroke-width="1.2"/>')
    for hx2 in (262, 293):
        P.append(f'<rect x="{hx2-8}" y="{wago_y+4}" width="16" height="9" rx="2" fill="#E0A92E" stroke="#B08A1E" stroke-width="0.7"/>')
        P.append(f'<circle cx="{hx2}" cy="{wago_y+21}" r="4.2" fill="#8A6A10"/>')
    P.append(f'<path d="M508 {cy+12} L508 {wago_y-8} L293 {wago_y-8} L293 {wago_y+21}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="470" y="{wago_y-12}" text-anchor="middle" font-size="8" font-weight="600" fill="#444441" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">母头黑</text>')
    P.append(f'<path d="M{plugx+34} {cy+8} L262 {cy+8} L262 {wago_y+21}" stroke="#2C2C2A" stroke-width="2.5" fill="none" stroke-linejoin="round"/>')
    P.append(f'<text x="216" y="{cy+2}" text-anchor="middle" font-size="8" font-weight="600" fill="#444441" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">公头黑</text>')
    P.append(f'<text x="232" y="{wago_y+10}" text-anchor="end" font-size="7.5" font-weight="600" fill="#854F0B">万可 221-222 两孔</text>')
    P.append(f'<text x="285" y="{wago_y+40}" text-anchor="middle" font-size="7.5" fill="#854F0B">孔1 公头黑 · 孔2 母头黑（二极管 11-14 拍板不装，EMI 写进报告"局限与改进"）</text>')
    _dx, _dy = jx + 79, cy + 26
    P.append(f'<text x="{_dx+8}" y="{_dy+8}" font-size="7" font-weight="600" fill="#854F0B" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">1N4007 未装（备用）</text>')
    P.append(f'<text x="{_dx+8}" y="{_dy+18}" font-size="6.5" fill="#854F0B" stroke="#FCEBEB" stroke-width="2.5" paint-order="stroke">若补装：跨接泵两端（色环朝+），见规划表勘误</text>')
    P.append(f'<rect x="536" y="{cy-6}" width="34" height="12" rx="2" fill="#B8BCC4" stroke="#6B7280" stroke-width="0.9"/>')
    P.append(f'<path d="M570 {cy} L600 {cy}" stroke="#6B7280" stroke-width="3"/>')
    P.append(f'<text x="553" y="{cy-12}" text-anchor="middle" font-size="6.5" fill="#5F5E5A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">泵公头</text>')
    pump_x = 600
    P.append(f'<rect x="{pump_x}" y="{cy-30}" width="86" height="58" rx="8" fill="#DDEBD0" stroke="#3B6D11" stroke-width="1.2"/>')
    P.append(f'<circle cx="{pump_x+30}" cy="{cy}" r="17" fill="#C4D8B0" stroke="#3B6D11" stroke-width="1"/>')
    for a in range(0, 360, 60):
        x1 = pump_x+30 + 6*math.cos(math.radians(a)); y1 = cy + 6*math.sin(math.radians(a))
        x2 = pump_x+30 + 15*math.cos(math.radians(a+30)); y2 = cy + 15*math.sin(math.radians(a+30))
        P.append(f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="#7FA35F" stroke-width="2"/>')
    P.append(f'<text x="{pump_x+43}" y="{cy+42}" text-anchor="middle" font-size="8" fill="#27500A" stroke="#FCEBEB" stroke-width="3" paint-order="stroke">水泵 3W 浸水</text>')
    P.append(f'<rect x="730" y="{py0+96}" width="250" height="76" rx="6" fill="#FAEEDA" stroke="#854F0B" stroke-width="1"/>')
    P.append(f'<text x="742" y="{py0+112}" font-size="9" font-weight="600" fill="#633806">采购口径（11/10 已下单）</text>')
    P.append(f'<text x="742" y="{py0+127}" font-size="8" fill="#633806">USB母转2P端子 · 0.3mm² 纯铜 · 充电款</text>')
    P.append(f'<text x="742" y="{py0+140}" font-size="8" fill="#633806">SKU1 公头线 30cm ×1 + SKU2 母头线 30cm ×1</text>')
    P.append(f'<text x="742" y="{py0+153}" font-size="8" fill="#633806">零剪线零焊接 · 万可压接 · 合计 ≤¥4</text>')

    return '\n'.join(P)

SVG = build()

HEAD = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>花房整机接线总图（板旁翻面版）</title>
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
  <h1>花房整机接线总图 · 板旁翻面版（ESP32 不插板 · 翻面平放 · 真实几何）</h1>
  <p class="meta">花房项目 Smart GreenHouse · 引脚与固件 <code>GreenHouse_v1.ino</code> 第 55–61 行逐一核对 · ESP32 板旁翻面 11/14 定稿（原直插方案针顶露头过短、母头套不进，已作废）· 与《docs/操作手册/花房接线规划表.md》§三同口径（冲突以此图 + 固件为准）· <b>模块针序一律以实物丝印对号入座</b></p>
  <p class="warn">五条铁律：① 模拟线只在 GPIO32–39（ADC1）——土壤 34 / 光敏 35；② 全系统共地只有一处——蓝轨单点回 ESP32 GND；③ <b>红轨/蓝轨与主孔区不互通，电源线别插进主区孔</b>；④ <b>同位号竖条才连通——a–e 一条 / f–j 一条，跨位号不通、跨中沟不通</b>；⑤ <b>电源轨四条各 25 孔贯通（11/14 实测）——无断口无需轨桥；上轨供电、下轨备用</b></p>

  <h2>一、面包板拟物总图（单板 BB400：1–30 位号 × a–j 列 · ESP32 板旁翻面 · 位 1–15 空闲）</h2>
  <figure>
  <svg viewBox="0 0 {SVG_W} {SVG_H}" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" style="font-family:inherit">
  <title>花房整机接线总图：板旁翻面版</title>
  <desc>单块BB400真实朝向：位号1-30沿板长、字母a-j沿板宽、同位号a-e/f-j各成5孔连通条；ESP32板旁翻面（位1-15空闲，双排针朝天，母头套针身）；土壤19-21、光敏22-25、DHT26-29直插，浮球RC区16-18；OLED/LED/继电器为板外件；ESP12根用线全从翻面板针身套母头；上下各红蓝电源轨各25孔贯通（11/14实测）；板外强电区画充电宝/公头线/母头线/万可/水泵/二极管的免剪pigtail接法。</desc>
  <defs>
  <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
  <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  </defs>
'''

FOOT = '''  </svg>
  <figcaption>板旁翻面版：孔阵按真实 BB400 几何绘制（同位号 a–e / f–j 各成一条 5 孔连通，跨位号不通）。<b>直插三模块（土壤 a19–21 / 光敏 a22–25 / DHT a26–29）画在真实位号正上方</b>，短针+淡虚引导线指向所插 a 孔；信号线（虚线）从翻面板针身出、另一头插同位号 b/e 列空孔（D34→b21 · D35→b22 · D33→b27 · D32→e18）；ESP32 位 1–15 空闲；模块取电 6 根为<b>公对公跳线</b>（b 列孔 → 轨，直插后针不露、母头无处可套）。所有跨红/蓝轨的线垫板色光晕 = 飞线跨越不搭接；电源轨各 25 孔贯通无断口（11/14 实测，原轨桥方案作废）；上下轨电气独立，如需用下缘轨须用红↔红/蓝↔蓝两根飞线桥接（11-18 实物即此接法）。<b>孔位可按空位整体平移</b>——RC 区/直插模块的位号是示例，实物用其他同构空位（如 RC 用位 23/27 的 f–j 条）电气等效，只要保持"同竖条取孔、R1 跨两位号、浮球一进节点一进蓝轨"。OLED/LED/继电器为板外件（04 屏架/底盘嵌槽/悬放），接线见盒内小注与清单；模块针序以实物丝印为准。</figcaption>
  </figure>

  <h2>二、逐线清单（杜邦 16 + 跳线 7 + 元件 1，位号即孔位；#3/#4/#16 已取消留档）</h2>
  <table>
    <tr><th style="width:36px;">#</th><th style="width:150px;">从</th><th style="width:150px;">到</th><th style="width:88px;">线种·色</th><th>孔位 / 说明</th></tr>
    <tr><td>1</td><td>ESP32 3V3 针顶（i1）</td><td><b>红轨近1端孔</b></td><td>杜邦·红（公-母）</td><td>全板 3V3 母线起点。公端入轨孔、母端套针顶</td></tr>
    <tr><td>2</td><td>ESP32 GND 针顶（i2）</td><td><b>蓝轨近1端孔</b></td><td>杜邦·黑（公-母）</td><td>全板 GND 母线，<b>单点共地</b></td></tr>
    <tr><td>3</td><td><s>红轨轨桥</s></td><td>—</td><td><s>跳线·红</s></td><td><b>已取消（11/14）</b>：实测轨 25 孔贯通无断口，无需桥接</td></tr>
    <tr><td>4</td><td><s>蓝轨轨桥</s></td><td>—</td><td><s>跳线·黑</s></td><td><b>已取消（11/14）</b>：同上</td></tr>
    <tr><td>5</td><td>土壤 GND（a19 针已插）</td><td>蓝轨</td><td>跳线·黑（公对公）</td><td>两端插孔：<b>b19</b> → 蓝轨孔（同位号竖条与 GND 针连通）</td></tr>
    <tr><td>6</td><td>土壤 5V（a20 针已插）</td><td>红轨</td><td>跳线·红（公对公）</td><td><b>b20</b> → 红轨孔（跨蓝轨飞线；丝印 5V 实接 3V3 ✓ 11/08 已验）</td></tr>
    <tr><td>7</td><td>ESP32 <b>D34</b> 针顶（a4）</td><td><b>b21</b></td><td>杜邦·黄（公-母）</td><td>母端套 D34 针顶、公端插 <b>b21</b>（与土壤 OUT 针 a21 同条）；ADC1 只读脚</td></tr>
    <tr><td>8</td><td>光敏 GND（a24 针已插）</td><td>蓝轨</td><td>跳线·黑（公对公）</td><td><b>b24</b> → 蓝轨孔（11/18 实物：AO DO GND VCC）</td></tr>
    <tr><td>9</td><td>光敏 VCC（a25 针已插）</td><td>红轨</td><td>跳线·红（公对公）</td><td><b>b25</b> → 红轨孔</td></tr>
    <tr><td>10</td><td>ESP32 <b>D35</b> 针顶（a5）</td><td><b>b22</b></td><td>杜邦·紫（公-母）</td><td>母端套 D35 针顶、公端插 <b>b22</b>（与光敏 AO 针 a22 同条）；DO 针<b>悬空不接</b>（raw=1421 已验）</td></tr>
    <tr><td>11</td><td>DHT11 VCC（a26 针已插）</td><td>红轨</td><td>跳线·红（公对公）</td><td><b>b26</b> → 红轨孔（在第2段轨——#3 桥接后有效）</td></tr>
    <tr><td>12</td><td>DHT11 负（a28 针已插）</td><td>蓝轨</td><td>跳线·黑（公对公）</td><td><b>b28</b> → 蓝轨孔（11/18 实物：三针版，位 29 空出）</td></tr>
    <tr><td>13</td><td>ESP32 <b>D33</b> 针顶（a7）</td><td><b>b27</b></td><td>杜邦·白（公-母）</td><td>母端套 D33 针顶、公端插 <b>b27</b>（与 DATA 针 a27 同条）；单总线（29.2℃/68% 已验）</td></tr>
    <tr><td>14</td><td>红轨</td><td><b>b16</b></td><td>跳线·红（公对公）</td><td>浮球上拉取电（R1 上端同位号）</td></tr>
    <tr><td>15</td><td>R1 · 1kΩ（棕黑红）</td><td>—</td><td>元件</td><td>两脚插 <b>a16 ↔ a18</b>：a16=3V3 侧，a18=上拉节点</td></tr>
    <tr><td>16</td><td><s>C1 · 100nF</s></td><td>—</td><td><s>元件</s></td><td><b>已取消（11-14）</b>：固件软件去抖（100ms 采样×连续 3 次一致）实测已覆盖；c18 孔空出</td></tr>
    <tr><td>17</td><td>浮球线 1</td><td><b>b18</b></td><td>裸线直插孔</td><td>节点位 18 的 b 孔</td></tr>
    <tr><td>18</td><td>浮球线 2</td><td><b>蓝轨</b>任意孔</td><td>裸线直插孔</td><td>两线可互换；优先插第1段（1–25）更稳</td></tr>
    <tr><td>19</td><td>ESP32 <b>D32</b> 针顶（a6）</td><td><b>e18</b></td><td>杜邦·绿（公-母）</td><td>母端套 D32 针顶、公端插 <b>e18</b>（节点位 18 同条）</td></tr>
    <tr><td>20</td><td>ESP32 D21 针顶（i11）</td><td>OLED SDA</td><td>杜邦·绿（母-母）</td><td>I2C 数据；OLED 装在 04 屏架（板外）</td></tr>
    <tr><td>21</td><td>ESP32 D22 针顶（i14）</td><td>OLED SCL</td><td>杜邦·白（母-母）</td><td>I2C 时钟</td></tr>
    <tr><td>22</td><td>OLED VCC</td><td>红轨</td><td>杜邦·红（公-母）</td><td>公端入轨孔</td></tr>
    <tr><td>23</td><td>OLED GND</td><td>蓝轨</td><td>杜邦·黑（公-母）</td><td>丝印 GND 针引出</td></tr>
    <tr><td>24</td><td>ESP32 D25 针顶（a8）</td><td>LED 模块 R</td><td>杜邦·红（母-母）</td><td>LED 在底盘嵌槽（板外）；D25/D27 在左排第 8/10 位</td></tr>
    <tr><td>25</td><td>ESP32 D27 针顶（a10）</td><td>LED 模块 G</td><td>杜邦·绿（母-母）</td><td>D26 居中=第 9 位，别认错行</td></tr>
    <tr><td>26</td><td>LED 模块 −</td><td>蓝轨</td><td>杜邦·黑（公-母）</td><td>GND 与全轨贯通</td></tr>
    <tr><td>27</td><td>ESP32 <b>VIN</b> 针顶（a15）</td><td>继电器 <b>DC+</b></td><td>杜邦·红（母-母）</td><td>线圈 5VDC；绝不用 3V3</td></tr>
    <tr><td>28</td><td>蓝轨</td><td>继电器 <b>DC−</b></td><td>杜邦·黑（公-母）</td><td>借蓝轨取 GND</td></tr>
    <tr><td>29</td><td>ESP32 <b>D26</b> 针顶（a9）</td><td>继电器 <b>IN</b></td><td>杜邦·橙（母-母）</td><td>信号线</td></tr>
    <tr><td>30–32</td><td>继电器 COM / NO / 万可</td><td>泵回路</td><td>板外</td><td><b>pigtail 免剪</b>：公头线红→COM；NO→母头线红；公头黑+母头黑 → 万可 221-222 两孔直连；泵公头插母座；NC 不接（~~1N4007~~ 11-14 拍板不装，见强电区注）</td></tr>
  </table>
  <p class="meta">合计：<b>杜邦 16 根</b>（母-母 6：#20/21/24/25/27/29——两端都套针顶；公-母 10：#1/2/7/10/13/19/22/23/26/28——母端套针顶、公端入轨孔或 b/e 列孔）+ <b>跳线公对公 7 根</b>（~~#3/#4 轨桥已取消~~ + #14 R1 取电 + #5/6/8/9/11/12 直插模块取电——直插后模块针已占 a 孔，取电只能两端都插孔）+ 元件 1 个（R1；~~C1 100nF~~ 已取消 11-14——固件软件去抖覆盖）+ 强电板外 = <b>pigtail 两根（公头线 30cm + 母头线 30cm，已下单）</b> + 万可 221-222 ×1（~~1N4007~~ 11-14 拍板不装：触点裕量足够，EMI 抑制写进报告"局限与改进"；补装唯一合规路径=跨接泵两端，见规划表第四节勘误）。<b>⚠ BOM 提醒：公对公跳线需 9 根（学校 40P 杜邦排里公对公那排）、公对母 10 根</b>。第二块面包板不作接线用，留桌面调试备板。</p>

  <h2>二·补、按元器件的接口对照表（本端接口 → 对端接口 · 核对视角）</h2>
  <p class="meta">逐线清单（第二节）是<b>施工视角</b>——拿一根线插两端；本表是<b>核对视角</b>——一个器件的所有接口一屏看全。同一根线两边都出现，用末列「清单#」对号；板上路径列说明这根线经面包板哪个孔中转（直插件的信号/取电都走同位号竖条连通，不是点对点直连）。</p>
  <table>
    <tr><th style="width:190px;">本端接口</th><th style="width:190px;">→ 对端接口</th><th style="width:110px;">线种·色</th><th>板上路径（孔位）</th><th style="width:64px;">清单#</th></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">ESP32 DevKitC（直插位 1–15：左排 a1–a15 / 右排 i1–i15 · USB 朝 1 位端）</td></tr>
    <tr><td>3V3 针顶（i1）</td><td>→ 红轨近 1 端孔</td><td>杜邦·红（公-母）</td><td>直连；全板 3V3 母线起点</td><td>#1</td></tr>
    <tr><td>GND 针顶（i2）</td><td>→ 蓝轨近 1 端孔</td><td>杜邦·黑（公-母）</td><td>直连；<b>单点共地</b></td><td>#2</td></tr>
    <tr><td>D34 针顶（a4）</td><td>→ 土壤 OUT</td><td>杜邦·黄（公-母）</td><td>针顶→<b>b21</b>（与土壤 OUT 针 a21 同条连通）；ADC1</td><td>#7</td></tr>
    <tr><td>D35 针顶（a5）</td><td>→ 光敏 AO</td><td>杜邦·紫（公-母）</td><td>针顶→<b>b25</b>（与 AO 针 a25 同条连通）；ADC1</td><td>#10</td></tr>
    <tr><td>D33 针顶（a7）</td><td>→ DHT11 DATA</td><td>杜邦·白（公-母）</td><td>针顶→<b>b27</b>（与 DATA 针 a27 同条连通）</td><td>#13</td></tr>
    <tr><td>D32 针顶（a6）</td><td>→ 浮球节点（位 18）</td><td>杜邦·绿（公-母）</td><td>针顶→<b>e18</b>（节点同条，外接 1kΩ 上拉；滤抖由固件完成）</td><td>#19</td></tr>
    <tr><td>D21 针顶（i11）</td><td>→ OLED SDA</td><td>杜邦·绿（母-母）</td><td>板外直连（04 屏架）；I2C 数据</td><td>#20</td></tr>
    <tr><td>D22 针顶（i14）</td><td>→ OLED SCL</td><td>杜邦·白（母-母）</td><td>板外直连；I2C 时钟</td><td>#21</td></tr>
    <tr><td>D25 针顶（a8）</td><td>→ LED 模块 R</td><td>杜邦·红（母-母）</td><td>板外直连（底盘嵌槽）</td><td>#24</td></tr>
    <tr><td>D27 针顶（a10）</td><td>→ LED 模块 G</td><td>杜邦·绿（母-母）</td><td>板外直连</td><td>#25</td></tr>
    <tr><td>D26 针顶（a9）</td><td>→ 继电器 IN</td><td>杜邦·橙（母-母）</td><td>板外直连；信号</td><td>#29</td></tr>
    <tr><td>VIN 针顶（a15）</td><td>→ 继电器 DC+</td><td>杜邦·红（母-母）</td><td>板外直连；5V 线圈供电（绝不用 3V3）</td><td>#27</td></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">土壤传感器（直插 a19–a21 · 丝印 5V 实接 3V3 ✓ 11/08 已验）</td></tr>
    <tr><td>GND 针（a19）</td><td>→ 蓝轨</td><td>跳线·黑（公对公）</td><td><b>b19</b> → 蓝轨孔（同条连通）</td><td>#5</td></tr>
    <tr><td>5V 针（a20）</td><td>→ 红轨</td><td>跳线·红（公对公）</td><td><b>b20</b> → 红轨孔</td><td>#6</td></tr>
    <tr><td>OUT 针（a21）</td><td>→ ESP32 D34</td><td>杜邦·黄（公-母）</td><td>a21 同条 → b21 → D34 针顶（模拟信号）</td><td>#7</td></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">光敏模块（直插 a22–a25）</td></tr>
    <tr><td>GND 针（a24）</td><td>→ 蓝轨</td><td>跳线·黑（公对公）</td><td><b>b24</b> → 蓝轨孔</td><td>#8</td></tr>
    <tr><td>VCC 针（a25）</td><td>→ 红轨</td><td>跳线·红（公对公）</td><td><b>b25</b> → 红轨孔</td><td>#9</td></tr>
    <tr><td>AO 针（a22）</td><td>→ ESP32 D35</td><td>杜邦·紫（公-母）</td><td>a22 同条 → b22 → D35 针顶（模拟信号）</td><td>#10</td></tr>
    <tr><td>DO 针（a23）</td><td>→ <b>悬空不接</b></td><td>—</td><td>raw=1421 已验，数字口弃用</td><td>#10 注</td></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">DHT11 三针版（直插 a26–a28 · 正/OUT/负 · 11/18 实物核对）</td></tr>
    <tr><td>正/VCC 针（a26）</td><td>→ 红轨</td><td>跳线·红（公对公）</td><td><b>b26</b> → 红轨孔</td><td>#11</td></tr>
    <tr><td>OUT/DATA 针（a27）</td><td>→ ESP32 D33</td><td>杜邦·白（公-母）</td><td>a27 同条 → b27 → D33 针顶（单总线）</td><td>#13</td></tr>
    <tr><td>负/GND 针（a28）</td><td>→ 蓝轨</td><td>跳线·黑（公对公）</td><td><b>b28</b> → 蓝轨孔；位 29 空出</td><td>#12</td></tr>
    <tr><td colspan="5" style="background:#FAF0DA;font-weight:600;">浮球 RC 区（位 16–18 · 全在位 18 同一条竖条取孔，不跨位号）</td></tr>
    <tr><td>红轨</td><td>→ R1 上端（a16）</td><td>跳线·红（公对公）</td><td>红轨孔 → <b>b16</b>（与 a16 同条）</td><td>#14</td></tr>
    <tr><td>R1 · 1kΩ（棕黑红）</td><td>a16 ↔ a18</td><td>元件</td><td>两脚直插孔；a18=上拉节点</td><td>#15</td></tr>
    <tr><td>~~C1 · 100nF~~</td><td>—</td><td>已取消</td><td>软件去抖覆盖（11-14）；c18 空出</td><td>#16</td></tr>
    <tr><td>浮球线 1</td><td>→ b18</td><td>裸线直插孔</td><td>节点位 18 的 b 孔</td><td>#17</td></tr>
    <tr><td>浮球线 2</td><td>→ 蓝轨任意孔</td><td>裸线直插孔</td><td>两线可互换；优先第 1 段（1–25）</td><td>#18</td></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">OLED 0.96 I2C（板外 · 04 屏架 · 丝印左→右 VCC/GND/SCL/SDA）</td></tr>
    <tr><td>VCC</td><td>→ 红轨</td><td>杜邦·红（公-母）</td><td>公端入轨孔</td><td>#22</td></tr>
    <tr><td>GND</td><td>→ 蓝轨</td><td>杜邦·黑（公-母）</td><td>公端入轨孔</td><td>#23</td></tr>
    <tr><td>SDA</td><td>→ ESP32 D21 针顶</td><td>杜邦·绿（母-母）</td><td>板外直连</td><td>#20</td></tr>
    <tr><td>SCL</td><td>→ ESP32 D22 针顶</td><td>杜邦·白（母-母）</td><td>板外直连</td><td>#21</td></tr>
    <tr><td colspan="5" style="background:#EAF3E1;font-weight:600;">双色 LED 模块（板外 · 底盘嵌槽 · 自带限流电阻）</td></tr>
    <tr><td>R</td><td>→ ESP32 D25 针顶</td><td>杜邦·红（母-母）</td><td>板外直连</td><td>#24</td></tr>
    <tr><td>G</td><td>→ ESP32 D27 针顶</td><td>杜邦·绿（母-母）</td><td>板外直连</td><td>#25</td></tr>
    <tr><td>−</td><td>→ 蓝轨</td><td>杜邦·黑（公-母）</td><td>公端入轨孔；GND 经 #2/#4 桥通</td><td>#26</td></tr>
    <tr><td colspan="5" style="background:#E3EDF8;font-weight:600;">继电器 JQC-3FF/5VDC（板外 · 悬放 · 跳帽 H 档）</td></tr>
    <tr><td>DC+</td><td>→ ESP32 VIN 针顶</td><td>杜邦·红（母-母）</td><td>板外直连；线圈 5VDC</td><td>#27</td></tr>
    <tr><td>DC−</td><td>→ 蓝轨</td><td>杜邦·黑（公-母）</td><td>公端入轨孔；借蓝轨取 GND</td><td>#28</td></tr>
    <tr><td>IN</td><td>→ ESP32 D26 针顶</td><td>杜邦·橙（母-母）</td><td>板外直连</td><td>#29</td></tr>
    <tr><td>COM</td><td>→ 公头线红（充电宝 5V+）</td><td>pigtail</td><td>板外强电；公头线另一端插充电宝</td><td>#30–32</td></tr>
    <tr><td>NO</td><td>→ 母头线红（→ 泵正）</td><td>pigtail</td><td>常开=断电自动停泵；~~1N4007 并进~~ 11-14 不装</td><td>#30–32</td></tr>
    <tr><td>NC</td><td>→ <b>不接（空着）</b></td><td>—</td><td>接 NC = 一上电就抽水</td><td>—</td></tr>
    <tr><td colspan="5" style="background:#FCEBEB;font-weight:600;">板外泵强电回路（充电宝 → 继电器 → 泵 · 不过面包板 · 全程零剪线）</td></tr>
    <tr><td>充电宝 USB 口</td><td>→ 公头线 30cm（SKU1）</td><td>pigtail</td><td>⚠ 先开小电流模式</td><td>#30–32</td></tr>
    <tr><td>公头线黑</td><td>→ 万可 221-222 孔1</td><td>pigtail</td><td>5V 负极汇流</td><td>#30–32</td></tr>
    <tr><td>~~1N4007~~</td><td>—</td><td>未装·备用</td><td>11-14 拍板不装（触点裕量足够）；补装需跨接泵两端（色环朝 +），WAGO 无法合规实现三线节点</td><td>#30–32</td></tr>
    <tr><td>母头线黑</td><td>→ 万可 221-222 孔2</td><td>pigtail</td><td>→ 泵负</td><td>#30–32</td></tr>
    <tr><td>泵公头</td><td>→ 母头线插座（SKU2）</td><td>pigtail</td><td>母头红=NO 来的 5V+，黑=万可孔3</td><td>#30–32</td></tr>
  </table>

  <h2>三、ESP32 端口占用总表（= 固件 55–61 行 + I2C 默认）</h2>
  <table>
    <tr><th>GPIO</th><th>丝印（直插位）</th><th>接谁</th><th>方向</th><th>为什么是这个脚</th></tr>
    <tr><td><b>34</b></td><td>D34（a4）</td><td>土壤 OUT</td><td>ADC1 只进</td><td>ADC1 组，WiFi 开启不受影响；只读脚不能接输出设备</td></tr>
    <tr><td><b>35</b></td><td>D35（a5）</td><td>光敏 AO</td><td>ADC1 只进</td><td>同上；DO 弃用</td></tr>
    <tr><td><b>33</b></td><td>D33（a7）</td><td>DHT11 DATA</td><td>数字双向</td><td>单总线，模块自带上拉</td></tr>
    <tr><td><b>32</b></td><td>D32（a6）</td><td>浮球干接点</td><td>数字输入</td><td>外接 1kΩ 上拉（fail-safe）+ 固件 100ms×3 连稳去抖（C1 已取消）</td></tr>
    <tr><td><b>26</b></td><td>D26（a9）</td><td>继电器 IN</td><td>数字输出</td><td>普通 IO，无启动毛刺历史问题（v1.3 已锁）</td></tr>
    <tr><td><b>25</b> / <b>27</b></td><td>D25 / D27（a8/a10）</td><td>LED 红 / 绿</td><td>数字输出</td><td>模块带限流电阻，直驱</td></tr>
    <tr><td><b>21</b> / <b>22</b></td><td>D21 / D22（i11/i14）</td><td>OLED SDA / SCL</td><td>I2C</td><td>硬件 I2C 默认脚（0x3C 实扫确认）</td></tr>
    <tr><td><b>VIN</b></td><td>VIN（a15）</td><td>继电器 DC+</td><td>电源 5V</td><td>线圈 5VDC；USB 供电时 ≈4.7V 可用；绝不用 3V3</td></tr>
    <tr><td>3V3</td><td>3V3（i1）</td><td>红轨母线</td><td>电源 3.3V</td><td>喂 4 个传感器 + 浮球上拉</td></tr>
    <tr><td>⚠️ 禁用</td><td>GPIO 6–11 / 12 / 4 / 13 / 14 等</td><td>—</td><td>—</td><td>6–11 接 flash 碰了变砖；12 启动脚拉错刷不进固件；4/13/14 属 ADC2 WiFi 一开读数全废——本机均未用</td></tr>
  </table>

  <h2>四、通电前 60 秒核对（打勾才上电）</h2>
  <ol>
    <li><b>ESP32 插稳</b>：左排 a1–a15 / 右排 i1–i15 全针入孔，板身不翘；USB 朝 1 位端</li>
    <li><b>轨贯通自检</b>：万用表蜂鸣档量轨首尾孔——通（11/14 已实测贯通，无需轨桥）；不通则查轨是否插对颜色</li>
    <li><b>共地单点</b>：ESP32 GND → 蓝轨只有 #2 一根线（#28 继电器 DC− 借蓝轨）</li>
    <li><b>模拟双线</b>：土壤 OUT→D34、光敏 AO→D35，没插到 ADC2 组</li>
    <li><b>继电器供电</b>：DC+ 接的是 <b>VIN</b> 不是 3V3；线圈 5VDC</li>
    <li><b>触点侧</b>：接 COM+NO，NC 空着（接 NC = 一上电就抽水）</li>
    <li><b>浮球 RC</b>：节点全在<b>位 18 同一条竖条</b>（a=R1 / b=浮球1 / e=D32；~~c=C1~~ 已取消）· <b>11-18 三测定稿：没水(贴杆尖)=闭合→判低；有水(靠盖端)=断开</b> → 固件 `LEVEL_WET_CLOSED=false`</li>
    <li><b>二极管</b>：未装（11-14 拍板）——万可两孔无法合规并联，触点裕量足够；EMI 抑制写入报告"局限与改进"</li>
    <li><b>跳帽</b>：High/Low 跳帽在 <b>H 档</b>；吸合逻辑反了先拨 L 档验证，再查 <code>RELAY_ACTIVE_HIGH</code></li>
    <li><b>固件先决</b>：联调烧 <code>RelayPumpTest</code>，测完烧回 <code>GreenHouse_v1</code> v1.6</li>
  </ol>

  <p class="foot">花房项目 · Smart GreenHouse · 整机接线总图 v5.4 单板直插版（2026-11-12：领导拍板 ESP32 直插 BB400 并实测跨距 a↔i 通过；真实几何重画——同位号 a–e/f–j 竖条连通、电源轨中断 2×25 加轨桥；ESP32 占位 1–15、模块 16–30；信号一律针顶夹持；v5.3.5 两板版备份于 生成器目录 build_wiring_v5_备份v5.3.5.py）· 引脚对照 GreenHouse_v1.ino L55–61 · 配套《花房接线规划表.md》《花房接线图_水泵.html》</p>
</div>
</body>
</html>
'''

out = r'D:\Documents\workbuddydocument\2026-10-17-08-59-13\docs\操作手册\花房接线图_整机总图.html'
open(out, 'w', encoding='utf-8').write(HEAD + SVG + FOOT)
print('written:', out, len(HEAD+SVG+FOOT), 'bytes')
