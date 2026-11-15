# 国行 iPhone 启用 Siri／ChatGPT 扩展：实际成功流程

我原来使用的是国行 Siri。按教程调整设备配置，再补齐系统语言、Siri 语言和地区后，ChatGPT 入口出现，资源下载完成后可以正常使用。手机拔掉 USB 后也仍可用。

**语言设置很重要：系统语言与 Siri 语言要一致。只改设备能力或地区，流程还没有完成。**

## 我验证过的两组语言与地区

| 组合 | 系统地区 | 系统语言 | Siri 语言 | 结果 |
| --- | --- | --- | --- | --- |
| 首次成功 | 香港 | 繁體中文 | 中文（國語／普通話—台灣） | ChatGPT 可设置并正常使用 |
| 后续追加测试 | 美国 | 英语（美国） | 英语（美国） | ChatGPT 仍然可用 |

香港不是系统地区的唯一选择。后续美区测试说明，美国地区与美式英语这组设置也可用；关键是不能只改其中一种语言。

这里的“系统地区”是“设置 → 通用 → 语言与地区”中的选项，与 GestaltX 中的 MobileGestalt 地区代码是两层设置。下面的设备缓存修改仍按首次成功时的 `ZA` 和 AI 能力 `1` 记录，不应把系统地区改为美国理解成还要把 GestaltX 改为美国。

## 原理与使用范围

GestaltX 通过沙盒逃逸漏洞访问系统的 MobileGestalt 缓存，并修改设备地区、功能能力的覆盖值。这次我只改了地区代码和 Apple Intelligence 能力，没有修改机型、CPU、主板或其它硬件标识。

这不是安装完整越狱环境，但也不是普通的语言设置。修改前需要保存原始缓存，保留恢复路径。系统升级、缓存重建或服务端规则变化，都可能改变后续结果。

本文实际完成的是 Siri 中的 ChatGPT 扩展。全新的 **Siri AI（Beta）** 有独立的语言、账号地区和服务资格要求，本次没有通过强制写入 `SiriMode = 2` 来开启它，也没有把 FaceTime、eSIM 或手表功能算作同时开通。

## 1. 准备工具和备份

本次使用：

