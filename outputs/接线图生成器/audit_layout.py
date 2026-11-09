# -*- coding: utf-8 -*-
"""接线图 SVG 布局三查：文字重叠 / 线穿裸文字 / 越界。用法: python audit_layout.py [html路径]"""
import re, sys, math, unicodedata

path = sys.argv[1] if len(sys.argv) > 1 else "docs/操作手册/花房接线图_整机总图.html"
html = open(path, encoding="utf-8").read()
m = re.search(r'<svg[^>]*viewBox="0 0 (\d+) (\d+)"[^>]*>(.*)</svg>', html, re.S)
if not m:
    print("!! 未找到 SVG"); sys.exit(1)
W, H = float(m.group(1)), float(m.group(2))
body = m.group(3)

texts = []
for tm in re.finditer(r'<text\b([^>]*)>(.*?)</text>', body, re.S):
    attrs, content = tm.group(1), tm.group(2)
    content = re.sub(r'<[^>]+>', '', content)
    content = content.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"')
    def attr(name, default=None):
        am = re.search(name + r'="([-\w.]+)"', attrs)
        return am.group(1) if am else default
    x = float(attr('x')) if attr('x') else None
    y = float(attr('y')) if attr('y') else None
    fs = float(attr('font-size', '12'))
    anchor = attr('text-anchor', 'start')
    exempt = 'paint-order' in attrs and 'stroke' in attrs
    texts.append(dict(x=x, y=y, fs=fs, anchor=anchor, content=content, exempt=exempt))

def text_width(t):
    return sum(t['fs'] if unicodedata.east_asian_width(c) in ('W','F') else t['fs']*0.62
               for c in t['content'])

def bbox(t):
    if t['x'] is None or t['y'] is None: return None
    w = text_width(t)
    x0 = t['x'] if t['anchor']=='start' else (t['x']-w/2 if t['anchor']=='middle' else t['x']-w)
    return (x0, t['y']-0.75*t['fs'], x0+w, t['y']+0.25*t['fs'])

issues = []
# 查1：裸文字两两重叠
for i in range(len(texts)):
    for j in range(i+1, len(texts)):
        a, b = texts[i], texts[j]
        if a['exempt'] or b['exempt']: continue
        ba, bb = bbox(a), bbox(b)
        if not ba or not bb: continue
        ox = min(ba[2],bb[2]) - max(ba[0],bb[0])
        oy = min(ba[3],bb[3]) - max(ba[1],bb[1])
        if ox > 1.5 and oy > 1.5:
            issues.append(f"[文字重叠] '{a['content'][:14]}' @({a['x']:.0f},{a['y']:.0f}) <-> '{b['content'][:14]}' @({b['x']:.0f},{b['y']:.0f}) {ox:.1f}x{oy:.1f}px")

paths = []
for pm in re.finditer(r'<path\b([^>]*)/?>', body):
    attrs = pm.group(1)
    dm = re.search(r'\bd="([^"]+)"', attrs)
    if not dm: continue
    nums = re.findall(r'[-\d.]+', dm.group(1))
    pts = [(float(nums[k]), float(nums[k+1])) for k in range(0, len(nums)-1, 2)]
    if ('stroke' in attrs) and ('fill="' not in attrs or 'fill="none"' in attrs) and len(pts) >= 2:
        paths.append(pts)

def seg_hits_bbox(p1, p2, bb):
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    steps = max(2, int(math.hypot(dx, dy)/3))
    for s in range(steps+1):
        t = s/steps
        if bb[0] < p1[0]+dx*t < bb[2] and bb[1] < p1[1]+dy*t < bb[3]:
            return True
    return False

# 查2：线穿裸文字
for pts in paths:
    for t in texts:
        if t['exempt']: continue
        bb = bbox(t)
        if not bb or not t['content']: continue
        for k in range(len(pts)-1):
            if seg_hits_bbox(pts[k], pts[k+1], bb):
                issues.append(f"[线穿裸文字] '{t['content'][:14]}' @({t['x']:.0f},{t['y']:.0f}) 被 {pts[k]}->{pts[k+1]} 穿过")
                break

# 查3：越界
for t in texts:
    bb = bbox(t)
    if bb and (bb[0] < 0 or bb[1] < 0 or bb[2] > W or bb[3] > H):
        issues.append(f"[文字越界] '{t['content'][:14]}' @({t['x']:.0f},{t['y']:.0f})")
for rm in re.finditer(r'<rect\b([^>]*)/?>', body):
    a = rm.group(1)
    g = lambda n: (re.search(n + r'="([-\d.]+)"', a) or [None,None])[1]
    try:
        x,y,w,h = float(g('x')), float(g('y')), float(g('width')), float(g('height'))
        if x < -2 or y < -2 or x+w > W+2 or y+h > H+2:
            issues.append(f"[rect越界] ({x:.0f},{y:.0f},{w:.0f}x{h:.0f})")
    except (TypeError, ValueError):
        pass

print(f"{path} | text {len(texts)} 线径 {len(paths)}")
if issues:
    print(f"!! 共 {len(issues)} 个问题：")
    for s in issues[:40]: print("  " + s)
    sys.exit(2)
print("✅ 布局三查全部通过：0 问题")
