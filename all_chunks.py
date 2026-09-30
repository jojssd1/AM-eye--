# -*- coding: utf-8 -*-
"""下载 Web UI 全部 webpack chunk，并搜索测温规则读写接口。"""
import os
import re
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "chunks")
os.makedirs(OUT, exist_ok=True)
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

# 1) 拿 runtime 里的 hash 映射
rt = S.get(BASE + "/doc/root-runtime.61a9d28e7c54955dde5c.js", timeout=20).text
m = re.search(r"\{1:\"[0-9a-f]{20}\".*?\}", rt)
mapping = dict(re.findall(r"(\d+):\"([0-9a-f]{20})\"", m.group(0)))
print(f"chunk 映射数量: {len(mapping)}")

# 2) 下载
ok = 0
for cid, h in sorted(mapping.items(), key=lambda x: int(x[0])):
    url = f"{BASE}/doc/js/{cid}_chunk.{h}.js"
    dst = os.path.join(OUT, f"{cid}_chunk.js")
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        ok += 1
        continue
    try:
        r = S.get(url, timeout=25)
        if r.status_code == 200:
            with open(dst, "wb") as f:
                f.write(r.content)
            ok += 1
    except Exception:
        pass
print(f"已下载 {ok}/{len(mapping)} 个 chunk，总计 "
      f"{sum(os.path.getsize(os.path.join(OUT,f)) for f in os.listdir(OUT))} 字节")

# 3) 搜索规则接口
print("\n" + "=" * 78)
print("搜索测温规则相关 API")
for kw in ["thermometry/rules", "ThermometryScene", "ThermometryRegion",
           "deleteThermometry", "setThermometryRule", "rules/1"]:
    print(f"\n### {kw}")
    hits = 0
    for fn in sorted(os.listdir(OUT)):
        txt = open(os.path.join(OUT, fn), "rb").read().decode("utf-8", "replace")
        for mm in re.finditer(re.escape(kw), txt):
            hits += 1
            if hits > 4:
                break
            a, b = max(0, mm.start() - 280), min(len(txt), mm.end() + 280)
            print(f"-- {fn} @{mm.start()}\n   {txt[a:b]}".replace("\n", " ")[:620])
        if hits > 4:
            break
    if hits == 0:
        print("   (未找到)")
