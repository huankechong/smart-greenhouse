# -*- coding: utf-8 -*-
"""
花房 Final Project 系统概念模型生成器 v3.3（参数化 glTF）
零依赖。分区布局: 左后=面包板电控区 / 左前=OLED / 中右前=花盆 / 右后=水箱水泵
v3.3: 全局重排消除穿模（面包板转90°、花盆右移、水箱后置、全线路径重算）
用法: python build_greenhouse_model.py -> 花房系统概念模型_v3_参数化.glb
坐标: Y向上, 底板顶面y=0, X左(-)右(+), Z后(-)前(+)
"""
import json, struct, math, os

# ---------- 尺寸参数（mm，W1 到货实测后回填） ----------
P = {
    "baseplate":  (320, 5, 230),
    "breadboard": (60, 8, 170),       # 转向: 长边沿Z
    "esp32":      (28, 3, 55),        # 随板转向
    "pot_top": 55, "pot_bot": 40, "pot_h": 95, "pot_x": 55, "pot_z": 55,
    "tank":       (150, 110, 90), "tank_x": 80, "tank_z": -50,
    "pump_r": 16, "pump_h": 30,
    "tube_r": 3, "wire_r": 1.4,
}

C = {  # 配色: 结构灰 / 电控黑白 / 水路蓝 / 植物绿 / 白=3D打印件
    "baseplate": (0.52, 0.55, 0.58, 1.0),
    "edge":      (0.38, 0.41, 0.44, 1.0),
    "breadboard": (0.88, 0.89, 0.92, 1.0),
    "rail_red":  (0.75, 0.10, 0.10, 1.0),
    "rail_blu":  (0.10, 0.22, 0.70, 1.0),
    "esp32": (0.13, 0.13, 0.15, 1.0),
    "usb": (0.75, 0.77, 0.80, 1.0),
    "antenna": (0.80, 0.70, 0.30, 1.0),
    "header": (0.08, 0.08, 0.09, 1.0),
    "led_red": (0.95, 0.15, 0.12, 1.0),
    "led_green": (0.15, 0.85, 0.25, 1.0),
    "lampshade": (1.0, 1.0, 1.0, 0.40),
    "tank": (0.16, 0.35, 0.65, 0.18),
    "water": (0.22, 0.52, 0.95, 0.55),
    "pump": (0.20, 0.20, 0.23, 1.0),
    "tube": (0.25, 0.62, 0.95, 1.0),
    "pot": (0.78, 0.38, 0.22, 1.0),
    "rim": (0.70, 0.33, 0.19, 1.0),
    "soil": (0.32, 0.21, 0.13, 1.0),
    "stem": (0.22, 0.58, 0.22, 1.0),
    "leaf": [(0.30,0.75,0.30,1),(0.36,0.82,0.36,1),(0.22,0.63,0.26,1)],
    "bracket": (0.97, 0.97, 0.98, 1.0),
    "hole": (0.15, 0.16, 0.18, 1.0),
    "sensor": (0.12, 0.40, 0.90, 1.0),
    "probe": (0.85, 0.85, 0.90, 1.0),
    "oled_stand": (0.97, 0.97, 0.98, 1.0),
    "oled_screen": (0.04, 0.05, 0.06, 1.0),
    "w_red": (0.90, 0.12, 0.10, 1.0), "w_blk": (0.06, 0.06, 0.07, 1.0),
    "w_ylw": (0.95, 0.78, 0.10, 1.0), "w_blu": (0.12, 0.40, 0.90, 1.0),
    "w_brn": (0.45, 0.28, 0.12, 1.0),
}

# ---------- glTF 装配 ----------
buf = bytearray()
bufferViews, accessors, meshes, materials, nodes = [], [], [], [], []

def add_view(data, target):
    global buf
    while len(buf) % 4: buf += b"\x00"
    off = len(buf); buf += data
    bufferViews.append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target})
    return len(bufferViews) - 1

