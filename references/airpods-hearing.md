# AirPods Pro 3 德区听力功能：Windows USB iAP2 实测

我在 Windows 上通过 USB 向 iPhone 提供柏林的配件定位。苹果地图移动到柏林后，AirPods Pro 3 设置中的听力测试、听力保护和 EN 352 保护入口随即出现，我在手机上确认了这一结果。这份记录保留了当次有效步骤和验证范围。

我这次激活使用的是**德国地址**，最后成功的位置是柏林。听力测试仍需本人佩戴耳机完成，EN 352 保护也需按手机引导手动开启；功能出现不等于已经完成这些操作。

## 我走过的弯路

一开始我自己摸索，用爱思助手改虚拟定位，把语言、时区和地区也一起改了，甚至重置耳机，功能还是不出现。后来我已经准备尝试登录德国 Apple ID。

转机是搜到了 Lestill 的视频和直播。其实中午我就看过视频，但没有找到群聊，没拿到完整的操作说明。我把视频里的提示词复制给 Codex，原本想让它按 AnyGo 的方向试一次。第一次没成功，我没有让它沿原方案继续排查，反而又把方向带回了爱思助手，这一步又绕了回去。

拿到完整教程后，我重新尝试配件定位路线，最后通过本地 MFi-v3 认证和 USB CarKit/iAP2 向手机发送德国柏林的位置。地图到柏林后，听力测试、听力保护和 EN 352 保护入口随即出现。

给大家避一个我实际踩过的坑：**爱思助手虽然能把地图蓝点改到德国，但我这次用它无法开启耳机功能，这条路没有跑通。** 我拿到的教程提供了 AnyGo 这条可行路线；本包记录并复现的是下面的开源本地 USB iAP2 方案，没有运行商业 AnyGo 或注册机，也没有依赖 AnyGo 云端。两条工具路线的来源和验证范围分开记录。

所以排查时，不要看到地图已经显示德国，就认定耳机的地区资格也变了。我这次没有靠登录德国 Apple ID 来解决问题，真正跑通的是配件定位。德国也是这份记录的激活地点，不是香港或美国。

## 实测环境与结果

| 项目 | 本次条件 |
| --- | --- |
| 电脑 | Windows，已安装 Apple 官方“Apple 设备”，USB 设备服务正常 |
| 手机 | iOS 27.3，已解锁并信任电脑 |
| 耳机 | AirPods Pro 3，型号标识 A3065，固件 9B47 |
| 连接 | 数据线连接电脑，双耳佩戴 |
| 目标位置 | 德国柏林，北纬 52.5200、东经 13.4050 |
| 网络及无线状态 | 德国 VPN；曾开启飞行模式，再单独开启 Wi-Fi 和蓝牙 |
| 最终确认 | 地图显示柏林，随后出现听力测试、听力保护、EN 352 保护入口 |

德国 VPN、飞行模式、Wi-Fi 和蓝牙是当时的操作条件，没有逐项排除，因此不能断言每一项都必需，也不能由本次结果判断“只改定位一定够用”。这是一组设备上的一次经验，其他系统版本和机型需各自验证。

## 使用的项目

