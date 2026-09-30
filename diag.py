# -*- coding: utf-8 -*-
"""定位 format=json 是否为 403 的原因，并确认哪些端点会挂起。"""
import sys
import time

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

TESTS = [
    ("deviceInfo  无format", "/ISAPI/System/deviceInfo"),
    ("deviceInfo  format=json", "/ISAPI/System/deviceInfo?format=json"),
    ("deviceInfo  format=xml", "/ISAPI/System/deviceInfo?format=xml"),
    ("thermal_caps 无format", "/ISAPI/Thermal/capabilities"),
    ("thermal_caps format=json", "/ISAPI/Thermal/capabilities?format=json"),
    ("sys_caps   无format", "/ISAPI/System/capabilities"),
    ("streaming  无format", "/ISAPI/Streaming/channels"),
    ("rules_ch1  无format(3s)", "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules"),
]

for label, path in TESTS:
    t0 = time.time()
    try:
        r = S.get(BASE + path, timeout=3)
        dt = time.time() - t0
        ct = r.headers.get("Content-Type", "")
        snippet = r.content[:160].decode("utf-8", errors="replace").replace("\n", " ")
        print(f"[{label}]\n  {r.status_code} | {ct} | {len(r.content)}B | {dt:.2f}s\n  {snippet}\n", flush=True)
    except Exception as e:
        print(f"[{label}]\n  !! {type(e).__name__}: {e} ({time.time()-t0:.2f}s)\n", flush=True)
