# Fully Unlock Your Apple Device

A Windows-first Codex/Agent Skill for enabling and troubleshooting selected Apple device features. It brings together the Siri/ChatGPT and AirPods workflows I tested, their common failure points, and recovery instructions. An Apple Watch hypertension-notification workflow is included as an untested reference.

[简体中文 README](README.md)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)
![Skill](https://img.shields.io/badge/skill-Codex%20%2F%20Agent-orange.svg)

---

## What has been tested

| Feature | Recorded result | Workflow |
| --- | --- | --- |
| ChatGPT through Siri on a China-mainland iPhone | **Working on my device.** Settings survived a normal restart, and ChatGPT remained usable after disconnecting USB. Both the Hong Kong/Traditional Chinese and US/English (US) configurations worked. | [Siri and ChatGPT](references/siri-chatgpt.md) |
| AirPods Pro 3 hearing-health features and EN 352 | **Feature entries appeared after accessory location moved the phone to Berlin, Germany.** Completing the Hearing Test, enabling the EN 352 switch, and retention after restoring real location are separate checks. | [AirPods hearing health](references/airpods-hearing.md) |
| Apple Watch hypertension notifications | **Third-party instructions; not tested by me.** Device, region, and health eligibility must be checked first. | [Apple Watch hypertension notifications](references/watch-hypertension.md) |

The tested iPhone was a China-mainland iPhone 17 Pro running iOS 27.3, build `24C5037i`. GestaltX was version 1.1.1, and the successful signing tool was iloader 2.4.1 on Windows. The AirPods were Pro 3, model A3065, firmware 9B47.

The project name describes its direction, not a claim that every Apple feature is supported. It does not claim to enable eSIM, FaceTime Audio, or every Siri AI Beta feature. See the [test history and lessons learned](references/tested-cases.md) for the exact results.

## Why I made this skill

I spent time changing the map location with i4Tools, adjusting language and region, resetting my AirPods, and nearly trying another Apple ID. The map moved to Germany, but the hearing features did not appear. The successful path used local MFi authentication and USB CarKit/iAP2 accessory location.

Siri brought a different set of problems: GestaltX installed successfully but lacked a usable App Group, the desktop signing tool needed its own proxy route, and matching the phone and Siri languages was easy to overlook.

This skill organizes those checks so a local agent can work through the relevant failure stage. Each module also contains instructions that can be followed without an agent.

## The workflow

1. Identify the feature and the exact device, OS build, and firmware.
2. Check the required USB connection, signing permissions, language, and network conditions.
3. Preserve the relevant original state. Export MobileGestalt before editing it; inspect existing full-device backups before starting another one. For temporary location, record the real location and a stop method.
4. Run only the selected module and its required changes.
5. Verify installation, permissions, writes, restart persistence, menus, downloads, and actual feature use as separate results.
6. Stop temporary processes, verify real-location recovery, and retain the rollback files.

Passwords, verification codes, trust prompts, and health questions are handled by the device owner.

## Details that matter

- **Match the system and Siri languages.** I first used Hong Kong as the system region, Traditional Chinese as the system language, and Mandarin Chinese (Taiwan) for Siri. Later, the system region was changed to the US and both languages to English (US); ChatGPT still worked.
- **System region and MobileGestalt Region Code are different settings.** The later US test did not require changing the MobileGestalt code from `ZA` to `LL`.
- **An installed app may still lack App Group access.** My Sideloadly 0.72 installation had no usable App Group. iloader 2.4.1 resolved that case. Check the actual signing result rather than assuming installation proves access.
- **The phone's network is separate from the desktop tool's network.** A working phone proxy does not mean iloader can reach Apple's developer endpoints. The included launcher can scope a local HTTP proxy to iloader alone.
- **A changed map location does not prove regional feature eligibility.** In my i4Tools attempt, the map showed Germany while the hearing features remained unavailable.

## Compatibility

GestaltX 1.1.1 supports **on-device MobileGestalt access on iOS/iPadOS 27.x**. Version 26.x is not supported for that access route, even though the IPA's minimum installation version is 26.0. Being installable, showing “Supported,” reading the cache, and enabling a particular service are different checks.

This restriction concerns the GestaltX workflow; it does not establish the compatibility of the separate AirPods accessory-location tool. See the [Siri compatibility section](references/siri-chatgpt.md#支持的系统版本先分清能安装和能读取) and the corresponding upstream documentation before trying another version.

## Install and use

Repository: [zouchenzhen/fully-unlock-your-apple-device](https://github.com/zouchenzhen/fully-unlock-your-apple-device).

The project was previously named `apple-feature-lab`. When updating an older installation, use the new directory name and skill invocation name.

```powershell
git clone https://github.com/zouchenzhen/fully-unlock-your-apple-device.git
```

Copy the entire `fully-unlock-your-apple-device` directory into your project's `.agents/skills/` directory or your user's `~/.agents/skills/` directory. You can also give the local path to [SKILL.md](SKILL.md) directly in a task. Follow your host's skill-management conventions if they differ.

Example prompts:

```text
Use $fully-unlock-your-apple-device to check my iPhone and help me configure the ChatGPT extension in Siri.
```

```text
Use $fully-unlock-your-apple-device to check hearing protection and EN 352 availability for my AirPods Pro 3. Explain the executable steps first.
```

```text
Use $fully-unlock-your-apple-device to explain Apple Watch hypertension-notification requirements and the untested workflow. Do not modify my devices.
```

The entry point loads the relevant module. A request for explanation stays an explanation; execution follows the device owner's authorized scope. Local terminal and USB access are needed for the device scripts. Installing a skill does not give a browser-only chat access to a connected iPhone.

## Repository structure

```text
SKILL.md                 Agent entry point and module routing
README.md                Chinese guide
README.en.md             English guide
agents/                  Skill interface metadata
references/              Workflows, shared checks, tested cases, and sources
scripts/                 Diagnostic, comparison, proxy, and bounded-location helpers
tests/                   Offline tests
```

## Scripts and validation

Python 3.11 or later is required. Cache comparison and the default location-plan mode use the standard library. Install device dependencies only when running the USB workflows:

```powershell
python -m pip install -r requirements-device.txt
```

The location helper defaults to **plan mode**: it does not import the USB library, connect to a phone, or send coordinates. Execution modes require explicit inputs and use source checks, time limits, and process cleanup. See [script parameters and results](references/scripts.md).

```powershell
python -m unittest discover -s tests -v
```

The 21 offline tests cover synthetic cache comparisons, private-output handling, input rejection, connection mocks, and cancellation/process-tree cleanup. They do not connect to a phone. The packaged wrappers have not been revalidated on a physical device; the earlier successful workflows and this offline validation are recorded separately.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New modules should include their sources, device and version requirements, minimal changes, observable success criteria, and recovery steps. Mark third-party instructions and untested experiments accordingly.

Useful reports include the public device model, OS build or firmware, tool version, exact error, and completed checks. Remove account details, serial numbers, UDIDs, IP addresses, certificates, and location history. Do not submit raw device caches or phone logs.

## Sources and license

The workflows build on existing tools and research, including [GestaltX](https://github.com/huamidev/GestaltX), [iloader](https://github.com/nab138/iloader), [iap2-location-bridge-windows](https://github.com/xpqball/iap2-location-bridge-windows), [accessory-location](https://github.com/aur3l14no/accessory-location), [DiPlay](https://github.com/shihabal3amri/DiPlay), and [PlayPort](https://github.com/youcci/playport). Lestill's videos and tutorials helped inform the original attempts. More projects and articles are listed in [related projects and further reading](references/related-projects.md).

Original documentation and helper scripts use the [MIT License](LICENSE). Upstream projects retain their own licenses, and third-party authentication material is not relicensed by this package. IPA files, keygens, signing certificates, MFi private keys, pairing records, and private device caches are not included.

## Community

[LINUX DO — Chinese developer community](https://linux.do/)

## Star History

If this project helps you, consider giving it a star.

[![Star History Chart](https://api.star-history.com/svg?repos=zouchenzhen/fully-unlock-your-apple-device&type=Date)](https://star-history.com/#zouchenzhen/fully-unlock-your-apple-device&Date)

I appreciate and thank the LINUX DO community for its open-source sharing, practical experience, and technical discussions.
