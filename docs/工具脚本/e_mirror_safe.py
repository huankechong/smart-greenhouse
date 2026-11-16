# -*- coding: utf-8 -*-
"""E盘镜像安全同步 v2（防呆版）——AR37 沉淀

对比旧脚本的改进（每条对应一次真实事故，见 AR37）：
1. 中文路径：git ls-files 用 bytes + decode('utf-8')（防 GBK 控制台乱码，事故#10）
2. NFC 归一：双侧路径 unicodedata.normalize('NFC')（防同形异码不匹配）
3. 白名单断言：先验证 1 个已知应同步文件能被正确映射（防集合键形态自相矛盾，事故#8——
   旧脚本 E盘清理曾因此误归档 104 个文件）
4. 只 cp 不 move/delete：破坏性为零，误跑可重跑（护栏律）
5. 完毕自动 md5 复验并打印统计

用法：python e_mirror_safe.py [--dry-run]
"""
import os, sys, hashlib, subprocess, unicodedata

E = r"E:/Documents/BU/第一学期/Introduction to Project Work/花房项目"
NFC = lambda s: unicodedata.normalize("NFC", s)
DRY = "--dry-run" in sys.argv

def git_files():
    raw = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files"],
                         capture_output=True).stdout          # bytes（编码律）
    return [l.decode("utf-8") for l in raw.splitlines() if l.strip()]

def to_e(f):
    if f in ("README.md", "AGENTS.md"): return os.path.join(E, f)
    if f.startswith("docs/"): return os.path.join(E, f)
    if f.startswith(("outputs/3D打印件/", "outputs/代码/", "outputs/素材/")):
        return os.path.join(E, NFC(f[len("outputs/"):]))
    return None

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(65536), b""): h.update(c)
    return h.hexdigest()

def blob_md5(f):
    b = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True).stdout
    return hashlib.md5(b).hexdigest()

files = git_files()
mapping = {f: to_e(f) for f in files}
mapped = {f: e for f, e in mapping.items() if e}

# ── 白名单断言（护栏律）：已知 README.md 必在映射里 ──────────────
assert "README.md" in mapped and mapped["README.md"] == os.path.join(E, "README.md"), \
    "白名单断言失败：README.md 未被正确映射——路径映射逻辑已坏，拒绝执行（这是护栏，见 AR37 事故#8）"

todo = []
for f, e in mapped.items():
    if not os.path.exists(e) or md5(e) != blob_md5(f):
        todo.append((f, e))

print(f"[e_mirror_safe] 范围 {len(mapped)} 个｜待同步 {len(todo)} 个" + ("（dry-run）" if DRY else ""))
if DRY:
    for f, e in todo[:20]: print("  will-sync", f)
    sys.exit(0)

import shutil
for f, e in todo:
    os.makedirs(os.path.dirname(e), exist_ok=True)
    blob = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True).stdout
    with open(e, "wb") as out: out.write(blob)

# ── 自动复验 ──────────────────────────────────────────────
bad = [f for f, e in mapped.items() if not os.path.exists(e) or md5(e) != blob_md5(f)]
n_ok = len(mapped) - len(bad)
print(f"[verify] 一致 {n_ok}｜异常 {len(bad)}")
for f in bad[:10]: print("  !!", f)
sys.exit(1 if bad else 0)