def add_accessor_f32(verts, bv):
    mn = [min(v[i] for v in verts) for i in range(3)]
    mx = [max(v[i] for v in verts) for i in range(3)]
    accessors.append({"bufferView": bv, "componentType": 5126, "count": len(verts), "type": "VEC3", "min": mn, "max": mx})
    return len(accessors) - 1

def add_accessor_u16(idx, bv):
    accessors.append({"bufferView": bv, "componentType": 5123, "count": len(idx), "type": "SCALAR", "min": [min(idx)], "max": [max(idx)]})
    return len(accessors) - 1

def add_material(name, rgba, blend=False):
    m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": list(rgba), "metallicFactor": 0.0, "roughnessFactor": 0.55}, "doubleSided": True}
    if blend: m["alphaMode"] = "BLEND"
    materials.append(m); return len(materials) - 1

def add_mesh(name, verts, idx):
    bv_v = add_view(struct.pack(f"<{len(verts)*3}f", *[c for v in verts for c in v]), 34962)
    bv_i = add_view(struct.pack(f"<{len(idx)}H", *idx), 34963)
    a_v = add_accessor_f32(verts, bv_v); a_i = add_accessor_u16(idx, bv_i)
    meshes.append({"name": name, "primitives": [{"attributes": {"POSITION": a_v}, "indices": a_i, "mode": 4}]})
    return len(meshes) - 1

def add_node(name, mesh, mat, t=(0,0,0), q=None, s=None):
    meshes[mesh]["primitives"][0]["material"] = mat
    n = {"name": name, "mesh": mesh, "translation": list(t)}
    if q: n["rotation"] = list(q)
    if s: n["scale"] = list(s)
    nodes.append(n); return len(nodes) - 1

# ---------- 基础网格 ----------
def box(w, h, d):
    x, y, z = w/2, h/2, d/2
    v = [[-x,-y,-z],[x,-y,-z],[x,-y,z],[-x,-y,z],[-x,y,-z],[x,y,-z],[x,y,z],[-x,y,z],
         [-x,-y,-z],[-x,y,-z],[-x,y,z],[-x,-y,z],[x,-y,-z],[x,y,-z],[x,y,z],[x,-y,z],
         [-x,-y,z],[-x,y,z],[x,y,z],[-x,-y,z],[-x,-y,-z],[x,y,-z],[x,y,z],[-x,-y,-z]]
    i = []
    for a,b,c in [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(8,9,10),(8,10,11),(12,14,13),(12,15,14),(16,17,18),(16,18,19),(20,22,21),(20,21,23)]:
        i += [a,b,c]
    return v, i

def cylinder(r_top, r_bot, h, seg=24):
    v, i = [], []
    for k in range(seg):
        a = 2*math.pi*k/seg; v.append([r_top*math.cos(a), h/2, r_top*math.sin(a)])
    for k in range(seg):
        a = 2*math.pi*k/seg; v.append([r_bot*math.cos(a), -h/2, r_bot*math.sin(a)])
    v.append([0, h/2, 0]); v.append([0, -h/2, 0])
    for k in range(seg):
        k2 = (k+1) % seg
        i += [k, k2, seg+k2,  k, seg+k2, seg+k]
        i += [seg*2, k2, k]; i += [seg*2+1, seg+k, seg+k2]
    return v, i

def sphere(r, seg=20, rings=14):
    v, i = [], []
    for ri in range(rings+1):
        phi = math.pi*ri/rings
        for k in range(seg):
            th = 2*math.pi*k/seg
            v.append([r*math.sin(phi)*math.cos(th), r*math.cos(phi), r*math.sin(phi)*math.sin(th)])
    for ri in range(rings):
        for k in range(seg):
            k2 = (k+1) % seg
            a, b = ri*seg+k, ri*seg+k2; c, d = (ri+1)*seg+k, (ri+1)*seg+k2
            i += [a,b,c, b,d,c]
    return v, i

