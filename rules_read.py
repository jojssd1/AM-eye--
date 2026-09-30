# -*- coding: utf-8 -*-
"""① chunk94 是否 GET 规则资源；② 带 Content-Type 再试读取规则（只读，不写入）。"""
import os
import re
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

print("#" * 78)
print("# ① chunk 94 中 thermometryRule 的调用方式")
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "chunks", "94_chunk.js")
t = open(p, "rb").read().decode("utf-8", "replace")
print(f"chunk94 长度 {len(t)}")
for kw in ['GetDeviceConfig("thermometryRule', 'SetDeviceConfig("thermometryRule',
           'thermometryRuleCap', '"thermometryRule"']:
    hits = list(re.finditer(re.escape(kw), t))
    print(f"\n### {kw}  -> {len(hits)} 次")
    for m in hits[:3]:
        a, b = max(0, m.start() - 180), min(len(t), m.end() + 260)
        print("   " + t[a:b].replace("\n", " ")[:480])

print("\n" + "#" * 78)
print("# ② 带 Content-Type 只读尝试（不写入设备）")
paths = ["/ISAPI/Thermal/channels/1/thermometry/rules",
         "/ISAPI/Thermal/channels/1/thermometry/rules?preset=1"]
hdrs = [
    ("Content-Type: application/xml", {"Content-Type": "application/xml"}),
    ("Content-Type: application/json", {"Content-Type": "application/json"}),
    ("Accept: application/xml", {"Accept": "application/xml"}),
]
for path in paths:
    for label, h in hdrs:
        try:
            r = S.get(BASE + path, headers=h, timeout=8)
            tag = "  <== 200 OK" if r.status_code == 200 else ""
            print(f"  {r.status_code}  {label:32s} {path}{tag}")
            if r.status_code == 200:
                print(r.content.decode("utf-8", "replace")[:1200])
        except Exception as e:
            print(f"  !! {label} {path}: {type(e).__name__}")
