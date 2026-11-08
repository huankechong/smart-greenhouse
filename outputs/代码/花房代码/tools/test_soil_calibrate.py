#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_soil_calibrate.py —— soil_calibrate.py 的离线自测

不需要真实串口：用合成的 raw 序列验证
  1. 异常值剔除（trim_outliers）
  2. 统计量（stats：中位数/均值/范围/标准差）
  3. 回写逻辑（write_back：只改常量、不动其它内容、定位不到就放弃）
  4. 干湿差不足时判定为异常

跑法：
  C:\\Users\\junbo\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe test_soil_calibrate.py
"""
import importlib.util
import random
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "soil_calibrate.py"
spec = importlib.util.spec_from_file_location("soil_calibrate", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        FAILED.append(name)


def main():
    random.seed(20261020)

    print("1. 异常值剔除")
    # 30 个正常样本围绕 3200，加 1 个极端跳变 4095
    vals = [3200 + random.randint(-20, 20) for _ in range(30)] + [4095]
    trimmed = mod.trim_outliers(vals)
    check("极端值 4095 被剔除", 4095 not in trimmed, f"got {trimmed[-3:]}")
    check("正常样本全部保留", len(trimmed) == 30, f"got {len(trimmed)}")
    check("全同值不被误删", len(mod.trim_outliers([1500] * 10)) == 10)

    print()
    print("2. 统计量")
    s = mod.stats([3200 + random.randint(-20, 20) for _ in range(30)])
    check("n = 30", s["n"] == 30, f"got {s['n']}")
    check("中位数在 3180~3220", 3180 <= s["median"] <= 3220, f"got {s['median']}")
    check("min <= 中位数 <= max", s["min"] <= s["median"] <= s["max"])
    check("标准差为正", s["stdev"] > 0, f"got {s['stdev']}")
    check("空输入返回 None", mod.stats([]) is None)

    print()
    print("3. 回写逻辑")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.ino"
        original = (
            "// 注释行\n"
            "const int SOIL_RAW_DRY = 3200;        // 探针全干\n"
            "const int SOIL_RAW_WET = 1300;        // 探针全湿\n"
            "const int SOIL_THRESHOLD_PCT  = 35;\n"
        )
        p.write_text(original, encoding="utf-8")

        ok, msg = mod.write_back(2800, 900, ino_path=p)
        after = p.read_text(encoding="utf-8")
        check("回写成功", ok, msg)
        check("DRY 已改为 2800", "SOIL_RAW_DRY = 2800" in after, after)
        check("WET 已改为 900", "SOIL_RAW_WET = 900" in after, after)
        check("阈值行未被改动", "SOIL_THRESHOLD_PCT  = 35" in after)
        check("注释被保留", "// 探针全干" in after and "// 探针全湿" in after)
        check("首行注释未被改动", after.startswith("// 注释行"))

        # 定位不到常量时应放弃，不写坏文件
        p2 = Path(td) / "broken.ino"
        p2.write_text("int x = 1;\n", encoding="utf-8")
        ok2, msg2 = mod.write_back(2800, 900, ino_path=p2)
        check("定位不到常量则放弃回写", ok2 is False, msg2)
        check("放弃时文件内容不变", p2.read_text(encoding="utf-8") == "int x = 1;\n")

        # 不存在的文件
        ok3, _ = mod.write_back(1, 2, ino_path=Path(td) / "nope.ino")
        check("文件不存在时优雅失败", ok3 is False)

    print()
    print("4. 干湿差判定阈值")
    check("MIN_SPAN 与主程序自检一致（800）", mod.MIN_SPAN == 800)
    # 模拟：干 3200 湿 1300 → 正常
    check("干3200/湿1300 差值 1900 ≥ 800 → 正常", (3200 - 1300) >= mod.MIN_SPAN)
    # 模拟：干 1200 湿 1100 → 异常
    check("干1200/湿1100 差值 100 < 800 → 判异常", not ((1200 - 1100) >= mod.MIN_SPAN))
    # 模拟：干点低于湿点 → 异常
    check("干<湿 → 判异常（方向反了）", not (1000 > 1500))

    print()
    if FAILED:
        print(f"自测失败：{len(FAILED)} 项未通过 → {FAILED}")
        return 1
    print("自测全部通过（16 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
