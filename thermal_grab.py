# -*- coding: utf-8 -*-
"""
HIKMICRO HM-TD2AXXT-15C 逐像素温度数据抓取 + 解析（可直接复用）

关键结论（实测）：
  GET /ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData?format=json
  * 必须带 ?format=json，否则返回 403 invalidOperation
  * 返回 multipart/form-data，3 段：JSON 元数据 / 温度二进制 / 热成像 JPEG
  * temperatureDataLength == 4 → float32，单位已是摄氏度
"""
import json
import os
import sys

import numpy as np
import requests
from requests.auth import HTTPDigestAuth

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from cam import BASE, CAM_USER, CAM_PWD   # 设备地址与凭据统一在 cam.py（凭据走环境变量）

CH = 1
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

URL = f"{BASE}/ISAPI/Thermal/channels/{CH}/thermometry/jpegPicWithAppendData?format=json"


def parse_multipart(content: bytes, boundary: str):
    """按 boundary 切分 multipart，返回 [(headers_dict, body_bytes), ...]"""
    delim = b"--" + boundary.encode()
    parts = []
    for chunk in content.split(delim):
        if not chunk or chunk in (b"--\r\n", b"--", b"\r\n"):
            continue
        if chunk.startswith(b"--"):
            break
        if chunk.startswith(b"\r\n"):
            chunk = chunk[2:]
        head, sep, body = chunk.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = {}
        for line in head.decode("utf-8", "replace").split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        # 优先用 Content-Length 精确截断，避免破坏二进制尾部
        clen = headers.get("content-length")
        if clen and clen.isdigit():
            body = body[: int(clen)]
        else:
            body = body.rstrip(b"\r\n")
        parts.append((headers, body))
    return parts


def grab():
    r = requests.get(URL, auth=HTTPDigestAuth(CAM_USER, CAM_PWD), timeout=30)
    print(f"HTTP {r.status_code} | {r.headers.get('Content-Type')} | {len(r.content)}B")
    r.raise_for_status()

    ctype = r.headers.get("Content-Type", "")
    boundary = ctype.split("boundary=")[-1].strip().strip('"')
    print(f"boundary = {boundary!r}")

    parts = parse_multipart(r.content, boundary)
    print(f"解析出 {len(parts)} 段:")
    for i, (h, b) in enumerate(parts):
        print(f"  [{i}] {h.get('content-type')}  {len(b)} bytes")

    meta, temp_raw, jpeg = None, None, None
    for h, b in parts:
        ct = h.get("content-type", "")
        if "json" in ct:
            meta = json.loads(b.decode("utf-8"))
        elif "jpeg" in ct or "image" in ct:
            jpeg = b
        else:
            temp_raw = b
    # 兜底：按长度判断温度段
    if temp_raw is None:
        for h, b in parts:
            if meta and abs(len(b) - meta.get("temperatureDataLength", -1)) == 0:
                temp_raw = b
                break

    print("\n--- JSON 元数据 ---")
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    # 元数据被包在 JpegPictureWithAppendData 节点下
    m = meta.get("JpegPictureWithAppendData", meta)

    w = int(m["jpegPicWidth"])
    h_ = int(m["jpegPicHeight"])
    tlen = int(m["p2pDataLen"])
    bpp = int(m["temperatureDataLength"])
    print(f"\n图像 {w}x{h_}，温度数据 {tlen} 字节 → 每像素 {bpp} 字节")
    assert tlen == w * h_ * bpp, f"长度校验失败: {tlen} != {w}*{h_}*{bpp}"

    if bpp == 4:
        temp = np.frombuffer(temp_raw[: w * h_ * 4], dtype="<f4").reshape(h_, w)
        print("解码方式: float32 直接为摄氏度")
    elif bpp == 2:
        scale = float(meta.get("scale", 1))
        offset = float(meta.get("offset", 273.15))
        raw = np.frombuffer(temp_raw[: w * h_ * 2], dtype="<i2").reshape(h_, w)
        temp = raw / scale + offset - 273.15
        print(f"解码方式: int16,  ℃ = raw/{scale} + {offset} - 273.15")
    else:
        raise SystemExit(f"未知每像素字节数: {bpp}")

    print("\n--- 温度矩阵统计 ---")
    print(f"  形状      : {temp.shape}")
    print(f"  最小值    : {temp.min():.2f} ℃")
    print(f"  最大值    : {temp.max():.2f} ℃")
    print(f"  平均值    : {temp.mean():.2f} ℃")
    print(f"  中位数    : {np.median(temp):.2f} ℃")
    iy, ix = np.unravel_index(np.argmax(temp), temp.shape)
    print(f"  最高点    : ({ix}, {iy}) = {temp.max():.2f} ℃")
    cy, cx = h_ // 2, w // 2
    print(f"  画面中心  : ({cx}, {cy}) = {temp[cy, cx]:.2f} ℃")

    np.save(os.path.join(OUT, "temperature.npy"), temp)
    if jpeg:
        with open(os.path.join(OUT, "thermal.jpg"), "wb") as f:
            f.write(jpeg)
    print(f"\n已保存: out/temperature.npy , out/thermal.jpg ({len(jpeg) if jpeg else 0} B)")
    return meta, temp, jpeg


if __name__ == "__main__":
    grab()
