# -*- coding: utf-8 -*-
"""
设备连接配置 —— 凭据一律从环境变量读取，避免明文写进代码/仓库。

用法（PowerShell）:
    $env:CAM_PWD = "你的设备密码"
    python thermal_grab.py

可选环境变量:
    CAM_HOST     设备 IP        （默认 192.168.1.64）
    CAM_USER     用户名         （默认 admin）
    CAM_PWD      密码           （**必须自行设置**）
    CAM_SCHEME   http / https   （默认 http）
    CAM_PORT     端口           （默认 80）
    CAM_CHANNEL  热成像通道号    （默认 1；本机实测通道 2 不支持）
"""
import os

import requests
from requests.auth import HTTPDigestAuth

CAM_HOST = os.environ.get("CAM_HOST", "192.168.1.64")
CAM_USER = os.environ.get("CAM_USER", "admin")
CAM_PWD = os.environ.get("CAM_PWD", "")
CAM_SCHEME = os.environ.get("CAM_SCHEME", "http")
CAM_PORT = os.environ.get("CAM_PORT", "80")
CAM_CHANNEL = int(os.environ.get("CAM_CHANNEL", "1"))

# 兼容各脚本原先的 BASE 变量（默认端口不显式拼出）
BASE = f"{CAM_SCHEME}://{CAM_HOST}"
if CAM_PORT not in ("80", "443", ""):
    BASE += f":{CAM_PORT}"

# 兼容旧脚本里的 USER / PWD 命名
HOST = CAM_HOST
USER = CAM_USER
PWD = CAM_PWD


def session():
    """返回已配置 HTTP Digest 认证的 requests.Session。"""
    if not CAM_PWD:
        raise SystemExit(
            "未设置 CAM_PWD 环境变量（设备管理员密码）。\n"
            "PowerShell 下请先执行： $env:CAM_PWD = '你的密码'"
        )
    s = requests.Session()
    s.auth = HTTPDigestAuth(CAM_USER, CAM_PWD)
    return s