def ring(r_out, r_in, h, seg=28):
    """空心圆环（盆沿）——真开孔，探针/茎从孔中过"""
    v, i = [], []
    for ring_r, yy in [(r_out, h/2), (r_in, h/2), (r_out, -h/2), (r_in, -h/2)]:
        for k in range(seg):
            a = 2*math.pi*k/seg
            v.append([ring_r*math.cos(a), yy, ring_r*math.sin(a)])
    TO, TI, BO, BI = 0, seg, seg*2, seg*3
    for k in range(seg):
        k2 = (k+1) % seg
        i += [TO+k2, TO+k, TI+k,  TO+k2, TI+k, TI+k2]
        i += [BO+k, BO+k2, BI+k,  BO+k2, BI+k2, BI+k]
        i += [BO+k2, BO+k, TO+k,  BO+k2, TO+k, TO+k2]
        i += [BI+k, BI+k2, TI+k,  BI+k2, TI+k2, TI+k]
    return v, i

def quat_to_dir(dx, dy, dz):
    """返回把 +Y 旋到方向(dx,dy,dz)的四元数和长度"""
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    if L == 0: return (0,0,0,1), 0.0
    dx, dy, dz = dx/L, dy/L, dz/L
    if dy > 0.99999: return (0,0,0,1), L
    if dy < -0.99999: return (1,0,0,0), L
    ax, az = dz, -dx
    s = math.sqrt(ax*ax + az*az)
    ax, az = ax/s, az/s
    ang = math.acos(max(-1.0, min(1.0, dy))); ha = ang/2
    return (ax*math.sin(ha), 0.0, az*math.sin(ha), math.cos(ha)), L

