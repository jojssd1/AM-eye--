# 海康微影在线测温热像仪（HM-TD2AXXT-15C）与电脑对接 · 调研报告

- 调研日期：2026-09-24
- 设备铭牌：HIKMICRO 在线测温热像仪，型号 HM-TD2AXXT-15C，电源 12V-24V ⎓ 4.8W MAX，序列号 EA9081641，标准 Q/HWY 002-2020，杭州微影软件有限公司

---

## 0. 一句话结论

**不需要安装海康的 SDK 或任何编译环境。** 这台设备是标准的海康系网络设备，用**普通 HTTP 请求（ISAPI 协议）+ HTTP Digest 认证**，在 Windows 上用 Python 写几十行代码，就能同时拿到：

1. **热成像画面**（JPEG 图 / RTSP 视频流）
2. **逐像素温度矩阵**（真正的辐射测温原始数据，能算出画面上任意一点的温度）
3. **测温规则结果**（你在设备上画好的点 / 线 / 框，直接返回最高温、最低温、平均温）

这是社区在多款海康 / 海康微影热像仪上独立验证过的路径。SDK 路线（HCNetSDK）功能更全但工程量大得多，**不建议作为起步方案**。

---

## 1. 这台设备到底是什么

### 1.1 厂商核对（已确认）

hikmicrotech.com 网站页脚版权方为 "© Hangzhou Microimage Software Co., Ltd."，与铭牌上的"杭州微影软件有限公司"一致。海康微影（HIKMICRO）是海康威视旗下专做热成像的子品牌，**固件栈、协议栈与海康网络摄像机同源**——这是后面所有方案成立的基础。

### 1.2 型号解析

| 字段 | 含义 | 置信度 |
|---|---|---|
| HM | HIKMICRO 前缀 | 确认 |
| TD2A | 系列码。官方国际站归入 **Autofocus Box Cameras（自动对焦测温枪机）**，即"在线测温热像仪" | 确认 |
| 2 / XX | 分辨率编码位。同族规律：2→256×192，3→384×288，6→640×512 | **推测**（该具体型号无公开资料） |
| T | 测温型（Thermometry） | 确认 |
| -15 | 镜头焦距 **15mm**（同族另有 -25，即 25mm） | 确认（由官方型号 HM-TD2A37T-15/Q 佐证） |
| C | 版本 / 区域后缀，含义未确认。同族公开后缀为 **/Q**、/V、/X、/T1、/KHD，未见 "-15C" | **未确认** |

> ⚠️ **型号疑点（重要）**：多方检索（HIKMICRO 官网、中文搜索引擎、经销商 B2B 站点）**均未找到 "HM-TD2AXXT-15C" 或任何 "-15C" 结尾的型号**。铭牌上的 "XX" 很可能是系列铭牌的占位写法（一块标签覆盖多个 SKU），或该型号为国内版 / OEM 定制版。
> **实践影响**：不需要纠结——接上设备后用 `/ISAPI/System/deviceInfo` 一查就知道真实型号和固件版本。

### 1.3 官方同族型号的规格（HM-TD2A37T-15/Q，最接近的公开资料）

| 项目 | 参数 |
|---|---|
| 探测器 | VOx 非制冷焦平面 |
| 分辨率 | 384×288（另有 640×512 的 TD2A67T） |
| 像元间距 | 17 μm |
| NETD | ≤35 mK（@25℃，F#=1） |
| 镜头 | 15 mm，F1.0，最小成像距离 0.5 m，自动对焦 |
| 测温范围 | -20~150 ℃ 或 0~650 ℃（双档） |
| 测温精度 | Max(±2 ℃, ±2%) |
| 帧率 | 50 fps；编码 H.265 / H.264 / MJPEG |
| 供电 / 功耗 | 10-30 VDC / **4.8 W Max** ← 与铭牌完全吻合，可确认属于该家族 |
| 外壳 | 铝，93×50×50 mm，约 344 g，IP40，-20~50 ℃ |

> 数据来源：HIKMICRO 官方产品页及其数据手册（链接见第 8 节）。

