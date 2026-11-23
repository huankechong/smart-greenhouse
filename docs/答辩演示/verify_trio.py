# -*- coding: utf-8 -*-
"""
三件套同源同版校验：HTML / PDF / PPTX 的关键数字必须一致。

PDF 文字用字体子集 + <hex> 字符串存储，必须经 ToUnicode CMap 解码才能拿到真实文本，
否则裸字节搜索会误匹配（'857' 在二进制里会撞上随机序列）。

回应 PR #52 评审第 3 条「HTML/PDF/PPTX 数字不一致」。
"""
import re
import sys
import zlib
from pathlib import Path

DECK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("deck").resolve()

MUST_PRESENT = ["1855", "857", "15%", "998", "68 h", "14.93"]
OLD_VALUES = {"2372": 1, "1050": 1}
FORBIDDEN = ["35%", "5 s 触发", "8/10", "48 h 运行中"]


def html_text(p):
    h = p.read_text(encoding="utf-8")
    body = re.sub(r"<div class=\"notes\">.*?</div>", "", h, flags=re.S)
    body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", body)


def _pdf_objects(d):
    """返回 {objnum: 解压后的流内容}。"""
    objs = {}
    for m in re.finditer(rb"(\d+)\s+0\s+obj(.*?)endobj", d, re.S):
        num = int(m.group(1))
        body = m.group(2)
        sm = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
        if sm:
            raw = sm.group(1)
            try:
                raw = zlib.decompress(raw)
            except Exception:
                pass
            objs[num] = (body[:sm.start()], raw)
    return objs


def _parse_tounicode(data):
    """解析 ToUnicode CMap，返回 {code:int -> str}。"""
    cmap = {}
    txt = data.decode("latin-1", "ignore")
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", txt, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            try:
                cmap[int(src, 16)] = bytes.fromhex(dst).decode("utf-16-be", "ignore")
            except Exception:
                pass
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", txt, re.S):
        for lo, hi, dst in re.findall(
                r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            try:
                a, b = int(lo, 16), int(hi, 16)
                base = int(dst, 16)
                for i in range(a, b + 1):
                    cmap[i] = chr(base + (i - a))
            except Exception:
                pass
    return cmap


def pdf_text(p):
    """用 pypdfium2 提取 PDF 文字。

    自写的 ToUnicode CMap 解析器对部分字体子集解码不全，会把正常数字误判为缺失
    （实测 998 被读成乱码，页面渲染其实完全正常）——一律改用 PDFium 官方实现。
    """
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(p))
    chunks = []
    for i in range(len(doc)):
        tp = doc[i].get_textpage()
        chunks.append(tp.get_text_range())
    return "\n".join(chunks)


def pptx_text(p):
    from pptx import Presentation
    prs = Presentation(str(p))
    chunks = []
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame:
                chunks.append(sh.text_frame.text)
    return "\n".join(chunks)


def _norm(t):
    """PDF 文字按字形逐字输出（'1 8 5 5'），比对前先去掉所有空白。"""
    return re.sub(r"\s+", "", t)


def _count(t, k):
    return _norm(t).count(_norm(k))


def main():
    h = html_text(DECK / "index.html")
    pdf = pdf_text(DECK / "deck.pdf")
    ppt = pptx_text(DECK / "deck.pptx")
    print(f"[提取长度] HTML={len(h)}  PDF={len(pdf)}  PPTX={len(ppt)}")

    ok = True
    print("\n【1】现行关键数字必须三件套齐全")
    for k in MUST_PRESENT:
        hn, pn, tn = _count(h, k), _count(pdf, k), _count(ppt, k)
        good = hn > 0 and pn > 0 and tn > 0
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {k:8s}  HTML={hn:3d}  PDF={pn:3d}  PPTX={tn:3d}")

    print("\n【2】旧值只允许出现在标注过的纠错语境")
    for k, allowed in OLD_VALUES.items():
        hn = _count(h, k)
        good = hn <= allowed
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {k:8s}  HTML={hn:3d} (允许 ≤{allowed})")
        for m in re.finditer(re.escape(k), h):
            seg = re.sub(r"\s+", " ", h[max(0, m.start() - 60):m.start() + 40])
            marked = any(w in seg for w in ("旧值", "已废弃", "已修正"))
            print(f"       {'标注✓' if marked else '未标注✗'} ...{seg}...")
            ok &= marked

    print("\n【3】应已消失的旧口径")
    for k in FORBIDDEN:
        hn, pn, tn = _count(h, k), _count(pdf, k), _count(ppt, k)
        good = hn == 0 and tn == 0
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {k:14s}  HTML={hn}  PDF={pn}  PPTX={tn}")

    print("\n【4】页数一致")
    d = (DECK / "deck.pdf").read_bytes()
    pages_pdf = len(re.findall(rb"/Type\s*/Page[^s]", d))
    from pptx import Presentation
    pages_ppt = len(Presentation(str(DECK / "deck.pptx")).slides)
    pages_html = len(re.findall(r'<section class="slide"', (DECK / "index.html").read_text(encoding="utf-8")))
    good = pages_html == pages_pdf == pages_ppt == 18
    ok &= good
    print(f"  {'OK ' if good else 'FAIL'} HTML={pages_html}  PDF={pages_pdf}  PPTX={pages_ppt}  (应均为 18)")

    print("\n" + "=" * 64)
    print(f"结论：{'✅ 三件套同源同版，数字一致' if ok else '❌ 存在不一致，需修正'}")
    print("=" * 64)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
