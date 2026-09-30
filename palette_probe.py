# -*- coding: utf-8 -*-
"""枚举设备实际接受的伪彩名称，并读取 DisplayMgr 能力。"""
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)
PAL = BASE + "/ISAPI/Image/channels/1/Palettes"


def get(p):
    try:
        r = S.get(BASE + p, timeout=8)
        print(f"\nGET {p} -> {r.status_code} | {len(r.content)}B")
        print(r.content.decode("utf-8", "replace")[:1800])
    except Exception as e:
        print(f"\nGET {p} !! {type(e).__name__}: {e}")


for p in ["/ISAPI/Thermal/DisplayMgr/Web/capabilities",
          "/ISAPI/Image/channels/1/DisplayParam",
          "/ISAPI/Image/channels/1/Palettes/capabilities",
          "/ISAPI/Thermal/DisplayMgr/capabilities"]:
    get(p)

# 当前值
orig = S.get(PAL, timeout=8).text
print("\n" + "=" * 78)
print(f"原始伪彩 XML: {orig.strip()}")

# 无效名称的完整报错
bad = ('<?xml version="1.0" encoding="UTF-8"?><Palettes version="2.0" '
       'xmlns="http://www.isapi.org/ver20/XMLSchema"><mode>__nope__</mode></Palettes>')
r = S.put(PAL, data=bad.encode(), headers={"Content-Type": "application/xml"}, timeout=8)
print(f"\n无效名称 PUT -> {r.status_code}\n{r.content.decode('utf-8','replace')}")

CANDIDATES = """WhiteHot Whitehot whiteHot whitehot BlackHot Blackhot blackHot blackhot
Rainbow rainbow Rainbow1 rainbow1 Ironbow IronBow ironbow iron Iron
Fusion Fusion1 Fusion2 Fusion3 fusion RedHot redHot Redhot redhot
GreenHot BlueHot Rain rain Sepia sepia Gray gray Grey grey
Medical medical Arctic arctic Lava lava HotIron hotIron HotMetal
Magma magma Inferno inferno Turbo turbo Jet jet
Red Green Blue red green blue White Black white black
Amber amber Purple purple Glory glory Emerald emerald
Sky sky Ocean ocean Fire fire Ice ice
RainbowFusion rainbowfusion Iron1 Iron2 Iron3
WhiteHot1 WhiteHot2 BlackHot1 Red1 Green1 Blue1
Stone stone Rainbow2 rainbow2""".split()

print("\n" + "=" * 78)
print("可用伪彩名称枚举")
ok = []
for name in CANDIDATES:
    body = ('<?xml version="1.0" encoding="UTF-8"?><Palettes version="2.0" '
            f'xmlns="http://www.isapi.org/ver20/XMLSchema"><mode>{name}</mode></Palettes>')
    try:
        r = S.put(PAL, data=body.encode(), headers={"Content-Type": "application/xml"}, timeout=6)
        if r.status_code == 200:
            ok.append(name)
            print(f"  [OK]   {name}")
    except Exception:
        pass

# 还原
S.put(PAL, data=orig.encode(), headers={"Content-Type": "application/xml"}, timeout=8)
now = S.get(PAL, timeout=8).text
print(f"\n可用伪彩({len(ok)}): {ok}")
print(f"已还原，当前值: {now.strip()[-40:]}")
