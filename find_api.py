# -*- coding: utf-8 -*-
"""在设备 Web UI 的 JS 中定位关键测温调用，打印上下文。"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

WEBUI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "webui")

KEYWORDS = [
    "pixelToPixelParam",
    "pixelToPixel",
    "jpegPicWithAppendData",
    "realTimethermometry",
    "ThermometryUploadList",
    "thermalDataLink",
    "clickToThermometry",
    "thermalStreamParam",
    "PictureWithAppendData",
]


def scan(kw, ctx=260):
    print("\n" + "=" * 78)
    print(f"### 关键字: {kw}")
    hits = 0
    for fn in sorted(os.listdir(WEBUI)):
        if not fn.endswith(".js"):
            continue
        txt = open(os.path.join(WEBUI, fn), "rb").read().decode("utf-8", errors="replace")
        for m in re.finditer(re.escape(kw), txt):
            hits += 1
            if hits > 6:
                break
            a = max(0, m.start() - ctx)
            b = min(len(txt), m.end() + ctx)
            print(f"\n-- {fn} @{m.start()} --")
            print(txt[a:b].replace("\n", " "))
        if hits > 6:
            break
    if hits == 0:
        print("  (未找到)")


for kw in KEYWORDS:
    scan(kw)
