# AM-eye · 海康微影在线测温热像仪对接

用 **HTTP Digest + ISAPI** 直接对接 HIKMICRO 在线测温热像仪（`HM-TD2AXXT-15C`），
无需海康 SDK、无需编译环境，纯 Python 即可实现：

- **逐像素温度矩阵** —— 640×512 float32 摄氏度，可算画面任意一点温度
- **规则测温实时流** —— 设备推送的最高/最低/平均温 + 最热点坐标
- **参数控制** —— 伪彩、AGC、快门校正、发射率、温度档、报警阈值、测温规则

> 本仓库同时是一份**实测报告**：所有结论均在真机上验证，并记录了 10 个容易踩的坑。

---

## 设备信息（实测）

| 项目 | 值 |
|---|---|
| 型号 | `HM-TD2AXXT-15C` |
| 固件 | `V5.5.336` build `260415` |
| 平台 | 海康 `G5`，`deviceCategory = thermometryDevice` |
| 探测器 | **640 × 512** |
| 认证 | HTTP Digest（realm `IP Camera(EA908)`） |
| 端口 | 80 / 443 / 554(RTSP) / 8000 |

---

## 快速开始

```powershell
# 1. 安装依赖
pip install requests numpy matplotlib pillow

# 2. 设置设备密码（凭据只走环境变量，不写进代码）
$env:CAM_PWD = "你的设备密码"

# 3. 抓一帧逐像素温度矩阵 + 热成像图
python thermal_grab.py
```

可选环境变量：`CAM_HOST`、`CAM_USER`、`CAM_PWD`、`CAM_SCHEME`、`CAM_PORT`、`CAM_CHANNEL`（见 `cam.py`）。

---

## 三个必须知道的硬约束

1. **`?format=json` 不通用** —— 大多数接口加它反而 403，但取温度的两个接口**必须加**。
2. **热成像通道号是 `1`** —— 通道 2 全部 403（网上"通常是 2"的说法对本机不成立）。
3. **浏览器无法直连设备** —— 无 CORS 头，且 JS 做不了 Digest 认证 → **必须配后端代理**。

---

## 目录结构

| 文件 | 作用 |
|---|---|
| `cam.py` | 设备连接配置（凭据从环境变量读取） |
| `thermal_grab.py` | **核心参考**：抓取并解析逐像素温度矩阵 |
| `probe.py` | 逐接口能力探测 |
| `fetch.py` / `fetch2.py` | 批量抓取 ISAPI 资源 |
| `test_ops.py` / `test_ops2.py` | CORS / RTSP / 控制写入 / 长连接流 验证 |
| `palette_probe.py` | 伪彩名称穷举（确认 8 个合法值） |
| `find_rules.py` / `rules_read.py` / `rules_read2.py` | 测温规则接口定位 |
| `all_chunks.py` / `scrape_webui.py` | 下载设备 Web UI 的 JS，反查真实 API |
| `viz.py` | 生成"伪彩图 vs 温度矩阵"对比图 |
| `HIKMICRO热像仪对接调研报告.md` | 前期调研报告（含选型与路线对比） |
| `热像仪自研页面对接技术分析.md` | **完整实测技术分析**（推荐先读这份） |

---

## 核心接口速查

```text
# 逐像素温度矩阵（必须带 format=json）
GET /ISAPI/Thermal/channels/1/thermometry/jpegPicWithAppendData?format=json
    → multipart：JSON 元数据 / 热成像 JPEG / 640×512 float32 温度矩阵（单位℃）

# 规则测温实时流（长连接持续推送，必须 stream=True）
GET /ISAPI/Thermal/channels/1/thermometry/realTimethermometry/rules?format=json

# 抓图
GET /ISAPI/Streaming/channels/101/picture      # 1280×720
GET /ISAPI/Streaming/channels/102/picture      # 640×512
rtsp://admin:密码@192.168.1.64:554/Streaming/Channels/101

# 控制（PUT）
/ISAPI/Thermal/channels/1/thermometry/basicParam       # 发射率/距离/温度档/报警阈值
/ISAPI/Thermal/channels/1/thermometry/pixelToPixelParam
/ISAPI/Thermal/channels/1/thermometry/rules            # 测温规则
/ISAPI/Image/channels/1/Palettes                       # 伪彩
/ISAPI/Image/channels/1/AGC                            # 自动增益
/ISAPI/Image/channels/1/FFC                            # 快门校正
```

**合法伪彩（仅这 8 个）**：`Rainbow` `Fusion1` `Fusion2` `Ironbow1` `RedHot` `GreenHot` `Rain` `Sepia`
（`WhiteHot` / `BlackHot` / `Ironbow` 等会返回 400）

---

## 注意

- 本仓库**不包含** `out/` 目录：其中有设备自身的前端 JS（约 27MB，受版权保护）与原始报文。
- 请勿把设备密码提交进仓库；本仓库统一通过 `CAM_PWD` 环境变量传入。
- 抓取温度矩阵约 **1.35 MB/帧**，建议 1~3 fps 轮询，不要当视频流用。
