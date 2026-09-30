# -*- coding: utf-8 -*-
"""实测续：实时测温流、CORS、视频接口、RTSP、控制写入。"""
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
print("# 0. realTimethermometry/rules?format=json 是否为“持续推送流”")
try:
    r = S.get(BASE + "/ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules?format=json",
              stream=True, timeout=(5, 3))
    print(f"  状态 {r.status_code} | {r.headers.get('Content-Type')} | "
          f"Transfer-Encoding={r.headers.get('Transfer-Encoding')}")
    t0, total, shown = time.time(), 0, 0
    try:
        for chunk in r.iter_content(2048):
            total += len(chunk)
            if shown < 3:
                print(f"  [chunk {shown}] {chunk[:400]!r}")
                shown += 1
            if time.time() - t0 > 6:
                break
    except Exception as e:
        print(f"  流结束: {type(e).__name__}: {e}")
    print(f"  ==> 6 秒内累计收到 {total} 字节"
          f"{'（持续推送，属长连接流）' if total > 0 else '（无数据）'}")
    r.close()
except Exception as e:
    print(f"  !! {type(e).__name__}: {e}")

print("\n" + "#" * 78)
print("# 1. CORS 检查")
try:
    r = S.get(BASE + "/ISAPI/System/deviceInfo", timeout=6)
    hdr = {k: v for k, v in r.headers.items()}
    cors = {k: v for k, v in hdr.items() if "access-control" in k.lower()}
    print(f"  CORS 字段: {cors if cors else '（无，浏览器跨域直连会被拦截）'}")
    print(f"  全部响应头: {hdr}")
except Exception as e:
    print(f"  !! {e}")

print("\n" + "#" * 78)
print("# 2. 视频/图片接口（浏览器可用性）")
for p in ["/ISAPI/Streaming/channels/101/picture",
          "/ISAPI/Streaming/channels/102/picture",
          "/ISAPI/Streaming/channels/101/httpPreview",
          "/ISAPI/Streaming/channels/102/httpPreview",
          "/Streaming/Channels/101/httpPreview"]:
    try:
        r = S.get(BASE + p, timeout=5, stream=True)
        print(f"  {r.status_code}  {p:48s} {r.headers.get('Content-Type')}")
        r.close()
    except Exception as e:
        print(f"  !! {p}: {type(e).__name__}")

print("\n" + "#" * 78)
print("# 3. RTSP DESCRIBE（确认取流路径）")
def rtsp(path):
    s = socket.create_connection(("192.168.1.64", 554), timeout=6)
    s.sendall((f"DESCRIBE rtsp://192.168.1.64:554{path} RTSP/1.0\r\nCSeq: 1\r\n"
               f"Accept: application/sdp\r\nUser-Agent: probe\r\n\r\n").encode())
    time.sleep(1.0)
    try:
        d = s.recv(8192).decode("utf-8", "replace")
    except Exception as e:
        d = f"<recv err {e}>"
    s.close()
    return d

for path in ("/Streaming/Channels/101", "/Streaming/Channels/102"):
    try:
        d = rtsp(path)
        print(f"  {path}\n     {d[:260].replace(chr(13)+chr(10), ' | ')}")
    except Exception as e:
        print(f"  !! {path}: {type(e).__name__}: {e}")

print("\n" + "#" * 78)
print("# 4. 控制写入：basicParam 原值回写（无副作用）")
try:
    g = S.get(BASE + "/ISAPI/Thermal/channels/1/thermometry/basicParam", timeout=8)
    print(f"  GET -> {g.status_code}, {len(g.content)}B")
    p = S.put(BASE + "/ISAPI/Thermal/channels/1/thermometry/basicParam",
              data=g.content, headers={"Content-Type": "application/xml"}, timeout=10)
    print(f"  PUT -> {p.status_code}  {p.content.decode('utf-8','replace')[:160]!r}")
    if p.status_code == 200:
        print("  ==> 写入可用：页面可下发测温参数（发射率/距离/温度档/报警阈值）")
except Exception as e:
    print(f"  !! {type(e).__name__}: {e}")

print("\n" + "#" * 78)
print("# 5. 伪彩 / AGC / FFC 写入测试（改后立即还原）")
try:
    cur = S.get(BASE + "/ISAPI/Image/channels/1/Palettes", timeout=6).text
    print(f"  当前伪彩: {cur.strip().replace(chr(10),' ')}")
    for mode in ("WhiteHot", "Ironbow", "Rainbow", "Fusion1", "BlackHot"):
        body = (f'<?xml version="1.0" encoding="UTF-8"?>'
                f'<Palettes version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">'
                f'<mode>{mode}</mode></Palettes>')
        r = S.put(BASE + "/ISAPI/Image/channels/1/Palettes", data=body.encode(),
                  headers={"Content-Type": "application/xml"}, timeout=8)
        print(f"   PUT mode={mode:10s} -> {r.status_code}")
    # 还原
    S.put(BASE + "/ISAPI/Image/channels/1/Palettes", data=cur.encode(),
          headers={"Content-Type": "application/xml"}, timeout=8)
    print(f"  已还原为: {S.get(BASE + '/ISAPI/Image/channels/1/Palettes', timeout=6).text.strip()}")
except Exception as e:
    print(f"  !! {type(e).__name__}: {e}")
