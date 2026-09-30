# -*- coding: utf-8 -*-
"""实测：规则读取、控制写入、CORS、浏览器可用视频流。"""
import json
import socket
import sys
import time

import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）
AU = HTTPDigestAuth(CAM_USER, CAM_PWD)
S = requests.Session()
S.auth = AU

print("#" * 78)
print("# 1. 规则测温值读取（多种路径/参数）")
RULE_PATHS = [
    "/ISAPI/Thermal/channels/1/thermometry/rules",
    "/ISAPI/Thermal/channels/1/thermometry/rules?format=json",
    "/ISAPI/Thermal/channels/1/thermometry/rules/1",
    "/ISAPI/Thermal/channels/1/thermometry/rules/1?format=json",
    "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules?format=json",
    "/ISAPI/Thermal/channels/1/thermometryMode",
    "/ISAPI/Thermal/channels/1/thermometryMode?format=json",
    "/ISAPI/Thermal/channels/1/thermometry/tempRangeParam?format=json",
    "/ISAPI/Thermal/channels/1/thermometry/thermometryShieldMask?format=json",
]
for p in RULE_PATHS:
    try:
        r = S.get(BASE + p, timeout=6)
        body = r.content.decode("utf-8", "replace").replace("\n", " ")
        print(f"  {r.status_code}  {p}")
        print(f"        {body[:220]}")
    except Exception as e:
        print(f"  !! {p}: {type(e).__name__}")

print("\n" + "#" * 78)
print("# 2. CORS 检查（决定浏览器能否直连设备）")
try:
    r = S.get(BASE + "/ISAPI/System/deviceInfo", timeout=6)
    cors = {k: v for k, v in r.headers.items() if "access-control" in k.lower() or "origin" in k.lower()}
    print(f"  GET deviceInfo 响应头中 CORS 相关字段: {cors if cors else '（无）'}")
    print(f"  全部响应头: {dict(r.headers)}")
except Exception as e:
    print(f"  !! {e}")
try:
    r = S.options(BASE + "/ISAPI/System/deviceInfo", timeout=6,
                  headers={"Origin": "http://localhost:8000",
                           "Access-Control-Request-Method": "GET"})
    print(f"\n  OPTIONS 预检 -> {r.status_code}")
    print(f"  响应头: {dict(r.headers)}")
except Exception as e:
    print(f"  !! OPTIONS: {e}")

print("\n" + "#" * 78)
print("# 3. 浏览器可播放的视频/图片接口")
VID = [
    "/ISAPI/Streaming/channels/101/picture",
    "/ISAPI/Streaming/channels/102/picture",
    "/ISAPI/Streaming/channels/101/httpPreview",
    "/ISAPI/Streaming/channels/102/httpPreview",
    "/Streaming/Channels/101/httpPreview",
]
for p in VID:
    try:
        r = S.get(BASE + p, timeout=5, stream=True)
        ct = r.headers.get("Content-Type")
        print(f"  {r.status_code}  {p:48s} {ct}")
        r.close()
    except Exception as e:
        print(f"  !! {p}: {type(e).__name__}")

print("\n" + "#" * 78)
print("# 4. RTSP DESCRIBE")
def rtsp_describe(path):
    s = socket.create_connection(("192.168.1.64", 554), timeout=6)
    req = (f"DESCRIBE rtsp://192.168.1.64:554{path} RTSP/1.0\r\n"
           f"CSeq: 1\r\nAccept: application/sdp\r\nUser-Agent: probe\r\n\r\n")
    s.sendall(req.encode())
    time.sleep(0.8)
    data = s.recv(4096).decode("utf-8", "replace")
    s.close()
    return data

for path in ("/Streaming/Channels/101", "/Streaming/Channels/102"):
    try:
        d = rtsp_describe(path)
        print(f"  {path} -> {d.splitlines()[0] if d else '(空)'}")
        print("     " + d[:300].replace("\r\n", " | "))
    except Exception as e:
        print(f"  !! {path}: {type(e).__name__}: {e}")

print("\n" + "#" * 78)
print("# 5. 控制写入能力：basicParam 原值回写（无副作用往返测试）")
try:
    g = S.get(BASE + "/ISAPI/Thermal/channels/1/thermometry/basicParam", timeout=8)
    print(f"  GET  -> {g.status_code}, {len(g.content)}B")
    body = g.content
    p = S.put(BASE + "/ISAPI/Thermal/channels/1/thermometry/basicParam",
              data=body, headers={"Content-Type": "application/xml"}, timeout=10)
    print(f"  PUT  -> {p.status_code}")
    print(f"         {p.content.decode('utf-8','replace')[:200].replace(chr(10),' ')}")
    if p.status_code == 200:
        print("  ==> 写控制可用（PUT 生效）")
except Exception as e:
    print(f"  !! {type(e).__name__}: {e}")
