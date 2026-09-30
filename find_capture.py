# -*- coding: utf-8 -*-
"""定位 Web UI 真正抓取逐像素温度的函数，并实测候选抓取端点。"""
import os
import re
import sys
import time

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
WEBUI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "webui")
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

# ---------- A. JS 上下文搜索 ----------
KEYS = ["bSupportCaptureThermal", "CaptureThermal", "AppendData", "thermalCapture"]
print("#" * 78)
print("# A. JS 中抓图相关逻辑")
for kw in KEYS:
    print(f"\n### {kw}")
    n = 0
    for fn in sorted(os.listdir(WEBUI)):
        if not fn.endswith(".js"):
            continue
        txt = open(os.path.join(WEBUI, fn), "rb").read().decode("utf-8", errors="replace")
        for m in re.finditer(re.escape(kw), txt):
            n += 1
            if n > 4:
                break
            a, b = max(0, m.start() - 300), min(len(txt), m.end() + 300)
            print(f"-- {fn} @{m.start()}\n   {txt[a:b]}".replace("\n", " ")[:700])
        if n > 4:
            break
    if n == 0:
        print("   (未找到)")

# ---------- B. 实测候选端点 ----------
print("\n" + "#" * 78)
print("# B. 实测候选抓取端点")
CANDS = [
    ("GET",  "/ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData"),
    ("POST", "/ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData"),
    ("GET",  "/ISAPI/Thermal/channels/1/thermometry/JpegPictureWithAppendData"),
    ("GET",  "/ISAPI/Thermal/channels/1/thermometry/pictureWithAppendData"),
    ("GET",  "/ISAPI/Thermal/channels/1/thermometry/pixelToPixelData"),
    ("POST", "/ISAPI/Thermal/channels/1/thermometry/pixelToPixelParam"),
    ("GET",  "/ISAPI/Streaming/channels/101/picture"),
    ("GET",  "/ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData?format=json"),
]
for method, p in CANDS:
    t0 = time.time()
    try:
        r = S.request(method, BASE + p, timeout=6)
        ct = r.headers.get("Content-Type", "")
        print(f"  {method:4s} {p:72s} {r.status_code} {ct} {len(r.content)}B {time.time()-t0:.1f}s")
        if r.status_code == 200:
            with open(os.path.join(WEBUI, "..", "capture_" + re.sub(r"\W+", "_", p)[-50:]), "wb") as f:
                f.write(r.content)
            head = r.content[:120]
            print(f"        头字节: {head[:80]!r}")
    except Exception as e:
        print(f"  {method:4s} {p:72s} !! {type(e).__name__} ({time.time()-t0:.1f}s)")