- Windows，已安装 Apple 官方“Apple 设备”，能通过 USB 识别手机。
- [GestaltX 1.1.1 官方发行版](https://github.com/huamidev/GestaltX/releases/tag/v1.1.1)。
- [iloader 2.4.1 官方 Windows 版](https://github.com/nab138/iloader/releases/tag/v2.4.1)。
- 手机已有正常可用的境外网络；这次使用日本全局节点。

我使用的 GestaltX 1.1.1 IPA 与官方发行包的 SHA-256 一致：

```text
0621b070cafacb2f1f83fad459697d02263e513b04d77b462da333c5b0a4e708
```

先检查现有整机备份。如果已有较新的已完成加密备份，是否重做全量可根据新增数据决定；**当前 MobileGestalt 的原始文件仍要另外导出**，两种备份的作用不同。

## 2. 用 iloader 签名安装，保留 App Group

1. 用数据线连接手机，解锁并信任电脑。
2. 手机启用开发者模式；如需重启，按系统提示完成。
3. 打开 iloader，使用自己的 Apple ID 登录，由本人输入密码和验证码。
4. 选中这台 iPhone，点 **Import IPA／导入 IPA**，选择原始 `GestaltX_1.1.1.ipa`。
5. 执行 **Sign & Install App／签名并安装应用**，保持默认扩展处理，保留分享扩展。无需为了这一步安装 SideStore。
6. 如手机要求信任开发者，在“设置 → 通用 → VPN 与设备管理”中由本人完成。
7. 打开 GestaltX，在 **Tools → Read MobileGestalt** 读取设备。

成功标准是手机显示实际机型、**Status: Connected**，并列出 CacheExtra 数量。我这次首次读取是 86。

页面的 `iOS Supported` 只是工具对系统版本的判断，不能代替签名权限和实际读取成功；其它设备也不必恰好显示 86。

签名账号只用于申请开发证书，不必与手机的 iCloud 或 App Store 账号一致。签名时登录另一个账号，也不会自动切换手机上的这些账号。

### 我遇到的签名问题

最初用 Sideloadly 0.72，虽然 IPA 安装成功、分享扩展也没有删除，但读取时报：

```text
The signed app has no usable App Group.
Enable its App Group capability and sign it again.
```

核对后，实际签名没有授予可用 App Group。这时 App 还没有读到系统缓存，更没有完成修改。换用 iloader 后取得了有效 App Group，读取才成功。因此，**安装成功不等于签名权限完整**；如果看到这个报错，应该修复签名，而不是继续改其它开关。

登录过程中还遇到过：

```text
Auth error -22406: Enter the correct password for this Apple Account.
```

我换了另一个自己的 Apple ID 后登录成功，手机主 iCloud 账号无需跟着换。密码和验证码只在工具与系统提示中由本人输入。

## 3. 先导出当前原始缓存

读取成功后，先不应用任何修改：

1. 在 **Backups** 确认初始设备备份已生成。
2. 回到 **Tools → Export Plist**，导出当前设备文件。
3. 将导出文件保存到手机之外的本地备份位置，并保留 App 内的初始备份。

正式导出包含设备绑定证明，便于以后导回同一设备。仅仅把某个 plist 拿来导入，不等于它就是可用于这台手机的原始备份。

电脑上的比较脚本不验证设备证明的 HMAC，也不能仅凭两份文件证明它们属于当前连接的手机。原始文件必须来自本机读取，恢复导入仍由 GestaltX 做设备证明与布局校验。

这些缓存可能含有设备信息，不要上传到公开仓库。保留当前 GestaltX 及其数据，后续需要重新签名时优先沿用本次成功的签名账号。

## 4. 只应用两项修改

在 **Tools → Intelligence** 中设置：

| 项目 | 本次选择 |
| --- | --- |
| Region Code | **Hong Kong（ZA）** |
| Apple Intelligence Capability | **Enable** |
| Sales Region | Keep Current |
| Siri AI Mode | Keep Current |
| On-Device Siri | Keep Current |
| 其它项目 | Keep Current |

返回 **Tools → Apply Changes**。确认预览仅涉及所需的地区代码和 AI 能力，再应用。已经符合目标值的字段不必重复修改；我这次原值不同，因此预览为两项变化。

看到 **Write verified／写入已验证** 后，正常重启手机。我的实际差分是：

- Region Code：`CH → ZA`。
- Apple Intelligence Capability：原本没有额外覆盖值，写入 `1`。
- 原始销售地区后缀 `CH/A` 保留，其它 CacheExtra 字段及 CacheData 未变。

重启后重新读取并导出文件，与原始缓存比较，确认只有这两项变化。这个步骤验证的是设备配置已经写入并跨重启保留。

可用本包的 `scripts/verify_mobilegestalt.py` 只读比较两个本地文件。严格的 `--expected-siri` 模式对应上面这组历史原值；其它原始配置先使用普通比较模式，按实际差分判断，不为满足测试而改动设备。

## 5. 补齐系统语言、Siri 语言和地区，再重启

这一步很容易漏。GestaltX 中的设备代码与系统语言、Siri 语言、系统地区是几项独立设置，前面写入成功后，手机侧的配置仍要做完。

首次成功时，我按香港和繁体中文配置：

1. **设置 → 通用 → 语言与地区**：把繁體中文设为主要语言，地区选香港。
2. **设置 → Siri／Apple Intelligence & Siri → 语言**：选中文（國語／普通話—台灣）。
3. 按教程确认 App Store 使用自己的非国区账号；本次没有把退出主 iCloud 作为操作步骤。
4. 完成后再正常重启一次。
5. 解锁手机，重新确认日本全局节点连接正常。

后来我又把系统地区改为美国，并把**系统语言和 Siri 语言一起改成英语（美国）**，ChatGPT 仍然可用。两种语言保持一致，比只记住“地区选香港”更重要。

## 6. 启用 ChatGPT，等资源下载后实际调用

进入“设置 → Siri／Apple Intelligence & Siri”：

1. 如需要，先开启 Apple Intelligence，等待模型或相关资源下载。
2. 找到 **ChatGPT → Set Up／设置**，按引导启用。也可能位于 **Extensions／延伸功能** 中。
3. 可以先不登录 ChatGPT 账号，保留默认的请求确认提示。
4. 下载期间保持 Wi-Fi、供电和正常的境外网络。
5. 完成后明确让 Siri 调用 ChatGPT，例如：

```text
請用 ChatGPT 寫一首四行的春天小詩。
```

或在美式英语配置下使用：

```text
Ask ChatGPT to write a four-line poem about spring.
```

确认回复中显示 ChatGPT 标识并实际生成内容。单纯问天气、看到新动画或看到 ChatGPT 入口，都不足以代替这一步。

我最后确认功能已经能用，手机拔掉 USB 后也仍然可用。电脑只在签名安装、配置修改和核验时使用，不需要一直连接来维持功能。

## Windows 签名网络故障

这次 iloader 曾报：

```text
Failed to list developer devices
error sending request for url
https://developerservices2.apple.com/services/QH65B2/ios/listDevices.action
```

测试发现，电脑直连该接口超时，经本机 HTTP 代理可达。**手机开着全局代理，不代表电脑上的签名工具也走代理。**

仓库附带 [Start-IloaderWithProxy.ps1](../scripts/Start-IloaderWithProxy.ps1)。完全退出 iloader 后，在仓库根目录执行；下面是本次电脑的安装路径和代理端口：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-IloaderWithProxy.ps1 -Executable E:\application\iloader\iloader.exe -ProxyUri http://127.0.0.1:10808
```

`Executable` 应填写本机 iloader 的实际路径，端口也应与本机代理监听端口一致。脚本只给新启动的 iloader 子进程设置代理，不修改系统全局代理、不关闭证书校验，也不读取签名账号密码。

这一步只针对电脑的连接故障，不是每个人都要执行。若网络请求已经正常、错误变成账号认证错误，应按实际错误处理。

## 重启、掉签和恢复

我已验证正常重启后两项配置保留，也验证了拔掉 USB 后 ChatGPT 仍可用。免费签名的 App 到期后可能无法打开，但不会因为到期就自动反向改回已经写入的缓存。以后需要调整或恢复时，仍要先让 GestaltX 恢复为可运行状态。

需要回退时，优先在当前 GestaltX 的 **Backups** 中选择初始备份执行 Restore，检查差分、应用并完整重启；也可对这两个预设使用 Restore Original。AI 能力原本没有额外覆盖值时，应恢复为原状态，而不是自行填 `0`。

系统语言、系统地区和 Siri 语言在系统设置中另行恢复。系统升级、缓存重建或服务端规则变化可能使功能状态改变，因此不把这次成功称为永久激活。未经授权的系统修改也可能影响售后认定，不能按“没有完整越狱”推断为没有风险。

## 参考来源

- [GestaltX 官方仓库](https://github.com/huamidev/GestaltX)与 [1.1.1 发行版](https://github.com/huamidev/GestaltX/releases/tag/v1.1.1)。
- [GestaltX 1.0.1 发行说明](https://github.com/huamidev/GestaltX/releases/tag/v1.0.1)：地区代码与销售地区后缀独立处理。
- [iloader 官方仓库](https://github.com/nab138/iloader)与 [2.4.1 发行版](https://github.com/nab138/iloader/releases/tag/v2.4.1)。
- [GestaltX App Group 问题讨论](https://github.com/huamidev/GestaltX/issues/82)。
- [Apple：在 iPhone 开启 ChatGPT](https://support.apple.com/guide/iphone/turn-on-chatgpt-iph00fd3c8c2/ios)。
- [Apple：获取 Siri AI](https://support.apple.com/en-us/127893)。
- [Apple 中国保修条款](https://www.apple.com/legal/warranty/products/ios-warranty-china.html)。

Mac 上 Clash／Mihomo 的 Siri 代理 skill 等补充资料，见 [相关项目与延伸阅读](related-projects.md)。