_tube_cache = {}
def tube_between(name, p1, p2, r, mat, seg=14):
    q, L = quat_to_dir(p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    if L < 0.5: return None
    mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
    key = ("cyl", r, round(L,2), seg)
    if key not in _tube_cache:
        _tube_cache[key] = add_mesh("m_auto_" + str(len(_tube_cache)), *cylinder(r, r, L, seg))
    return add_node(name, _tube_cache[key], mat, mid, q=q)

# ================= 装配（v3.3 分区布局） =================
# 1. 整合底板 P1-6 + 边框 + 四角安装孔
w,h,d = P["baseplate"]
add_node("整合底板_P1-6", add_mesh("m_base", *box(w,h,d)), add_material("mat_base", C["baseplate"]), (0,-h/2,0))
m_edge = add_material("mat_edge", C["edge"])
add_node("底板边框_前", add_mesh("m_ef", *box(w-6, 0.8, 2)), m_edge, (0, 0.4, d/2-3))
add_node("底板边框_后", add_mesh("m_eb", *box(w-6, 0.8, 2)), m_edge, (0, 0.4, -d/2+3))
add_node("底板边框_左", add_mesh("m_el", *box(2, 0.8, d-6)), m_edge, (-w/2+3, 0.4, 0))
add_node("底板边框_右", add_mesh("m_er", *box(2, 0.8, d-6)), m_edge, (w/2-3, 0.4, 0))
m_hole = add_material("mat_hole", C["hole"])
for cx, cz in [(-w/2+10, d/2-10), (w/2-10, d/2-10), (-w/2+10, -d/2+10), (w/2-10, -d/2+10)]:
    add_node(f"安装孔_{cx}_{cz}", add_mesh("mh_"+str(cx)+str(cz), *cylinder(2.6, 2.6, 1.2, 12)), m_hole, (cx, 0.4, cz))

# 2. 面包板（左区，长边沿Z贴左缘）+ 电源轨沿长边
bw,bh,bd = P["breadboard"]; bx,bz = -30, -5
add_node("面包板", add_mesh("m_bb", *box(bw,bh,bd)), add_material("mat_bb", C["breadboard"]), (bx,bh/2,bz))
add_node("面包板_电源轨红", add_mesh("m_rr", *box(3, 0.8, bd-8)), add_material("mrr", C["rail_red"]), (bx-bw/2+5, bh+0.4, bz))
add_node("面包板_电源轨蓝", add_mesh("m_rb", *box(3, 0.8, bd-8)), add_material("mrb", C["rail_blu"]), (bx+bw/2-5, bh+0.4, bz))
add_node("面包板_中槽", add_mesh("m_rc", *box(3, 0.8, bd-8)), m_edge, (bx, bh+0.4, bz))

# 3. ESP32（板中，长边沿Z）+ USB(前端)/天线(后端)/排针(两侧)
ew,eh,ed = P["esp32"]
add_node("ESP32主控", add_mesh("m_esp", *box(ew,eh,ed)), add_material("mat_esp", C["esp32"]), (bx,bh+eh/2,bz))
add_node("ESP32_USB口", add_mesh("m_usb", *box(12,3.5,9)), add_material("mat_usb", C["usb"]), (bx, bh+eh+1.7, bz+ed/2-5))
add_node("ESP32_天线区", add_mesh("m_ant", *box(12,1.5,9)), add_material("mat_ant", C["antenna"]), (bx, bh+eh+0.7, bz-ed/2+5))
for ox_, nm in [(-15, "排针左"), (15, "排针右")]:
    add_node(f"ESP32_{nm}", add_mesh("m_ph"+nm, *box(2.5,4,ed-5)), add_material("mat_hdr", C["header"]), (bx+ox_, bh+eh+2, bz))

# 4. 状态 LED ×2 + 半透明灯罩 P1-5（板前端）
for (name, col, lx) in [("状态LED_红","led_red",-38), ("状态LED_绿","led_green",-22)]:
    add_node(name, add_mesh("m_"+name, *cylinder(3,3,8,12)), add_material("mat_"+name, C[col]), (lx, bh+4, 70))
add_node("灯罩_半透明_P1-5", add_mesh("m_shade", *sphere(10)), add_material("mat_shade", C["lampshade"], blend=True), (-30, 15, 70), s=(1, 0.75, 1))

# 5. 水箱 + 水位 + 水泵 + P0-2 水泵固定座（右后）
tw,th,td = P["tank"]; tx,tz = P["tank_x"], P["tank_z"]
add_node("水箱(半透明)", add_mesh("m_tank", *box(tw,th,td)), add_material("mat_tank", C["tank"], blend=True), (tx, th/2, tz))
add_node("水箱_水位", add_mesh("m_water", *box(tw-16, 55, td-16)), add_material("mat_water", C["water"], blend=True), (tx, 31, tz))
add_node("水泵(箱内)", add_mesh("m_pump", *cylinder(P["pump_r"], P["pump_r"], P["pump_h"])), add_material("mat_pump", C["pump"]), (tx, P["pump_h"]/2, tz))
add_node("水泵固定座_P0-2", add_mesh("m_pm", *cylinder(21, 21, 6, 24)), add_material("mat_pmt", C["bracket"]), (tx, 4, tz))
for s_, nm in [(-26, "卡爪左"), (26, "卡爪右")]:
    add_node(f"水泵座_{nm}", add_mesh("m_pm"+nm, *box(10, 6, 30)), add_material("mat_pmt2", C["bracket"]), (tx+s_, 3.5, tz))

# 6. 水管：立管(120,25 盆外) -> 过顶 -> 下探至 P0-3 夹 -> 内折 -> 出水口(土面上方)
m_tube = add_material("mat_tube", C["tube"])
tr = P["tube_r"]
add_node("水管_立管", add_mesh("m_vp", *cylinder(tr, tr, 113)), m_tube, (120, 113/2, 25))
tube_between("水管_斜段_过顶", (120, 113, 25), (75, 124, 55), tr, m_tube)
tube_between("水管_斜段_下探", (75, 124, 55), (95, 106, 75), tr, m_tube)
add_node("水管固定夹_P0-3", add_mesh("m_clamp", *box(12, 9, 12)), add_material("mat_cl", C["bracket"]), (95, 104, 75))
tube_between("水管_内折段", (95, 106, 75), (70, 109, 60), tr, m_tube)
add_node("出水口_土面上方_P0-3", add_mesh("m_noz", *cylinder(4, 3, 9, 14)), m_tube, (70, 106.5, 60))

# 7. 花盆 + 空心盆沿 + 土 + 植物（中右前）
px,pz = P["pot_x"], P["pot_z"]
add_node("花盆", add_mesh("m_pot", *cylinder(P["pot_top"], P["pot_bot"], P["pot_h"])), add_material("mat_pot", C["pot"]), (px, P["pot_h"]/2, pz))
add_node("花盆_盆沿", add_mesh("m_rim", *ring(57, 45, 6, 28)), add_material("mat_rim", C["rim"]), (px, 92, pz))
add_node("盆土", add_mesh("m_soil", *cylinder(48, 48, 6, 28)), add_material("mat_soil", C["soil"]), (px, 92, pz))
add_node("植物_茎", add_mesh("m_stem", *cylinder(2.5, 3.5, 62)), add_material("mat_stem", C["stem"]), (px, 121, pz))
leaves = [(px,158,pz,1.05,0), (px-11,144,pz+11,0.95,1), (px+11,148,pz-11,0.90,2),
          (px-3,170,pz-13,0.80,1), (px+13,166,pz+7,0.85,2), (px,178,pz,0.70,0)]
for n_,(lx,ly,lz,sc,ci) in enumerate(leaves):
    add_node(f"植物_叶{n_+1}", add_mesh(f"m_lf{n_}", *sphere(17)), add_material(f"mat_lf{n_}", C["leaf"][ci]), (lx,ly,lz), s=(sc, 0.8*sc, sc))

# 8. 土壤传感器 + L 支架 P0-1（横臂跨盆沿带 M3 孔位，探针入土）
m_br = add_material("mat_br", C["bracket"])
add_node("传感器L支架_横臂_P0-1", add_mesh("m_br1", *box(34, 4, 18)), m_br, (px, 96, pz+46))
add_node("传感器L支架_竖板", add_mesh("m_br2", *box(30, 48, 4)), m_br, (px, 70, pz+47))
for ox_, nm in [(-12, "左"), (12, "右")]:
    add_node(f"L支架_M3孔_{nm}", add_mesh("m_bh"+nm, *cylinder(1.8, 1.8, 1.2, 10)), m_hole, (px+ox_, 98.2, pz+46))
add_node("土壤传感器板", add_mesh("m_sen", *box(22, 30, 3)), add_material("mat_sen", C["sensor"]), (px, 74, pz+44))
add_node("传感器_顶部插针", add_mesh("m_sh2", *box(18, 3, 4)), add_material("mat_hdr2", C["header"]), (px, 90.5, pz+44))
for k, ox_ in enumerate([-6, 6]):
    add_node(f"传感器探针{k+1}", add_mesh(f"m_pr{k}", *box(2.5, 26, 1.5)), add_material("mat_pr", C["probe"]), (px+ox_, 79, pz+44))

# 9. OLED 45° 斜面支架 P1-4（左前，屏朝观众）
ox,oz = -95, -62
add_node("OLED底座_P1-4", add_mesh("m_ob", *box(70, 12, 50)), add_material("mat_ob", C["oled_stand"]), (ox, 6, oz))
qx45 = (-math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5))
add_node("OLED托板_45度", add_mesh("m_ot", *box(56, 3, 42)), add_material("mat_ot", C["oled_stand"]), (ox, 30, oz+4), q=qx45)
add_node("OLED屏", add_mesh("m_os", *box(46, 2, 34)), add_material("mat_os", C["oled_screen"]), (ox, 32.6, oz+2.4), q=qx45)
add_node("OLED托板_背撑", add_mesh("m_og", *box(50, 3, 26)), add_material("mat_og", C["oled_stand"]), (ox, 14, oz-12), q=(-math.sqrt(0.5),0,0,math.sqrt(0.5)))

