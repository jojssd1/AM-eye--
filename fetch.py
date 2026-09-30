# -*- coding: utf-8 -*-
"""抓取关键 ISAPI 资源（XML），保存到 out/ 并打印。"""
import os
import sys
import time

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

# 全量抓取清单
TARGETS = [
    ("deviceInfo",        "/ISAPI/System/deviceInfo", True),
    ("thermal_caps",      "/ISAPI/Thermal/capabilities", True),
    ("sys_caps",          "/ISAPI/System/capabilities", False),
    ("streaming",         "/ISAPI/Streaming/channels", True),
]

# 对通道 1 / 2 都试探热成像与图像资源
CH_PATHS = [
    ("thermometry",            "/ISAPI/Thermal/channels/{ch}/thermometry"),
    ("thermo_basicParam",      "/ISAPI/Thermal/channels/{ch}/thermometry/basicParam"),
    ("thermo_rules",           "/ISAPI/Thermal/channels/{ch}/thermometry/rules"),
    ("thermo_realtime_rules",  "/ISAPI/Thermal/channels/{ch}/thermometry/realTimethermometry/rules"),
    ("thermo_tempRangeParam",  "/ISAPI/Thermal/channels/{ch}/thermometry/tempRangeParam"),
    ("thermo_mode",            "/ISAPI/Thermal/channels/{ch}/thermometry/thermometryMode"),
    ("thermo_expert",          "/ISAPI/Thermal/channels/{ch}/thermometry/expertParam"),
    ("image_Palettes",         "/ISAPI/Image/channels/{ch}/Palettes"),
    ("image_AGC",              "/ISAPI/Image/channels/{ch}/AGC"),
    ("image_thermalAGC",       "/ISAPI/Image/channels/{ch}/thermalAGC"),
    ("image_shutter",          "/ISAPI/Image/channels/{ch}/shutter"),
    ("image_FFC",              "/ISAPI/Image/channels/{ch}/FFC"),
    ("image_DisplayParam",     "/ISAPI/Image/channels/{ch}/DisplayParam"),
]


def fetch(name, path, show):
    t0 = time.time()
    try:
        r = S.get(BASE + path, timeout=8)
    except Exception as e:
        print(f"[{name:22s}] {path}\n    !! {type(e).__name__}: {e} ({time.time()-t0:.1f}s)", flush=True)
        return
    dt = time.time() - t0
    ok = r.status_code == 200
    print(f"[{name:22s}] HTTP {r.status_code} | {len(r.content)}B | {dt:.2f}s", flush=True)
    if r.content:
        with open(os.path.join(OUT, name + ".xml"), "wb") as f:
            f.write(r.content)
        if show:
            print("-" * 74, flush=True)
            print(r.content.decode("utf-8", errors="replace"), flush=True)
            print("-" * 74, flush=True)
        elif not ok:
            print("    " + r.content[:200].decode("utf-8", errors="replace").replace("\n", " "), flush=True)


for name, path, show in TARGETS:
    fetch(name, path, show)

for ch in (1, 2):
    print(f"\n########## CHANNEL {ch} ##########", flush=True)
    for nm, tmpl in CH_PATHS:
        fetch(f"{nm}_ch{ch}", tmpl.format(ch=ch), False)
