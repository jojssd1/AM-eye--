# -*- coding: utf-8 -*-
"""逐个探测 ISAPI 端点，含超时与耗时统计，避免单点卡死整个流程。"""
import json
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

# (名称, 路径, 打印上限)
ENDPOINTS = [
    ("deviceInfo",       "/ISAPI/System/deviceInfo?format=json", 3000),
    ("thermal_caps",     "/ISAPI/Thermal/capabilities?format=json", 3000),
    ("sys_caps",         "/ISAPI/System/capabilities?format=json", 1500),
    ("streaming",        "/ISAPI/Streaming/channels?format=json", 3000),
    ("thermal_ch1",      "/ISAPI/Thermal/channels/1/thermometry?format=json", 1200),
    ("thermal_ch2",      "/ISAPI/Thermal/channels/2/thermometry?format=json", 1200),
    ("rules_ch1",        "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules?format=json", 2000),
    ("rules_ch2",        "/ISAPI/Thermal/channels/2/thermometry/realTimethermometry/rules?format=json", 2000),
    ("palettes_ch1",     "/ISAPI/Image/channels/1/Palettes?format=json", 1500),
    ("palettes_ch2",     "/ISAPI/Image/channels/2/Palettes?format=json", 1500),
    ("tempRange_ch2",    "/ISAPI/Thermal/channels/2/thermometry/tempRangeParam?format=json", 800),
    ("video_ch1",        "/ISAPI/Streaming/channels/101?format=json", 1500),
]


def probe(name, path, limit, timeout=15):
    print("\n" + "=" * 78, flush=True)
    print(f"[{name}]  GET {path}", flush=True)
    t0 = time.time()
    try:
        r = S.get(BASE + path, timeout=timeout)
    except Exception as e:
        print(f"  !! {type(e).__name__}: {e}   ({time.time()-t0:.1f}s)", flush=True)
        return None

    dt = time.time() - t0
    ct = r.headers.get("Content-Type", "")
    print(f"  -> HTTP {r.status_code} | {ct} | {len(r.content)}B | {dt:.2f}s", flush=True)

    with open(os.path.join(OUT, f"{name}.raw"), "wb") as f:
        f.write(r.content)

    text = r.content.decode("utf-8", errors="replace")
    if "json" in ct.lower() or "format=json" in path:
        try:
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            print(pretty[:limit], flush=True)
            if len(pretty) > limit:
                print(f"  ... [+{len(pretty)-limit} chars -> out/{name}.raw]", flush=True)
            return parsed
        except Exception:
            pass
    print(text[:limit], flush=True)
    return None


if __name__ == "__main__":
    ok, bad = [], []
    for name, path, limit in ENDPOINTS:
        r = probe(name, path, limit)
        (ok if r is not None else bad).append(name)
    print("\n" + "=" * 78, flush=True)
    print("OK  :", ", ".join(ok), flush=True)
    print("FAIL:", ", ".join(bad) or "(none)", flush=True)