### 1.4 硬件接口（决定"怎么连"）

官方同族规格（已确认）：

- **1× RJ45** 10M/100M/1000M 自适应以太网口 ← **主通道**
- 1× RS-485（支持 Modbus）
- 1× 报警输入（0-3.3 VDC）、1× 报警输出（NC / 电平量）
- 1× CVBS 模拟视频输出
- 供电：DC 输入端子

**关键结论：**

- ❌ **不支持 PoE**（同族数据表未列出，与明确标注 PoE 的双光谱机型形成对比）→ 必须用 **12V-24V 直流电源适配器**供电，网线只走数据。
- ❌ **没有 USB / Type-C UVC 接口** → 这台设备**不能**像普通 USB 摄像头那样插上就被 Windows 识别成摄像头，**必须走网络**。
- ✅ 以太网口是唯一的数据通道，也是所有方案的基础。

---

## 2. 四条技术路线对比

| 路线 | 能拿视频 | 能拿逐像素温度矩阵 | 能拿规则测温值 | 工程复杂度 | 定性 |
|---|---|---|---|---|---|
| **ISAPI**（HTTP RESTful + Digest） | ✅ 抓图 | ✅ | ✅ | **低**（纯 HTTP） | **推荐**，社区多项目实测 |
| **HCNetSDK**（官方设备网络 SDK） | ✅ | ✅（有热成像专章） | ✅ | 高（C/C++ DLL 依赖） | 备用，需私有协议时才用 |
| **RTSP** | ✅ | ✅（社区实测，格式无公开规范） | ❌ | 中（需解 RTP 私有帧） | 只看画面时够用 |
| **ONVIF** | ✅ | ❌ | ❌ | 低 | **拿不到温度**，官方 Profile 不含辐射测温 |
| 云平台（Hik-Connect / 萤石云） | ✅ | ❌ | ❌ | 低 | 官方未开放测温 API，**不可行** |

**判断要点**：只有 ISAPI、HCNetSDK、RTSP 三条能取到温度数据；ONVIF 和云平台只能取视频。其中 ISAPI 是唯一"零编译依赖 + 能拿全量温度"的路线。

---

## 3. 推荐路线详解：ISAPI

### 3.1 基本原理

设备内置一个 HTTP 服务器，所有读写都通过 URL 完成，认证方式为 **HTTP Digest**（不是 Basic，需要 `--digest` 或 `HTTPDigestAuth`）。返回格式在 URL 上加 `?format=json` 可切成 JSON，否则默认 XML。

### 3.2 第一步永远是"探测能力"

**不同型号 / 固件支持的接口不同**（实测中有的机型 `jpegPicWithAppendData` 直接返回 notSupport），所以必须先查能力列表，再决定用哪个接口：

```
GET /ISAPI/Thermal/capabilities
```

关注这几个字段：`isSupportJpegPicWithAppendData`、`isSupportRealTimethermometry`、`isSupportClickToThermometry`、`isSupportThermometryHistorySearch`。

### 3.3 三种数据获取方式

**方式 A：逐像素温度矩阵（最完整，能自己算任意点温度）**

```
GET /ISAPI/Thermal/channels/{通道}/thermometry/jpegPicWithAppendData?format=json
```

返回 multipart 多段数据，依次为：

1. **JSON 元数据**：`channel`、`jpegPicWidth`、`jpegPicHeight`、`jpegPicLen`、`temperatureDataLength`、`p2pDataLen`、`visiblePicLen`、`scale`、`offset`
2. **温度二进制块**（长度 = 宽×高×每像素字节数）
3. 热成像 JPEG
4. 可见光 JPEG（若机型支持双光谱）

**温度换算（关键）：**

- 若 `temperatureDataLength / (宽×高) == 4`：数据是 **float32，直接就是摄氏度**
- 若等于 2：数据是 **int16，公式为 `℃ = raw / scale + offset - 273.15`**（offset 是开尔文）