# 10. 走线（全链避让：穿盆沿上方/绕开植物/避开其他线束）
m_w = {k: add_material("mw_"+k, v) for k, v in
       [("red",C["w_red"]),("blk",C["w_blk"]),("ylw",C["w_ylw"]),("blu",C["w_blu"]),("brn",C["w_brn"])]}
wr = P["wire_r"]
# 10a. 传感器->ESP32 ×3：越沿上高点(104) -> 高空左行(过盆沿上方) -> 落板前端
for i_, (col, off) in enumerate([("red",-8),("ylw",0),("blk",8)]):
    a = (px+off, 92, pz+44); b = (px+off, 104, pz+44)
    c = (-30+off, 104, 55); dd = (-30+off, 8, 40)
    nm = ["红","黄","黑"][i_]
    tube_between(f"线_传感器{nm}_越沿", a, b, wr, m_w[col])
    tube_between(f"线_传感器{nm}_后行", b, c, wr, m_w[col])
    tube_between(f"线_传感器{nm}_入板", c, dd, wr, m_w[col])
# 10b. OLED->ESP32 ×4：出座前沿 -> 底板走廊 -> 斜上板前端
for i_, (col, off) in enumerate([("red",-9),("blk",-3),("ylw",3),("blu",9)]):
    a = (ox+off, 3, -30); b = (ox+off, 2.5, 25); c = (-40+off, 8, 55)
    nm = ["红","黑","黄","蓝"][i_]
    tube_between(f"线_OLED{nm}_出座", a, b, wr, m_w[col])
    tube_between(f"线_OLED{nm}_上板", b, c, wr, m_w[col])
