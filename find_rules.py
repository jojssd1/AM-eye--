# -*- coding: utf-8 -*-
"""① 从 JS 反查“读取已配置测温规则”的真实调用；② 伪彩名单补测。"""
import os
import re
import sys

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
WEBUI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "webui")
S = requests.Session()
S.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)

print("#" * 78)
print("# ① JS 中测温规则相关调用")
for kw in ["ThermometryRegion", "ThermometryScene", "RegionCoordinates", "thermometryRules", "useRules"]:
    print(f"\n### {kw}")
    n = 0
    for fn in sorted(os.listdir(WEBUI)):
        if not fn.endswith(".js"):
            continue
        txt = open(os.path.join(WEBUI, fn), "rb").read().decode("utf-8", "replace")
        for m in re.finditer(re.escape(kw), txt):
            n += 1
            if n > 3:
                break
            a, b = max(0, m.start() - 240), min(len(txt), m.end() + 240)
            print(f"-- {fn} @{m.start()}\n   {txt[a:b]}".replace("\n", " ")[:560])
        if n > 3:
            break
    if n == 0:
        print("   (未找到)")

# 在端点表里找 thermometry 下的所有子资源名
print("\n### 端点表 thermometry 相关模板")
ep = os.path.join(WEBUI, "endpoints.txt")
if os.path.exists(ep):
    for line in open(ep, encoding="utf-8"):
        if "thermometry" in line.lower():
            print("   ", line.strip())

print("\n" + "#" * 78)
print("# ② 伪彩名单补测")
PAL = BASE + "/ISAPI/Image/channels/1/Palettes"
orig = S.get(PAL, timeout=8).text
MORE = """Iron Iron1 Iron2 Ironbow1 Fusion Rainbow2 Rainbow3 Rainbow4
Amber Amber1 Glory Glory1 Purple Purple1 Magma Magma1 Inferno Inferno1
Turbo Turbo1 Jet Jet1 Lava Lava1 Medical Medical1 Arctic Arctic1
Ocean Ocean1 Fire Fire1 Ice Ice1 Sky Sky1 Stone Stone1 Emerald Emerald1
Cyan Cyan1 Pink Pink1 Violet Violet1 Gray1 Grey1 Sepia1 Rain1
RedHot1 GreenHot1 BlueHot1 WhiteHot1 BlackHot1 HotIron HotIron1
WHITEHOT BLACKHOT Bluehot Redhot Greenhot
Rrainbow Fusion3 Fusion4 FusionA FusionB""".split()
ok = []
for name in MORE:
    body = ('<?xml version="1.0" encoding="UTF-8"?><Palettes version="2.0" '
            f'xmlns="http://www.isapi.org/ver20/XMLSchema"><mode>{name}</mode></Palettes>')
    try:
        r = S.put(PAL, data=body.encode(), headers={"Content-Type": "application/xml"}, timeout=6)
        if r.status_code == 200:
            ok.append(name)
            print(f"  [OK] {name}")
    except Exception:
        pass
S.put(PAL, data=orig.encode(), headers={"Content-Type": "application/xml"}, timeout=8)
print(f"\n补测新增可用: {ok}")
print(f"当前伪彩(应还原): {'Fusion1' if 'Fusion1' in S.get(PAL, timeout=8).text else '异常!'}")
