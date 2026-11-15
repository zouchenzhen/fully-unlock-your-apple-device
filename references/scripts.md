# 脚本入口与结果

脚本分成只读检查、计划和显式执行。先在仓库根目录运行命令；不会因为读取 skill 就自动启动这些脚本。

Python 3.11+。缓存比较与计划模式仅用标准库。需要连接设备时，才在独立虚拟环境安装设备依赖：

```powershell
python -m pip install -r requirements-device.txt
```

本次打包的辅助脚本经过离线测试，封装版尚未重新做真机复测。历史成功案例使用的版本和原始步骤见 [tested-cases.md](tested-cases.md)。

## 只读 USB 预检

```powershell
python scripts/device_preflight.py
```

只查询已信任 USB 设备的公开型号、系统版本／build、开发者模式与加密备份开关。不自动配对，不更改备份密码，不读取个人内容。只有恰好一台 USB 设备时才连接；多台时让用户保留目标设备后重试。

退出码 `0` 表示只读检查完成；`2` 表示依赖或连接准备不满足；`1` 表示读取失败；`130` 表示用户中断。单个状态无法读取时显示未知，不能把未知当作未开启。

## 只读 MobileGestalt 比较

参数是用户在本机保存的两份文件。例如：

```powershell
python scripts/verify_mobilegestalt.py .\private\MobileGestalt-before.plist .\private\MobileGestalt-after.plist
```

脚本只读文件，比较类型、CacheExtra 变化以及缓存数据、代际信息是否一致。输出已知字段的有限值和其它变化数量，不输出设备标识或任意原始值。

`--expected-siri` 严格对应这次历史差分：原始 `CH` 变为 `ZA`，AI 覆盖值原本不存在、之后为整数 `1`，其余内容不变：

```powershell
python scripts/verify_mobilegestalt.py .\private\MobileGestalt-before.plist .\private\MobileGestalt-after.plist --expected-siri
```

严格匹配退出 `0`，合法文件但差分不符退出 `2`，输入无法读取或格式不符退出 `1`。普通比较成功退出 `0` 只表示比较完成，不表示功能已启用；原值不同的设备先用普通比较，不要为了严格模式通过而改变设备原值。

它识别并在比较时排除顶层 `GestaltXDeviceProof`，但**不验证证明的 HMAC、不证明文件所属设备，也不写回手机**。正式恢复仍交给 GestaltX 的本机证明与缓存布局校验。

## USB iAP2：计划、服务探测、认证与发送

```powershell
python scripts/run_iap2_location.py
```

默认 `--mode plan`，不导入 USB 库、不连接手机、不读取身份文件、不发送坐标。提供 `--bridge-root` 时只静态检查上游源码。执行模式如下：

| 模式 | 会做什么 | 需要身份文件 |
| --- | --- | --- |
| `plan` | 输出计划与是否提供参数 | 否 |
| `service-probe` | 打开并关闭 CarKit 服务 | 否 |
| `auth-probe` | 配件识别、认证、等待订阅，不发坐标 | 是 |
| `send` | 条件满足后限时发送显式目标坐标 | 是 |

上游桥接工具需要另行安装，本包不捆绑其协议代码。固定提交：

```text
3d0af910ac6868df99978f593adb2fcbd2de8cc1
```

执行前校验上游模块与认证 helper 的源码哈希，仅接受该版本的原始文件或本包的精确配件标识补丁。校验失败时停止，不能删除校验来迁就另一版本；升级需要审查并重新验证。

在根目录旁已按 [AirPods 模块](airpods-hearing.md)克隆上游、准备其 Python 依赖后，可先做服务探测：

```powershell
python scripts/run_iap2_location.py --mode service-probe --bridge-root .\iap2-location-bridge-windows --timeout 30
```

认证和发送参数见 AirPods 模块中的完整命令。接口接受：

- `--cert-file`、`--key-file`：仓库外的本地身份文件路径；不在命令行传入文件内容。
- `--latitude`、`--longitude`：发送模式必须显式给出，不能省略目标或继承上一台设备的位置。
- `--duration`：上游握手后循环时长，1–600 秒；认证默认 20 秒，发送默认 180 秒。
- `--timeout`：监督整个工作进程的总时限，1–660 秒；发送默认 duration 加 45 秒。
- `--upstream-identity`：运行时使用历史成功轮的原配件标识，不更改其它能力声明。不能据此认定配件名称已被单独证明为成功原因。
- `--stop-file`：可选的新停止标志路径；文件出现时请求清理并停止，已有标志则拒绝新会话。脚本不删除用户的标志文件。

按 Ctrl+C 或创建指定停止文件可请求停止。子进程会尝试执行流和 helper 清理；Windows 由 Job Object 限制进程树，超时或父进程关闭后回收本轮 worker 与 helper。不能建立该保护时，不开始 USB 操作。退出 `124` 表示超时，`130` 表示中断，`1` 表示执行失败。

正常结束或收到 ACK，都不代表手机已采用目标坐标。结束发送后让用户断开 USB、重新请求真实位置，再检查功能状态。脚本没有“恢复真实 GPS 坐标”能力。

## 恢复上游原配件标识

```powershell
python scripts/apply-upstream-identity.py .\iap2-location-bridge-windows\src\iap2_location_bridge_windows\profile.py
```

仅修改前述固定版本中六项配件描述，核对完整源码哈希；重复执行不会再次改动。未知内容拒绝写入。使用定位入口的 `--upstream-identity` 可在运行时完成等效替换，不必同时修改文件。

## iloader 的单进程代理

先完全退出 iloader，使用实际安装路径与本机 HTTP 代理地址：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-IloaderWithProxy.ps1 -Executable E:\application\iloader\iloader.exe -ProxyUri http://127.0.0.1:10808
```

这个路径和端口是历史实例，应换成本机真实配置。`-CheckOnly` 只验证参数，不启动工具。脚本使用 ASCII，兼容 Windows PowerShell 5.1；只在子进程设置代理，不持久写环境变量、不改变系统全局代理、不跳过 TLS 校验。

## 离线验证

```powershell
python -m unittest discover -s tests -v
```

测试使用合成 plist、模拟手机接口与短命测试进程，核对差分、隐私输出、无效坐标、默认计划不导入 USB、取消清理和进程树超时回收。不会登录账号、安装 App 或连接设备。
