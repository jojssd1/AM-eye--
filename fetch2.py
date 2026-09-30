# -*- coding: utf-8 -*-
"""抓取 pixelToPixelParam 及其能力集，定位逐像素温度数据的正确调用方式。"""
import os
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

PATHS = [
    "/ISAPI/Thermal/channels/1/thermometry/pixelToPixelParam",
    "/ISAPI/Thermal/channels/1/thermometry/pixelToPixelParam/capabilities",
    "/ISAPI/Thermal/channels/1/thermometry/basicParam/capabilities",
    "/ISAPI/Thermal/channels/1/thermometry/thermometryMode/capabilities",
    "/ISAPI/Thermal/TempHumi",
    "/ISAPI/Thermal/AlgVersion",
    "/ISAPI/Thermal/thermalDataLinkInfo",
    "/ISAPI/Thermal/thermalDataLinkStatus",
    "/ISAPI/Thermal/channels/1/clickToThermometry/initialization",
    "/ISAPI/Thermal/DisplayMgr/Web/capabilities",
    "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules/capabilities",
]

for p in PATHS:
    try:
        r = S.get(BASE + p, timeout=10)
        print("\n" + "=" * 78)
        print(f"GET {p}\n  -> {r.status_code} | {r.headers.get('Content-Type')} | {len(r.content)}B")
        body = r.content.decode("utf-8", errors="replace")
        with open(os.path.join(OUT, "q_" + p.replace("/", "_")[-70:] + ".xml"), "wb") as f:
            f.write(r.content)
        print(body[:2600])
    except Exception as e:
        print(f"\nGET {p}\n  !! {type(e).__name__}: {e}")
