# -*- coding: utf-8 -*-
"""最后一击：GET 带 body / preset 变体，读取已配置的测温规则（只读）。"""
import os
import re
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)
URL = BASE + "/ISAPI/Thermal/channels/1/thermometry/rules"

print("#" * 78)
print("# GET 携带 XML body 的尝试（只读语义，不会改设备）")
bodies = [
    ("空 ThermometryScene",
     b'<?xml version="1.0" encoding="UTF-8"?><ThermometryScene></ThermometryScene>'),
    ("带 id",
     b'<?xml version="1.0" encoding="UTF-8"?><ThermometryScene><id>1</id></ThermometryScene>'),
    ("裸空", b''),
]
for label, body in bodies:
    for params in ({}, {"preset": "0"}, {"preset": "1"}):
        try:
            r = S.request("GET", URL, data=body, params=params,
                          headers={"Content-Type": "application/xml"}, timeout=8)
            extra = r.content.decode("utf-8", "replace")
            tag = "  <== 成功!" if r.status_code == 200 else ""
            print(f"  {r.status_code}  body={label:22s} params={params}{tag}")
            print(f"        {extra[:200].replace(chr(10),' ')}")
            if r.status_code == 200:
                print(extra[:1500])
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            print(f"  !! {label} {params}: {type(e).__name__}")

print("\n" + "#" * 78)
print("# WSDK_GetDeviceConfig 的 HTTP 方法实现")
for root, _, files in os.walk(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")):
    for fn in files:
        if not fn.endswith(".js"):
            continue
        p = os.path.join(root, fn)
        t = open(p, "rb").read().decode("utf-8", "replace")
        for m in re.finditer(r'GetDeviceConfig[:=]\s*function[^}]{0,400}', t):
            print(f"-- {fn}\n   {m.group(0)[:400]}")
        for m in re.finditer(r'WSDK_GetDeviceConfig\s*[:=][^,;]{0,300}', t):
            print(f"-- {fn}\n   {m.group(0)[:300]}")
