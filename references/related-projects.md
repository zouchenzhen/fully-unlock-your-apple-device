# 相关项目与延伸阅读

我把相关 skill、上游工具和技术资料整理在这里，方便按问题继续查阅。这个项目侧重 Windows 上的三模块整合、实际排错和验证记录；具体定位、签名与系统缓存工具来自已有开源项目。

核对日期：2026 年 11 月 15 日。下列作者的实操报告与本项目的验证状态分别记录，我自己的 Watch 模块仍未实测。

## 相关 skill

| 项目 | 适合参考的内容 | 平台与范围 |
| --- | --- | --- |
| [flute/apple-watch-hypertension-skill](https://github.com/flute/apple-watch-hypertension-skill) | 中文新手教程、USB CarKit/iAP2 香港定位、停止与真实位置恢复检查、作者的 S12 实操复盘 | Mac 本地 Agent 的手表专用路线；适合研究 Watch 模块，不能直接当成本项目 Windows 封装的测试结果 |
| [kuangre123/clash-siri-apple-intelligence-proxy](https://github.com/kuangre123/clash-siri-apple-intelligence-proxy) | Clash Verge／Mihomo 的进程代理、代理组和 DNS 排错 | 主要解决 Mac 上 Siri／Apple 智能的网络路径；不替代 iPhone 的 GestaltX、App Group 和语言配置 |

本次读取的手表项目版本为 [`660e5b9`](https://github.com/flute/apple-watch-hypertension-skill/tree/660e5b984d3b02b25c5b3ac04e0cd45dedae3d5e)，其 [SKILL.md](https://github.com/flute/apple-watch-hypertension-skill/blob/660e5b984d3b02b25c5b3ac04e0cd45dedae3d5e/SKILL.md)、[实操复盘](https://github.com/flute/apple-watch-hypertension-skill/blob/660e5b984d3b02b25c5b3ac04e0cd45dedae3d5e/references/retrospective.md)和[第三方来源说明](https://github.com/flute/apple-watch-hypertension-skill/blob/660e5b984d3b02b25c5b3ac04e0cd45dedae3d5e/THIRD_PARTY_NOTICES.md)值得一起看。作者报告过 S12、iOS 27.0.1 与 macOS 的成功组合，项目使用 GPL-3.0-only。

代理项目本次读取的版本为 [`8231fc7`](https://github.com/kuangre123/clash-siri-apple-intelligence-proxy/tree/8231fc7438feb7cac99f4a3a27e202b1586521a8)，可参阅其 [SKILL.md](https://github.com/kuangre123/clash-siri-apple-intelligence-proxy/blob/8231fc7438feb7cac99f4a3a27e202b1586521a8/SKILL.md)；项目使用 MIT 许可证。

## 上游工具与其它实现

| 项目 | 用途与本项目的关系 |
| --- | --- |
| [huamidev/GestaltX](https://github.com/huamidev/GestaltX) | Siri 流程实际使用的 MobileGestalt 编辑、备份与恢复工具；它是上游工具，不是本项目编写的 skill |
| [xpqball/iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows) | AirPods 流程使用的 Windows USB iAP2 实现；其地图验证与这里记录的耳机入口验证是不同的测试范围 |
| [JerseyRiver/airpods-hearing-aid-hk-guide](https://github.com/JerseyRiver/airpods-hearing-aid-hk-guide) | ESP32、Wi-Fi 版 iPad 和香港 Wi-Fi 定位信息的另一条路线，包含监管域观察记录；适合比较定位来源，不应与德国 EN 352 的功能范围混为一谈 |

认证与协议相关的 [DiPlay](https://github.com/shihabal3amri/DiPlay)、[PlayPort](https://github.com/youcci/playport)、[accessory-location](https://github.com/aur3l14no/accessory-location)，以及签名使用的 [iloader](https://github.com/nab138/iloader)，在对应模块中另有具体版本和操作说明。

## 提示词出处与原理研究

- **[LINUX SB：国行 iPhone Air 与 18 系列写境外 eSIM 的社区实操](https://linux.sb/topic/30986)**。作者使用 iPhone Air、iOS 27.3 beta 和 GestaltX 1.0.3，包含 App Group、开发者模式、保留销售地区、AI 配置及备份经验。其“26.x 不支持”的说法已结合本文使用的 GestaltX 1.1.1 官方源码进一步限定为本机 MobileGestalt 访问；账号条件和 eSIM 附加选项仍属于该作者的经验，不能自动成为本项目的实测支持。具体整理见 [Siri 兼容性说明](siri-chatgpt.md#支持的系统版本先分清能安装和能读取)。
- **[V2EX：把这段话给 Codex 免费开启高血压通知](https://www.v2ex.com/t/1248960)**，2026 年 10 月。公开帖介绍 macOS、本地 MFi-v3 认证、USB CarKit/iAP2 与香港 NMEA 提示词，作者也链接了 `accessory-location`。这是追溯手表教程技术路线的公开来源之一。
- **[修改 iOS 定位的几种方法](https://nvme0n1p.dev/posts/ios-location-modify)**，2026 年 4 月 22 日。比较开发者模拟定位与 iAP2 配件定位，并讨论爱思和 AnyGo 的实现思路，适合理解为什么“地图位置已改变”与功能资格可能是不同结果。
- **[Lagrange Point：Bypassing regulatory locks, Faraday cages and upgrading your hearing](https://lagrangepoint.substack.com/p/airpods-hearing-aid-hacking)**，2024 年 11 月 12 日。记录 AirPods Pro 2、iOS 18.1 的监管地区与 Wi-Fi 定位实验，是理解原理的历史资料；其中具体方法要结合当前系统重新判断。

## 怎样使用这些资料

按目标模块查阅，不把不同平台、系统版本、目标地区或作者反馈拼成一条未经验证的执行流程。需要使用外部实现时，先核对其当前条件和源码，再决定是否纳入本项目。

本页只做链接和摘要，没有合入这些 skill 的代码。后续移植时遵守各自许可证并保留原作者与版本；本项目的 MIT 许可证不会改变外部项目或第三方认证材料的许可范围。实际测试结果继续记录在 [实操与踩坑记录](tested-cases.md)。