# 10c. 水泵->ESP32 ×2：箱内出顶(线孔) -> 高空过顶 -> 板后端下行入板
for i_, (col, off) in enumerate([("blu",-2.5),("brn",2.5)]):
    a = (tx+off, 31, tz); b = (tx+off, 114, tz)
    c = (5+off, 114, tz); dd = (5+off, 4, -78); e = (-8+off, 8, -78)
    nm = ["蓝","棕"][i_]
    tube_between(f"线_水泵{nm}_出箱", a, b, wr, m_w[col])
    tube_between(f"线_水泵{nm}_过顶", b, c, wr, m_w[col])
    tube_between(f"线_水泵{nm}_下行", c, dd, wr, m_w[col])
    tube_between(f"线_水泵{nm}_入板", dd, e, wr, m_w[col])

# ---------- 导出 GLB ----------
gltf = {
    "asset": {"version": "2.0", "generator": "greenhouse-param-builder-v3.3"},
    "scene": 0, "scenes": [{"name": "GreenHouse Final Project", "nodes": list(range(len(nodes)))}],
    "nodes": nodes, "meshes": meshes, "materials": materials,
    "buffers": [{"byteLength": len(buf)}], "bufferViews": bufferViews, "accessors": accessors,
}
json_data = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
while len(json_data) % 4: json_data += b"\x20"
bin_pad = (4 - len(buf) % 4) % 4
total = 12 + 8 + len(json_data) + 8 + len(buf) + bin_pad
out = struct.pack("<III", 0x46546C67, 2, total)
out += struct.pack("<II", len(json_data), 0x4E4F534A) + json_data
out += struct.pack("<II", len(buf) + bin_pad, 0x004E4942) + bytes(buf) + b"\x00"*bin_pad
fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "花房系统概念模型_v3_参数化.glb")
with open(fname, "wb") as f: f.write(out)
print(f"OK -> {fname}")
print(f"GLB {total} bytes | nodes {len(nodes)} | meshes {len(meshes)} | materials {len(materials)}")
