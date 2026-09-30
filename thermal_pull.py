# -*- coding: utf-8 -*-
"""抓取热像仪逐像素温度数据 + 实时测温规则，并解析 multipart 结构。"""
import os
import re
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


def hexdump(data, offset=0, width=16, maxbytes=640):
    lines = []
    for i in range(0, min(len(data), maxbytes), width):
        chunk = data[i:i + width]
        hx = " ".join(f"{b:02x}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset+i:08x}  {hx:<{width*3}}  |{asc}|")
    return "\n".join(lines)


# ---------- 1. 逐像素温度 + JPEG ----------
def pull_matrix():
    print("=" * 78)
    print("[1] jpegPicWithAppendData  (逐像素温度矩阵)")
    url = f"{BASE}/ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData"
    t0 = time.time()
    try:
        r = S.get(url, timeout=20)
    except Exception as e:
        print(f"  !! {type(e).__name__}: {e}")
        return None
    print(f"  HTTP {r.status_code} | {r.headers.get('Content-Type')} | {len(r.content)}B | {time.time()-t0:.2f}s")
    if r.status_code != 200:
        print("  " + r.content[:300].decode("utf-8", errors="replace"))
        return None
    path = os.path.join(OUT, "thermal_raw.bin")
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"  已保存 -> out/thermal_raw.bin ({len(r.content)} bytes)")
    print("  --- 头部 hexdump ---")
    print(hexdump(r.content, maxbytes=512))
    # 找出 JPEG SOI 位置
    soi = [m.start() for m in re.finditer(b"\xff\xd8\xff", r.content)]
    print(f"  JPEG SOI(FFD8FF) 偏移: {soi[:10]}")
    return r.content


# ---------- 2. 其它热成像端点试探 ----------
def probe_more():
    print("\n" + "=" * 78)
    print("[2] 其它候选端点")
    paths = [
        "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry",
        "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules",
        "/ISAPI/Thermal/channels/1/thermometry/rules",
        "/ISAPI/Thermal/channels/1/thermometry/rules/capabilities",
        "/ISAPI/Thermal/channels/1/thermometry/capabilities",
        "/ISAPI/Thermal/channels/1/thermometry/temperatureData",
        "/ISAPI/Image/channels/1/Palettes/capabilities",
        "/ISAPI/Image/channels/1/AGC/capabilities",
        "/ISAPI/Thermal/channels/1/thermometry/thermometryMode/capabilities",
        "/ISAPI/Thermal/channels/1/thermometry/tempRangeParam/capabilities",
        "/ISAPI/Thermal/channels/1/thermometry/expertParam",
        "/ISAPI/Thermal/channels/1/thermometry/environmentTemperatureMonitorParam",
        "/ISAPI/Thermal/channels/1/thermometry/thermometryShieldMask",
        "/ISAPI/System/Video/inputs/channels",
    ]
    for p in paths:
        for method in ("GET", "POST"):
            try:
                r = S.request(method, BASE + p, timeout=6)
                tag = f"{r.status_code}"
                extra = ""
                if r.status_code == 200:
                    extra = " <== OK"
                    with open(os.path.join(OUT, "p_" + re.sub(r"\W+", "_", p)[-60:] + f"_{method}.xml"), "wb") as f:
                        f.write(r.content)
                print(f"  {method:4s} {p:66s} {tag}{extra}")
                if r.status_code == 200:
                    body = r.content[:300].decode("utf-8", errors="replace").replace("\n", " ")
                    print(f"        {body}")
            except Exception as e:
                print(f"  {method:4s} {p:66s} !! {type(e).__name__}")


if __name__ == "__main__":
    pull_matrix()
    probe_more()