> ⚠️ 不要试图从伪彩图或灰度图反推温度。伪彩 JPEG 是经过自动增益（AGC）拉伸的**显示图**，没有固定的"灰度-温度"映射，只能用于肉眼观察。真实温度必须来自上面的原始矩阵。

**方式 B：只读规则测温值（最省事）**

```
GET /ISAPI/Thermal/channels/{通道}/thermometry/realTimethermometry/rules?format=json
```

返回 `ThermometryUploadList` 数组，含 `ruleName`、`ruleID`、`thermometryUnit`（0=℃, 1=℉, 2=K），以及：

- 线/框规则：`LinePolygonThermCfg{ MaxTemperature, MinTemperature, AverageTemperature, TemperatureDiff }`
- 点规则：`PointThermCfg{ temperature }`

**方式 C：只要画面**

- 抓图：`GET /ISAPI/Streaming/channels/{id}/picture`
- 视频流：`rtsp://用户名:密码@设备IP:554/Streaming/Channels/101`（101 主码流，102 子码流）

### 3.4 其他有用的接口

| 用途 | 路径 |
|---|---|
| 设备信息 | `/ISAPI/System/deviceInfo` |
| 测温配置读/写 | `/ISAPI/Thermal/channels/{t}/thermometry`、`/basicParam`、`/1/regions`、`/thermometryMode`、`/tempRangeParam` |
| 伪彩 / 调色板 | `/ISAPI/Image/channels/{c}/Palettes` |
| 自动增益 AGC | `/ISAPI/Image/channels/{c}/AGC`、`/thermalAGC` |
| 快门校正（FFC） | `/ISAPI/Image/channels/{c}/shutter`、`/FFC` |
| 报警事件流 | `/ISAPI/Event/notification/alertStream`（长连接流式，事件码 TMA / TMPA / TDA） |

**已知的坑**：热成像通道号**通常是 2**（不是 1），可见光是 1。如果某个接口报 "Device Error"，多半是通道号或参数错了——把 1 和 2 都试一遍。

---

## 4. 备用路线：HCNetSDK（设备网络 SDK）

**什么时候才需要它**：需要设备私有功能（录像回放、云台、多设备统一管理、无法用 HTTP 表达的操作）时。

要点：

- 从 `open.hikvision.com`（海康开放平台，注册免费）→ 工具下载 / 设备集成 SDK 获取，版本 V6.x
- SDK 包内的 `开发文档/` 里**含《设备网络SDK编程指南（热成像）.pdf》**——热成像是网络 SDK 的一个模块，**没有**独立的"热成像测温 SDK"分包
- 官方示例语言：**MFC(C++)、C#、Java**（**无官方 Python**）
- Windows 64 位必须搭配一致的 DLL 集：`HCNetSDK.dll`、`HCCore.dll`、`PlayCtrl.dll`，以及**必须整个目录随程序一起加载的 `HCNetSDKCom\`**，另有一堆渲染依赖（AudioRender、HWDecode、MP_Render、SuperRender、YUVProcess、libmmd、GdiPlus、d3dx9_43、D3DCompiler_43 等）
- Python 调用需用 ctypes 封装（社区库 `laugh12321/HCNetSDK-python` 可用，但**它不含测温功能**，且最后一次更新是 2023 年）。已知坑：位数必须匹配、须调 `NET_DVR_SetSDKInitCfg` 指定 Com 目录、日志目录须可写、**Windows 下字符串按 GBK 编码**、回调函数必须存为模块级全局变量否则被 GC 回收导致崩溃

**结论**：起步阶段完全不需要 SDL。ISAPI 拿不到的东西，再考虑上 SDK。

---

## 5. 当前状态与第一步动手清单

### 5.1 本机环境（已实测）

| 项目 | 状态 | 说明 |
|---|---|---|
| 操作系统 | Windows 10 家庭中文版 19045 | ✅ |
| Python | **3.14.5**（另装 3.12、3.11） | ✅ 建议**用 3.12** 跑项目，3.14 太新，个别库轮子可能还没适配 |
| Node.js | v26.0.0 | ✅ |
| Java | OpenJDK 21 | ✅（若走 HCNetSDK 的 Java 示例） |
| ffmpeg | ❌ 未安装 | 不影响——`opencv-python` 自带解码器，可解 RTSP |
| .NET SDK | ❌ 未安装 | 走 C# 路线才需要 |
| C/C++ 编译器 | ❌ 未安装 | 走 C++ SDK 路线才需要 |

**结论**：走 **Python + ISAPI** 路线，现有环境**零安装即可开工**（只需 `pip install requests numpy`）。

### 5.2 网络现状（已实测扫网）

扫描了 `192.168.101.0/24` 全网的 554（RTSP）/ 80（HTTP）/ 8000（HCNetSDK）端口：

- **未发现热像仪**。扫到的 4 台设备均非海康系（Server 标识为 `Mrvl-R2_0`、`Microsoft-IIS/10.0` 等）。
- 本机网卡：`192.168.101.78`（另有一个 `100.94.60.49`，是 VPN / 虚拟网卡）
- 海康设备**出厂默认 IP 通常是 `192.168.1.64`**，与本机所在的 `192.168.101.x` 不是同一网段，**当前直连不通**。

**⇒ 所以第一件事不是写代码，而是把设备"弄到网上"。** 具体做法（按顺序）：

1. **供电**：接 12V-24V 直流电源（**不支持 PoE**，网线不供电），等 1-2 分钟启动
2. **接网线**：设备 RJ45 ↔ 电脑网口（直连也行，一般支持自动翻转）
3. **找到设备**：设备默认 IP 是 `192.168.1.64`，两种方式
   - 用官方工具 **SADP**（海康设备网络搜索工具）或 **HIKMICRO Studio** 搜索局域网设备并修改 IP
   - 或给电脑网卡临时加一个 `192.168.1.x` 的 IP，直接访问 `http://192.168.1.64`
