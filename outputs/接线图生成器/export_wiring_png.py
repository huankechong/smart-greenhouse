# -*- coding: utf-8 -*-
"""
接线图 SVG → 高清 PNG 导出（R4 · S2-10.1 交付物）
================================================================
用法：python export_wiring_png.py [html路径] [输出目录]

做什么：从「花房接线图_整机总图.html」里抽出内联 SVG，用 Edge headless
      渲染成 2 倍分辨率 PNG（矢量→位图，放进报告不糊）。

为什么不用 cairosvg：装不依赖 cairo 的系统库，Windows 上坑多。
      Edge 已经装好，headless 截图零安装。

为什么不用外部字体：SVG 内联的 <text> 用的是 font-family 继承，
      这里给 SVG 根补一条显式字体栈，避免 headless 环境字体回退。
"""
import re, sys, pathlib, subprocess, shutil, os

# ---------- 浏览器定位（按优先级找） ----------
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

FONT_STACK = ("Microsoft YaHei,Microsoft YaHei UI,PingFang SC,"
              "Noto Sans CJK SC,Source Han Sans SC,SimHei,sans-serif")

# ---------- 缩放档 ----------
SCALES = {
    "2x": 2,
    "3x": 3,
    "4x": 4,
}


def find_browser():
    for p in BROWSERS:
        if pathlib.Path(p).exists():
            return p
    return None


def extract_svg(html_path):
    """从 HTML 里抽出第一个带 viewBox 的内联 SVG，补上字体栈与尺寸。"""
    html = pathlib.Path(html_path).read_text(encoding="utf-8")
    m = re.search(r'(<svg\b[^>]*viewBox="0 0 (\d+) (\d+)"[^>]*>.*?</svg>)', html, re.S)
    if not m:
        raise SystemExit("!! HTML 里没找到带 viewBox 的内联 SVG")
    svg = m.group(1)
    w, h = int(m.group(2)), int(m.group(3))

    # 给根 <svg> 补 font-family，让 headless 渲染时中文字形正确
    if "font-family" not in svg.split(">", 2)[1]:
        svg = svg.replace(
            "<svg ",
            f'<svg font-family="{FONT_STACK}" ', 1)

    return svg, w, h


def wrap_html(svg, w, h, scale):
    """包一个最小 HTML 供 headless 截图（去掉 body 边距，白底）。"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#fff}}
svg{{display:block;width:{w}px;height:{h}px}}
</style></head>
<body>{svg}</body></html>"""


def render(png_out, svg, w, h, scale, browser, full_page=False):
    """用 Edge headless 截图。
    full_page=False → 只截 SVG 本体（纯图，适合插报告）
    full_page=True  → 截整个 HTML（含标题/逐线清单/核对表，适合当附录页）
    """
    if full_page:
        # 直接截原 HTML，窗口给足高度让整页都进画面
        src = pathlib.Path(html_src).resolve()
        tmp_html = None
        win_h = 4200
    else:
        tmp_html = png_out.with_suffix(".tmp.html")
        tmp_html.write_text(wrap_html(svg, w, h, scale), encoding="utf-8")
        src = tmp_html.resolve()
        win_h = h

    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--default-background-color=FFFFFFFF",
        f"--force-device-scale-factor={scale}",
        f"--window-size={w},{win_h}",
        f"--screenshot={png_out.resolve()}",
        src.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if tmp_html:
        tmp_html.unlink(missing_ok=True)

    if not png_out.exists():
        print(r.stdout[-800:])
        print(r.stderr[-800:])
        raise SystemExit(f"!! 渲染失败：{png_out.name}")
    return png_out


def png_size(p):
    """读 PNG 头部拿真实像素尺寸（校验用）。"""
    d = p.read_bytes()[:33]
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return (int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big"))


def trim_bottom(p, margin=24):
    """裁掉 PNG 底部纯白空白，避免出一张下半截是空的图。
    需要 Pillow；没装就原样返回（不报错）。"""
    try:
        from PIL import Image
    except ImportError:
        print("   (未装 Pillow，跳过裁白)")
        return png_size(p)
    im = Image.open(p).convert("RGB")
    w, h = im.size
    px = im.load()
    last = 0
    for y in range(h - 1, -1, -1):
        hit = False
        for x in range(0, w, 7):
            r, g, b = px[x, y]
            if r < 245 or g < 245 or b < 245:
                hit = True
                break
        if hit:
            last = y
            break
    new_h = min(h, last + 1 + margin)
    if new_h < h:
        im.crop((0, 0, w, new_h)).save(p)
        print(f"   已裁掉底部空白 {h - new_h}px → {new_h}px")
    return png_size(p)


def main():
    global html_src
    html_src = sys.argv[1] if len(sys.argv) > 1 else "docs/操作手册/花房接线图_整机总图.html"
    outdir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/接线图生成器/导出PNG")
    scale_key = sys.argv[3] if len(sys.argv) > 3 else "3x"
    scale = SCALES.get(scale_key, 3)

    browser = find_browser()
    if not browser:
        raise SystemExit("!! 没找到 Edge/Chrome，无法渲染")
    print(f"浏览器: {browser}")

    svg, w, h = extract_svg(html_src)
    print(f"SVG: viewBox 0 0 {w} {h}，{len(svg)} 字符")

    outdir.mkdir(parents=True, exist_ok=True)
    stem = pathlib.Path(html_src).stem

    # ① 纯图版：只有接线图本体，3 倍分辨率 —— 报告正文插图用
    out_svg = outdir / f"{stem}_接线图.png"
    render(out_svg, svg, w, h, scale, browser)
    s = png_size(out_svg)
    print(f"✅ {out_svg.name}  {s[0]}x{s[1]} px  {out_svg.stat().st_size/1024:.0f} KB  (scale {scale}x)")

    # ② 整页版：含标题+逐线清单+端口表+核对表 —— 报告附录/答辩手页用
    out_page = outdir / f"{stem}_接线图_附清单.png"
    render(out_page, svg, w, h, 2, browser, full_page=True)
    s2 = trim_bottom(out_page)
    print(f"✅ {out_page.name}  {s2[0]}x{s2[1]} px  {out_page.stat().st_size/1024:.0f} KB  (scale 2x, 含清单表)")


if __name__ == "__main__":
    main()
