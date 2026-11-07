# Existing installation updates / 已安装系统更新

Use existing authorization, private records and verified local resources. Freshly check vehicle identity, current versions and applicable power/backup conditions. Do not restart the first-root workflow or request unchanged confirmations again.

复用授权、私有记录及已验证资源，核对当前车辆和版本；供电/备份条件没有变化时不重复询问。先判断实际传输路径，不默认要求 U 盘或热点。

## Choose by scope / 按更新范围选择

| Scope / 范围 | Supported path / 可用路径 |
|---|---|
| Working Store, usable network / 商店与网络可用 | Prefer the Store/updater for the entire requested set, including the Store itself. Honor source preference; check source/origin ownership, versions and actual artifact reachability. Proxy only when needed. 默认整批走更新器，不先重装商店；镜像可达不等于来源归属兼容。 |
| Store setup/repair or needed offline refresh / 商店初始化、修复或需离线刷新 | Official `first-install --from` sends a verified local Store bundle over ENET, supports rerunning and keeps newer installed versions. No physical USB or HU internet is inherently needed. Its scope excludes arbitrary app catalogs. 可离线更新商店配套组件，但不是其他应用的通用安装器。 |
| Offline app updates / 应用离线更新 | Use complete official `usb-repo` media recognized by the HU, or a version-verified supported local import. A low-level file reader is not an exposed import API. 官方 USB 是可用方案，不是全局前提；仅 ENET 导入须核对真实接口。 |

Before writing, state which components the path covers. If only part is feasible, finish independent preparation and explain the remaining condition. Install only complete, compatible dependency sets; a Store refresh is not an update of every app.

执行前明确路径覆盖范围；部分可行时完成独立准备，安装必须满足完整依赖，不能把“商店已更新”当作“全部应用已更新”。

## Offline means where bytes are read / 离线取决于实际读取位置

Updater 0.8.30 checks the uplink lease before network catalogs and HTTP requests, including proxied ones. Its USB reader bypasses that network check. An OSS HTTPS source is still a network source; packages saved on the computer are not automatically consumed by it. Check this gate before proxy setup. Do not fake a lease/mount, edit updater state or bypass Store with direct deploy.

审阅的 0.8.30 在线源在代理生效前也检查 uplink；电脑有离线包不等于车机在读取它们。不能把该路径的限制概括为“所有更新都需要热点”。没有支持的纯 ENET 应用导入时，说明具体组件与限制，不笼统说整个任务必须用 U 盘。

Store 0.9.30 with updater 0.8.32/uplink 0.7.7 exposes "Phone over USB". Preserve its current value: disabling it can disconnect an active USB phone uplink; it does not disable Wi-Fi. Do not toggle it merely to update apps.

新版“Phone over USB”控制 USB 手机网络接入；关闭可能中断当前 USB 手机链路，不等同于关闭 Wi-Fi。应用更新应保留车主设置。

## One plan, one execution / 一次计划，一次执行

1. Read the saved checkpoint; batch independent read-only identity/status/resource checks. Inventory installed components and dependencies, preserving those without a release source. Reuse same-version review, current confirmations and applicable backups.
2. Select the route and resolve source availability before writing. Catalog access alone does not prove package access. Reuse a working proxy when needed, but revalidate its network assumptions; never copy a historical DNS/IP override into a general recipe.
3. Freeze an execution manifest: current/target versions, source/origin, catalog revision, artifact hashes, dependencies and local paths. For an explicit prepared snapshot, upstream unreachability leaves freshness unconfirmed, not bytes invalid. Resolve a request for "latest" before writing. Afterwards report newer releases as a later update; re-plan only for compatibility, a material safety finding, or user direction.
4. Install only the delta through supported operations in dependency order. Let the updater resolve requirements; observe each result and commit self-updates before proceeding. Do not bootstrap an intermediate Store/updater version and then chase another release. Repeat installation only for documented prerequisites or recovery.
5. Verify target versions, required activation/boot checks, app registration and service health once. Restart when the installed release requires it or a diagnosed fault justifies it. A missing navigation session/starting frame alone does not establish an installation failure or require a whole-HU restart. Report visual testing separately, restore task-only settings and save the checkpoint.

首次写入前锁定目标，执行中不追新；仅安装差异，避免同一组件先后装两版。检查必须覆盖实际依赖与启动验证，但安装验收不等于导航体验测试。没有手机导航画面时注明未目视验证，不默认延长成整机重启和地图排错。记录准备、安装、必要重启及验收耗时，定位重复工作，不承诺固定完成时间。