4. **激活设备**：全新设备首次使用必须**设置管理员密码激活**（网页或 Studio 里完成）
5. **画测温规则**：在设备网页里配置点 / 线 / 框测温规则（否则方式 B 读不到任何规则值）
6. **验证连通**（Git Bash 里执行，IP 换成改好的）：

```bash
# 查设备信息（确认型号、固件版本、序列号）
curl --digest -u admin:你的密码 http://192.168.1.64/ISAPI/System/deviceInfo

# 探测支持哪些热成像能力 —— 这一步决定后面用哪个接口
curl --digest -u admin:你的密码 http://192.168.1.64/ISAPI/Thermal/capabilities

# 读规则测温值（通道 2，错了就换 1 试试）
curl --digest -u admin:你的密码 \
  "http://192.168.1.64/ISAPI/Thermal/channels/2/thermometry/realTimethermometry/rules?format=json"

# 拉逐像素温度矩阵 + JPEG（结果存文件，再用 Python 解析）
curl --digest -u admin:你的密码 -o thermal.bin \
  "http://192.168.1.64/ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json"

# 用 VLC / OpenCV 验证视频流
# rtsp://admin:你的密码@192.168.1.64:554/Streaming/Channels/101
```

**如果 `Thermal/capabilities` 返回 404 或 Device Error**：说明该固件用的是海康旧版热成像接口，需要改试 `/ISAPI/Thermal/channels/2/thermometry`、`/basicParam` 等路径，或者退回 HCNetSDK 路线。这是本次调研中**唯一必须靠实机验证**的不确定点。

---

## 6. 可复用的开源代码

