# -*- coding: utf-8 -*-
"""抓取设备自带 Web UI 的 JS，反查它真实调用的 ISAPI 端点。"""
import os
import re
import sys

import requests
from requests.auth import HTTPDigestAuth
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "webui")
os.makedirs(OUT, exist_ok=True)

S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)


def get(path):
    try:
        r = S.get(BASE + path, timeout=30)
        return r
    except Exception as e:
        print(f"  !! {path}: {type(e).__name__}: {e}")
        return None


# 1) index.html
idx = get("/doc/index.html")
assets = set()
if idx and idx.status_code == 200:
    html = idx.text
    for m in re.finditer(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', html):
        # 相对路径必须相对 /doc/ 解析
        u = urljoin("/doc/index.html", m.group(1))
        if u.startswith("/"):
            assets.add(u)
    print(f"index.html 引用资源 {len(assets)} 个:")
    for a in sorted(assets):
        print("   ", a)

# 2) 逐个下载 JS
KEYWORDS = [
    "jpegPicWithAppendData", "realTimethermometry", "thermometry", "Thermal",
    "pixelToPixel", "Palettes", "AGC", "FFC", "shutter", "TemperatureData",
    "thermalStream", "picture", "Streaming/channels",
]

downloaded = []
for a in sorted(assets):
    if not a.split("?")[0].lower().endswith(".js"):
        continue
    r = get(a)
    if not r or r.status_code != 200:
        continue
    fn = os.path.join(OUT, os.path.basename(a.split("?")[0]))
    with open(fn, "wb") as f:
        f.write(r.content)
    downloaded.append(fn)
    print(f"\n下载 {a}  -> {len(r.content)} bytes")

# 3) 在下载的 JS 里搜 ISAPI 路径
print("\n" + "=" * 78)
print("在 JS 中找到的 ISAPI 路径")
found = {}
for fn in downloaded:
    txt = open(fn, "rb").read().decode("utf-8", errors="replace")
    for m in re.finditer(r'["\'`]([^"\'`\s]{0,80}/ISAPI/[^"\'`\s]{0,160})["\'`]', txt):
        p = m.group(1)
        found.setdefault(p, set()).add(os.path.basename(fn))
    # 也搜不带引号的拼接片段
    for m in re.finditer(r'(/ISAPI/[A-Za-z0-9_/\-]{3,120})', txt):
        p = m.group(1)
        found.setdefault(p, set()).add(os.path.basename(fn))

for p in sorted(found):
    if any(k.lower() in p.lower() for k in ("thermal", "image", "stream", "picture", "palette", "agc", "ffc", "shutter")):
        print(f"  {p}    <- {','.join(sorted(found[p]))}")

print(f"\n合计发现 {len(found)} 条 ISAPI 路径（全部写入 out/webui/endpoints.txt）")
with open(os.path.join(OUT, "endpoints.txt"), "w", encoding="utf-8") as f:
    for p in sorted(found):
        f.write(p + "\n")