- [xpqball/iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows)：本次使用的 Windows USB 实现，基于提交 `3d0af910ac6868df99978f593adb2fcbd2de8cc1`。
- [aur3l14no/accessory-location](https://github.com/aur3l14no/accessory-location)：上述实现的上游，提供最小 iAP2 配件定位流程。
- [shihabal3amri/DiPlay v0.2.7](https://github.com/shihabal3amri/DiPlay/releases/tag/v0.2.7)：本次本地认证材料的来源。APK 仅作为压缩包读取，没有安装到 iPhone 或运行。
- [youcci/playport](https://github.com/youcci/playport)：提示词引用的 MFi-v3 与 CarPlay 协议参考。它本身是 CarPlay 接收端，不是现成的 Windows USB 耳机功能开关。

## 操作流程

### 1. 准备手机和 USB 连接

安装 Apple 官方“Apple 设备”，确认它能识别手机。手机解锁，完成“信任此电脑”，保持 USB 连接。

在手机上检查：

1. “设置 → 隐私与安全性 → 定位服务”已开启。
2. “定位服务 → 系统服务 → 系统自定义”已开启。
3. “地图”允许“使用 App 期间”访问位置，并开启精确位置。
4. 打开苹果地图，点击当前位置，先确认能显示真实位置。

本流程不需要越狱、开发者模式或更换 Apple USB 驱动。不要为了连接这个工具，把正常工作的 Apple 驱动替换为 WinUSB。先停止爱思或其它工具的循环定位，避免两个来源互相覆盖。

### 2. 安装公开工具并探测 CarKit

需要 Python 3.11 及以上版本、Git 和 [uv](https://docs.astral.sh/uv/)。从本文仓库根目录打开 PowerShell，执行：

```powershell
git clone https://github.com/xpqball/iap2-location-bridge-windows.git
cd iap2-location-bridge-windows
git checkout 3d0af910ac6868df99978f593adb2fcbd2de8cc1
uv sync --locked --python 3.11
uv run python tools/probe_windows_service.py
```

正常情况下会看到：

```text
USB lockdown connected
CarKit service opened successfully
```

这个探测只打开并关闭 `com.apple.carkit.service`，不加载认证材料、不发送坐标。

### 3. 本地准备认证材料

本次使用 DiPlay v0.2.7 APK 中的两个文件：

```text
assets/offline-mfi/certificate.p7b
assets/offline-mfi/identity.pk8
```

它们是 DiPlay 公开预览版中附带的共享实验性配件身份，来源和使用限制见 [DiPlay 声明](https://github.com/shihabal3amri/DiPlay/blob/v0.2.7/docs/THIRD_PARTY_NOTICES.md#experimental-authentication-data)。它们不是个人 Apple 账户的密钥，也不是新签发给本工具的 MFi 身份；Apple 后续可能不再接受该身份。

公开工具提供可选导入器：

```powershell
uv run python tools/import_diplay_identity.py --download
```

导入器下载固定版本，核对完整 APK 的 SHA-256，校验文件格式及证书与私钥的匹配关系，仅将两个文件保存在仓库外的本地身份目录。它不会安装或执行 APK，也不会把私钥发送给手机或外部服务。认证阶段只向手机提供配件证书和挑战签名。

按导入器输出设置当前 PowerShell 会话的两个路径变量。默认目录对应的命令是：

```powershell
$identityDir = Join-Path $env:LOCALAPPDATA 'iap2-location-bridge-windows\identity'
$env:IAP2_LOCATION_BRIDGE_WINDOWS_CERT_FILE = Join-Path $identityDir 'certificate.p7b'
$env:IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE = Join-Path $identityDir 'identity.pk8'
```

已有身份目录时导入器会拒绝覆盖。无需重复下载或重新导入；按实际存放位置设置路径即可。不要把身份文件、APK、手机配对记录或本机日志上传到 GitHub。

### 4. 使用上游原配件身份字符串

本次成功的发送使用了 `accessory-location` 的原身份字符串。Windows 仓库上述提交已将这些字符串改名，其 README 也注明改名后的身份尚未重新完成实机验证。

运行本文附带的独立补丁脚本：

```powershell
uv run python ../scripts/apply-upstream-identity.py src/iap2_location_bridge_windows/profile.py
```

脚本只接受上述固定版本的 `profile.py`，核对完整源码哈希后再修改；其他版本或已有未知改动会被拒绝。它仅将 `identity()` 的六项名称改回：

```python
(
    "Accessory Location Lab", "AL-1", "Local Research",
    "AL-LOCAL-001", "0.1", "1",
)
```

这是 Name、ModelIdentifier、Manufacturer、SerialNumber、FirmwareVersion、HardwareVersion 六个配件描述字段。手动编辑也必须先通过同一固定版本与完整源码哈希核对，不能以手动替换绕过脚本的版本拒绝；其余能力声明和定位编码保留。

本次使用的本地包装脚本通过 `--upstream-identity` 在运行时替换这六个字段，没有永久修改依赖仓库。原公开工具没有这个命令行选项，使用公开仓库复现时，需要完成上述等效修改。已有对照不足以单独证明六个字符串就是成功原因。

### 5. 探测认证，再发送柏林坐标

使用本包带全进程时限的包装入口。以下命令仍在前面克隆的 `iap2-location-bridge-windows` 目录内执行；当前 Python 环境来自该工具的 `uv sync`。先完成不发送坐标的认证探测：

```powershell
uv run python ../scripts/run_iap2_location.py --mode auth-probe --bridge-root . --cert-file $env:IAP2_LOCATION_BRIDGE_WINDOWS_CERT_FILE --key-file $env:IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE --duration 20 --timeout 45 --upstream-identity
```

确认出现 `authentication_succeeded` 后，发送柏林坐标：

```powershell
uv run python ../scripts/run_iap2_location.py --mode send --bridge-root . --cert-file $env:IAP2_LOCATION_BRIDGE_WINDOWS_CERT_FILE --key-file $env:IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE --latitude 52.5200 --longitude 13.4050 --duration 180 --timeout 225 --upstream-identity
```

本次实际成功运行的本地包装命令记录为：

```text
python run_bridge.py send --seconds 180 --upstream-identity
```

上面的 `run_bridge.py` 仅用于说明原始实测记录，不是本包的执行入口。本包使用 `run_iap2_location.py`，目标坐标必须显式传入，默认运行只输出计划。它复用固定版本上游的发送行为，并提供停止标志及覆盖整个子进程的超时清理。上游 `--duration` 只限制握手完成后的主循环，不能当作全进程时限。成功记录没有使用时钟偏移或小数秒修正。

发送期间，在手机上操作：

1. 保持手机解锁、USB 连接，打开苹果地图并点击当前位置。
2. 到“定位服务”关闭总开关，等待约 10 秒，再重新开启；此时电脑继续发送。
3. 回地图再次点击当前位置，确认蓝点实际移动到柏林。
4. 双耳佩戴并连接 AirPods Pro 3，重新查看耳机设置中的听力健康区域。

这次操作后，手机地图显示柏林，我随即确认听力测试、听力保护、EN 352 保护入口全部出现。

### 6. 停止并检查恢复

实验结束后等待限时退出，或按 Ctrl+C，断开 USB。重新在地图中请求真实位置；如果仍显示上次定位，退出重开地图，必要时重新开关定位服务并等待重新定位。随后检查耳机功能是否保留，并恢复实验前的网络和无线设置。

进程退出只说明发送停止，不能代替真实位置恢复检查。恢复真实位置后的功能保留情况没有完成单独记录，因此不把它写成永久激活。

## 为什么地图能改，功能仍可能不出现

苹果地图显示的位置与系统对地区功能的可用性判断是两个结果。前期使用普通软件模拟定位时，地图已经显示德国，耳机设置仍没有听力健康入口；当时读取到的 `countryd` 日志中，`os_eligibility` 和 `LatLonLocation` 的地区仍为 `CN`。这说明单看地图截图不足以确认地区功能判断已经改变。

iAP2 这条路线让电脑作为配件提供定位：通过已信任的 USB 连接打开 CarKit 服务，完成配件识别和 MFi-v3 挑战认证，等待手机订阅定位后，再发送带校验和的 GGA/RMC NMEA 语句。Apple 的 Core Location 也区分 [配件提供的位置](https://developer.apple.com/documentation/corelocation/cllocationsourceinformation/isproducedbyaccessory) 与 [软件模拟的位置](https://developer.apple.com/documentation/corelocation/cllocationsourceinformation/issimulatedbysoftware)。这种来源差异可以解释为什么两条路线的行为不同。

最终成功时没有再次抓到系统地区日志的 `DE` 值；实际确认结果是地图到达柏林，随后所有上述功能入口出现。认证、地图位置和功能入口是不同的检查点。

## 如何判断停在哪一层

| 观察到的事件或现象 | 能说明什么 |
| --- | --- |
| `link_ready` | iAP2 链路建立 |
| `identification_accepted` | 配件描述被接受 |
| `authentication_succeeded` | 手机接受本次配件认证 |
| `location_requested` | 手机订阅了定位数据 |
| `location_link_acknowledged` | 数据获得链路确认，不能说明坐标已被系统采用 |
| 苹果地图蓝点移动 | 地图采用了目标位置 |
| 耳机设置出现对应入口 | 该功能入口在当前条件下可用 |

前期实验曾反复出现 `GPRMC NMEA Screening failed`。尝试按手机时间校准、延后时间和改为小数秒，都没有形成有效修复证据，因此成功步骤不包含这些调整。

源码审查还发现，DiPlay 将两行 NMEA 合并放进一个 parameter `0`，而这里使用的 Windows 实现分别放入两个 parameter `0`。当时准备过严格 DiPlay 格式的兼容方案，但在实际运行该方案之前，功能已经出现。本次成功仍使用 Windows 原有 NMEA 编码，不能把“合并两行 NMEA”写成成功原因。

## 来源、许可证与发布内容

Windows 工具基于 `aur3l14no/accessory-location` 修改，相关协议代码与 DiPlay、PlayPort 等公开项目的研究和实现有关。上述项目的源码按各自仓库的 GPL-3.0 声明使用；若发布包含其代码的修改版，应保留原作者、来源和许可证，并按许可证提供对应源码。第三方认证材料不属于这些项目源码的 GPL 授权范围。

这份记录的发布范围是操作说明、公开源码引用和不包含个人数据的必要修改。不要随仓库分发 `certificate.p7b`、`identity.pk8`、APK、配对记录、设备标识、账户信息或原始手机日志。

Apple 官方功能说明可参考 [AirPods 听力健康功能](https://support.apple.com/guide/airpods/hearing-health-features-airpods-pro-2-3-devd9aac5b42/web) 和 [听力保护](https://support.apple.com/120850)。功能入口出现后，仍按手机上的引导完成实际设置和测试。

香港 Wi-Fi 版 iPad 的另一实现，以及开发者模拟定位、配件定位与监管地区的研究文章，见 [相关项目与延伸阅读](related-projects.md)。
