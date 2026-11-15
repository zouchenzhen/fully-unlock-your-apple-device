# Apple Feature Lab

**Apple 功能启用与排错：给人看的实操记录，也给 AI 用的 Agent Skill。**

我在 Windows 上完成了国行 iPhone 的 Siri／ChatGPT 扩展配置，以及 AirPods Pro 3 德国地区听力功能入口的开启。这里保留有效步骤、踩坑经过和恢复方法，并加入尚未实测的 Apple Watch 高血压通知教程模块。

本包只对下面登记的功能提供流程，不把“满血”当作所有 Apple 功能都能同时解锁。工具和系统版本会变化，复现时先看对应模块的条件与验证状态。

## 从这里选择功能

| 目标 | 当前记录 | 人类教程与 AI 模块 |
| --- | --- | --- |
| Siri 中使用 ChatGPT | **本机实测可用**；重启和拔掉 USB 后可用；香港繁中、美区双美式英语组合均成功 | [Siri／ChatGPT](references/siri-chatgpt.md) |
| AirPods Pro 3 听力健康及 EN 352 | **德国柏林配件定位后入口出现**；听力测试、EN 352 实际开关和恢复位置后的长期保留分别验收 | [AirPods 听力健康](references/airpods-hearing.md) |
| Apple Watch 高血压通知 | **第三方教程，作者未实测**；先核对机型、地区、健康适用条件 | [Watch 高血压通知](references/watch-hypertension.md) |

我的原始经历、成功配置、失败尝试和证据层级集中在 [实测与踩坑记录](references/tested-cases.md)。

## 整体步骤

1. **选定功能，确认设备。** 型号、系统 build、耳机固件或 watchOS 要对应到所选模块，不用一套开关处理全部设备。
2. **做必要检查。** 手机解锁、USB 信任、账号签名权限、电脑网络与手机网络分别确认。
3. **保存原始状态。** Siri 修改前导出当前 MobileGestalt；已有近期整机备份时先核实，不无差别重做全量。临时定位流程记录起始真实位置与停止方式。
4. **按模块执行。** Siri 只修改所需字段；耳机使用有时限的配件定位；手表流程先确认接受未实测实验。
5. **逐层确认结果。** “软件装上”“写入成功”“地图改变”“菜单出现”“功能实际可用”是不同的检查点。
6. **结束并检查恢复。** 结束临时进程，确认真实定位恢复；保留原始文件和回退方法，记录功能是否仍可用。

账号密码、设备密码、验证码和健康问答由本人处理。不需要把这些内容发到聊天里。

## 几个最容易踩坑的地方

**系统语言与 Siri 语言要一致。** 我首次成功用香港地区、繁體中文和中文（台灣）Siri，后来系统地区改成美国、两种语言一起改为英语（美国），ChatGPT 仍能使用。系统地区与 GestaltX 的 Region Code 是两层设置，美区测试没有再次修改 MobileGestalt。

**安装成功不等于 App Group 正常。** Sideloadly 0.72 虽装上 GestaltX，但实际 App Group 为 0，读取失败；换 iloader 2.4.1 后才读到配置。出现 `no usable App Group` 应处理签名，不要继续改系统。

**手机的境外网络不等于电脑工具也走代理。** iloader 的 Apple 开发者接口曾直连超时，经电脑本机代理可达；代理启动器只作用于该子进程。

**地图在德国不等于耳机资格已切换。** 我用爱思改位置、改语言地区、重置耳机都没成功，曾准备换德国 Apple ID。最终成功用的是德国柏林的 USB 配件定位，详细经过见实测记录。

## 使用这个 skill

项目地址：[zouchenzhen/apple-feature-lab](https://github.com/zouchenzhen/apple-feature-lab)。

先取得仓库：

```powershell
git clone https://github.com/zouchenzhen/apple-feature-lab.git
```

包名：`apple-feature-lab`。统一入口是 [SKILL.md](SKILL.md)，它按目标加载对应模块。

在本地 Codex 中，将整个 `apple-feature-lab` 目录放到当前项目的 `.agents/skills/` 下，或放到用户的 `~/.agents/skills/` 中。也可以在任务中明确提供当前 `SKILL.md` 的本地路径。当前主机如有不同的技能安装规则，以主机的技能管理入口为准。

可用这样的任务开始：

```text
使用 $apple-feature-lab，先检查我的 iPhone 条件，再帮助我配置 Siri 的 ChatGPT 扩展。
```

```text
使用 $apple-feature-lab，帮我检查 AirPods Pro 3 的听力保护和 EN 352 功能，先说明当前可执行的步骤。
```

```text
使用 $apple-feature-lab，先解释 Apple Watch 高血压通知的官方条件和未实测教程，不要修改设备。
```

默认允许 AI 根据任务自动选择本 skill，但发现 skill 不代表获准自动修改设备。明确只做分析时，它应停在分析；用户授权执行后，再推进该模块。

本包需要本地终端和设备连接能力才能运行 USB 脚本；单纯导入 skill 不会给纯网页聊天增加这些能力。当前执行脚本以 Windows、Python 3.11+ 为主，macOS 的第三方教程来源不等于本包已完成跨平台实测。

Siri 模块使用的 GestaltX 1.1.1，本机 MobileGestalt 访问支持 iOS／iPadOS 27.x，26.x 不支持这条路线；IPA 能安装不等于能读取或修改。详细范围及社区案例见 [系统兼容性说明](references/siri-chatgpt.md#支持的系统版本先分清能安装和能读取)。这个限制不套用到独立的耳机配件定位工具。

## 脚本与离线验证

参数、依赖、输出和错误处理见 [脚本说明](references/scripts.md)。定位脚本默认只生成计划，发送模式需要明确指定坐标；只读缓存比较不修改输入文件。

```powershell
python -m unittest discover -s tests -v
```

离线测试使用合成数据与模拟连接，不会连接手机。通过离线测试说明脚本检查和清理行为符合预期，不代表所有手机或未来系统版本都兼容。

历史成功案例与本次脚本封装分别记录：封装版尚未重新做真机复测，不把离线通过写成新的设备成功案例。

## 增加功能和反馈

新增设备功能时，按 [贡献说明](CONTRIBUTING.md) 补齐来源、兼容条件、操作差分、成功判据和恢复路径。新方法先标记教程或实验，保留日期和原始结论，验证后再更新支持状态。

反馈时提供公开型号、系统 build、工具版本、错误文本和已经完成的检查。遮住账号、序列号、UDID、IP、设备名、证书和定位历史，不提交原始手机日志或系统缓存。

## 来源与许可证

思路参考 Lestill 的视频与教程，并在实际操作中核对 [GestaltX](https://github.com/huamidev/GestaltX)、[iloader](https://github.com/nab138/iloader)、[Windows iAP2 工具](https://github.com/xpqball/iap2-location-bridge-windows)、[accessory-location](https://github.com/aur3l14no/accessory-location)、[DiPlay](https://github.com/shihabal3amri/DiPlay) 和 [PlayPort](https://github.com/youcci/playport) 的公开实现。功能条件以各模块链接的 Apple 原文为准。

更多同类 skill、其它定位路线、公开提示词出处与原理研究，见 [相关项目与延伸阅读](references/related-projects.md)。本项目侧重把成熟工具与 Windows 实操排错整理成可复现流程，并保留清楚的来源与验证范围。

本包原创文档和辅助脚本使用 [MIT 许可证](LICENSE)。引用、调用或另行下载的上游代码继续遵守各自许可证；本包不重新授权这些项目或第三方认证材料。没有打包 IPA、注册机、签名证书、MFi 私钥、配对文件、私人缓存或群聊原图。