| 仓库 / 包 | Star | 最后更新 | 能干什么 |
|---|---|---|---|
| [xynogen/hiktemp](https://github.com/xynogen/hiktemp) | 0 | 2026-09 | **直接给 (H,W) float32 摄氏度矩阵**，纯 requests+numpy。最省事，可抄 |
| [MaomaoMAo-17/hikvision-thermal-parser](https://github.com/MaomaoMAo-17/hikvision-thermal-parser) | 17 | 2025-05 | multipart 解析，int16/float32 双兼容，中文 README |
| [ljelschen/HikvisionThermal](https://github.com/ljelschen/HikvisionThermal) | 0 | 2025-11 | 纯 ISAPI 调用样例，适合理解接口 |
| [neirolis/hikvision](https://github.com/neirolis/hikvision) | 6 | 2021-03 | Go 语言 ISAPI 测温读取 |
| [Hughav92/HIKVISION_RTSP_Thermal_Data](https://github.com/Hughav92/HIKVISION_RTSP_Thermal_Data) | 1 | 2026-03 | 从 RTSP RTP 包解析逐像素温度（非标做法，风险高） |
| [laugh12321/HCNetSDK-python](https://github.com/laugh12321/HCNetSDK-python) | 28 | 2023-11 | HCNetSDK 的 Python ctypes 封装（**不含测温**） |
| [MissiaL/hikvision-client](https://github.com/MissiaL/hikvision-client) | 260 | 2026-06 | ISAPI XML 封装（**不含测温**） |
| [mezz64/pyHik](https://github.com/mezz64/pyHik) | 208 | 2026-09 | 事件流（移动侦测/报警），**不含测温** |
| [kamjin3086/hik_isapi_docs](https://github.com/kamjin3086/hik_isapi_docs) | 1 | 2024-12 | 海康 ISAPI 文档 PDF 镜像 |

> 注意：**GitHub 上搜不到任何 HM-TD2A 系列（在线测温盒子机）的开源对接项目**。现有的 HIKMICRO 相关项目全是手持机 / USB 路线（Pocket2 辐射 JPEG、UVC 采集等），对本机不适用——本机没有 USB 口。所以代码需要基于上面的 ISAPI 路径自己写。

---

## 7. 待确认清单（诚实标注）

调研中**未能确认**、需要实机验证的：

1. **`HM-TD2AXXT-15C` 这个精确型号在公开资料中不存在**，"XX" 的分辨率（256×192 / 384×288 / 640×512）只能接上设备后用 `deviceInfo` 查
2. **尾缀 "C" 的含义未确认**（同族公开后缀是 /Q）
3. **该固件是否完整支持 `/ISAPI/Thermal/...` 这套接口**——海康微影官方**没有公开 ISAPI / SDK 协议文档**（官网下载中心只有 Studio/Viewer 软件、固件和手册）。虽然同属海康生态、大概率兼容，但**必须实测**（第一步就跑 capabilities）
4. **Modbus TCP 是否开放测温寄存器**——未找到任何官方或可靠社区证据，建议直接问海康微影技术支持
5. **官方 Java SDK 是否存在**——未能证实
6. **是否支持双光谱（带可见光通道）**——官方数据表只列了热成像通道，与个别经销商页面说的"双光谱"矛盾，以数据表为准

---

## 8. 参考链接

**厂商官方**
- 产品页（Autofocus Box Cameras）：https://www.hikmicrotech.com/en/industrial-products/autofocus-box-cameras/
- 下载中心（软件/固件/手册）：https://www.hikmicrotech.com/en/support/download-center/
- 数据手册 HM-TD2A37T-15/Q：https://webassets.hikmicrotech.com/global/asset/bf86aacbece345788ba4d0f80b561409.pdf
- 数据手册 HM-TD2A67T-15/Q：https://webassets.hikmicrotech.com/global/asset/302125030a24498998328e6a2216644a.pdf
- 用户手册（Thermographic Network Box Camera V5.5.336）：https://webassets.hikmicrotech.com/global/asset/f2d10d01b26e4732ba35f2f4ef5142c5.PDF
- 快速入门：https://webassets.hikmicrotech.com/global/asset/d5ee992ee64044e6b4bc6a3a5ee3c3fe.pdf

> 注：hikmicrotech.com 对脚本抓取有 WAF 拦截（curl 返回 403），**浏览器正常访问没问题**。以上 PDF 链接取自官方产品页的下载区，路径有效。

**海康开放平台**
- 开放平台（注册后可下载 SDK 与 ISAPI 文档）：https://open.hikvision.com/

**协议标准**
- ONVIF Profile 列表（可见无热成像/测温 Profile）：https://www.onvif.org/profiles/
