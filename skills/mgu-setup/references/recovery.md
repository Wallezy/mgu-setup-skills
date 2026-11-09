# Recovery and rollback / 恢复与回滚

Use this reference for failures, downgrade, restore or removal. Confirm the current installed tool's behavior before applying an action described here. See [evidence.md](evidence.md) for reviewed sources.

故障、降级、还原或卸载时读取本文；执行前核对车上实际工具能力。来源见 [evidence.md](evidence.md)。

## Diagnose before changing / 先诊断

| Observation / 现象 | Decision / 判断 |
|---|---|
| No ENET link / 无有线链路 | Inspect cable, dock, interface and power; do not flash. 检查线缆、拓展坞、网卡和供电，不刷写。 |
| ENET linked, discovery empty / 有链路但发现为空 | Check the selected Root version: v1.3.1 restores Windows broadcast fallbacks and retains macOS/Linux discovery fixes. Use [Root preparation](root-tool.md) before diagnosing missing SSH. 先核对工具版本和路由，不把发现失败当成需要刷写。 |
| Port timeout / 端口超时 | Distinguish route/wake/firewall from absent SSH. 区分路由、唤醒、防火墙和 SSH 未启用。 |
| Changed host key / 主机密钥变化 | Verify physical interface, fresh vehicle identity and expected restart before accepting a new key. 核实接口、车辆身份与重启过程，不能直接关闭校验。 |
| Public key rejected / 公钥拒绝 | Distinguish local `Load key: Permission denied` from server rejection; v1.3.0 fixes Windows key-file permissions. Match key/enrollment and selected user. 区分本地读不到密钥和服务端拒绝，不能因一次失败就 fix-key。 |
| Store recorded, no entry / 有安装记录无入口 | Check registry, tile/fallback and manager health; use official repair. 检查真实注册、入口和管理器，再用官方流程恢复。 |
| Tile exists, name missing / 入口存在但名称消失 | Store 0.9.29 and map app 0.6.2 include a manager-owned tile-name fix. This does not diagnose an absent tile. 该修复针对应用被管理器停止后的名称丢失，不等同于修复所有入口缺失。 |
| Needs setup after firmware update / 固件更新后需要设置 | Use the installed Store's Set up action and inspect its result/restart request. 使用当前商店设置动作；不是再次解锁 SSH 或强制恢复旧系统文件的理由。 |
| “Installed” tool has no launcher / 工具无入口 | Background services such as renderers do not need tiles. 渲染器等后台服务本来就没有入口。 |
| Startup animation repeats / 开机动画重复 | Compare boot IDs, uptime and service process/restart evidence. 动画重复本身不能证明整机重启。 |
| Coding restored, still unstable / 恢复编码后仍异常 | Coding restore cannot repair modes, patched executables or services. 继续区分文件、补丁和服务问题。 |
| Map missing / 无地图 | Inspect patch, pending restart, phone stream, output selection and renderer. 不能直接归因于安装失败。 |
| Download stalls / 下载停滞 | Test exact asset, change to official offline media or supported proxy; keep verified completed stages. 测试实际资源，换官方离线包/代理，不重做已验证步骤。 |

Avoid invoking an unknown daemon with guessed arguments. In this case `patchd.js status` started another daemon; inspect documented read-only entrypoints instead.

不能猜测守护进程的状态参数。案例中 `patchd.js status` 启动了第二个进程；应使用已确认的查询入口。

### Read-only status versus repair / 只读检查与修复

In reviewed deploy **0.8.8**, `status` calls `syncMgrHome()`. As root, when
MainApp's home is incorrectly root-owned, it repairs directory ownership/modes,
waits for the manager on ID7, may restart it, or saves a pending-restart state.
Other status reconciliation steps can also write. `--json` changes output, not
these side effects. This is conditional app-manager recovery, not an unconditional
head-unit reboot. Source: `deploy/unit/mgu-deploy.js` at Store commit
`ed9393a980743ddbe1933eed006c706c943d71e0`.

审阅的 deploy **0.8.8** 在 root 身份下执行 `status`，可能修复 MainApp 目录所有者/
权限、等待或重启应用管理器，或保存待重启状态；其他状态协调步骤也可能写入。
`--json` 不会变成只读模式。这是有条件的应用管理器恢复，不是每次都重启整台车机。

- A read-only request excludes this entrypoint and any wrapper/polling path that
  calls it. Use already-reviewed passive observations of boot IDs, uptime,
  processes, logs and file metadata through available supported tools.
  If none is available, report the observation as unavailable; do not try
  guessed flags or silently repair. 只读请求不得调用此入口或后台自动轮询它；
  使用已核对的被动观察方式，不可用就说明限制，不隐含修复。
- For an authorized repair/install, capture the relevant before-state first,
  run the supported operation once and record actual directory/service changes
  and pending restarts. Reuse existing authorization when it covers that repair;
  a diagnostic-only request does not. 已授权修复时先保留现场，记录实际修改及重启需求，
  不因该规则重复索取已有授权。

Root v1.3.0+ includes bounded retries for specific post-reset diagnostic-session
delays and a non-fatal busy enrollment readback. A final failure still stops
the workflow; these changes do not authorize automatically repeating flash.
Check activation, fresh SSH login and persistence separately. See [Root preparation](root-tool.md).

Root v1.3.0+ 对特定复位后诊断延迟和登记读回忙状态有内置处理；最终失败仍须停下分析，
不能自动从头重刷。激活成功、SSH 登录、持久化分别验收。

If BimmerCode reports a successful restore but individual settings remain reset,
the reviewed Root README describes incomplete coding restoration on some units.
Assess the matching saved CAFD/NCD and the supported E-Sys coding path; do not
diagnose every missing tile or boot problem as coding loss, and do not reflash
to restore coding. This skill does not provide an E-Sys implementation.

BimmerCode 提示恢复成功但部分设置仍重置时，上游记录了编码恢复不完整的可能性。
核对匹配的 CAFD/NCD 和 E-Sys 编码恢复条件；不能把所有入口/启动问题归为编码，也不能靠重刷补编码。

## Four different recovery scopes / 四种恢复范围

| Scope / 范围 | Supported approach and boundary / 方法与边界 |
|---|---|
| Coding / 编码 | Restore the matching HU/MGU pre-flash backup through a compatible coding tool. It is not file/firmware recovery. 使用匹配的刷写前编码备份，不等同于文件或固件恢复。 |
| Component / 组件 | Store/updater rollback to an available compatible retained version. Does not choose arbitrary historical releases. 回到可用且兼容的保留版本，不是任意选旧版。 |
| Map patch / 地图补丁 | App Remove patch or the supported tool removal path verifies/restores originals. CarPlay and Android Auto are separate. 经应用或上游移除流程恢复已校验原件，两个补丁分别判断。 |
| Firmware / 固件 | Not implemented by this skill or these Store backups. Escalate to a verified vehicle-programming recovery process when necessary. 不提供整机固件降级/救砖，必要时转专业编程恢复。 |

### Component rollback

At the reviewed mgu-deploy 0.8.3:

- Native tools switch to a retained other version. Missing/ambiguous candidates can be refused. Inspect activation/deactivation and dependency changes.
- iDrive 7 apps can return to the newest retained older package. The manager rejects an in-place downgrade, so the deploy tool removes/reinstalls while carrying data; if installation fails it attempts to reinstall the original current package.
- iDrive 8 app rollback is refused in this implementation. Do not extrapolate iDrive 7 behavior.
- Updater rollback requests perform dependency checks. Use the Store action or documented updater request for the installed release, not a manual `current` symlink swap.

审阅的 mgu-deploy 0.8.3 支持底层工具回到保留版本，及 iDrive 7 应用卸载后重装保留的最新旧包并迁移数据；iDrive 8 应用回滚被拒绝。较旧工具能力不同。优先使用商店/更新服务的回滚动作及依赖检查，禁止手改 `current` 链接冒充回滚。

Before rollback, confirm:

1. The requested scope and exact current/target version.
2. The target artifact/retained directory exists, matches the HU and is not a known-bad build for this vehicle.
3. Dependencies and data compatibility allow returning; preserve current recoverable resources before mutation.
4. The selected updater exposes this action and explains any refusal.

回滚前核对范围、当前/目标版本、资源存在、车型与依赖兼容、数据兼容和已知问题。**不能把导致过该车故障的旧版本作为默认恢复目标**；不可用时保留可用系统，说明缺少的条件。

### Deployment snapshot restore

Snapshot `stock` means paths covered by the first deployment snapshot, not complete factory firmware. The reviewed implementation does not copy all app data or tool version folders; sources/credentials have separate ownership, and a later installed component may require its own removal. Restore can be refused if retained versions are gone or required relationships would break.

Snapshots record firmware. Restores writing outside `/var/opt` require the recorded firmware to match in the reviewed implementation. After a firmware update, use the documented setup removal/repair path, not stale system-file snapshots.

`stock` 不是整机出厂镜像。快照不覆盖所有应用数据或工具版本目录，软件源/凭据也有独立规则。跨固件写回系统文件可能被拒绝，不能强行绕过。具体覆盖范围必须查看对应快照清单。

Do not call snapshot restore directly unless the current supported maintenance path and applicable local instructions permit it. If the Store is unavailable, first assess official bootstrap/repair. Do not invent a recovery component on the live car.

快照还原须走当前允许的维护路径。商店不可用时先评估官方修复，不临时编写救援组件在实车试运行。

## Driver settings and map diagnostics / 驾驶员设置与地图诊断

With map service 0.9.3, include both effective `map.state.conf` and, when present, `/var/opt/waze-on-cluster/profiles.json` in the configuration backup inventory. Confirm the installed version, actual paths and export coverage through supported maintenance tools; a deployment snapshot does not imply these files were saved. Keep profile identifiers private. No opted-in driver may mean no profile file; absence alone is not corruption.

地图服务 0.9.3 的配置备份清单应同时考虑当前生效的 `map.state.conf` 和实际存在的 `/var/opt/waze-on-cluster/profiles.json`。核对当前版本、路径及受支持工具的导出范围，不能默认部署快照已经覆盖。驾驶员标识私有保存；未启用独立设置时可能没有配置文件，不能直接判断损坏。

Older 0.9.x reads the effective settings, but changes made there while a driver has its own settings can be replaced by `profiles.json` at the next start of a profile-aware version. Record shared/own state and preserve both files before an authorized downgrade. Use supported UI/maintenance actions; do not delete the profile file or hand-edit it to force a reset.

旧版 0.9.x 仍可读取当前生效设置，但在驾驶员独立设置启用期间降级并修改配置，再启动支持该功能的版本时，改动可能被 `profiles.json` 覆盖。降级前记录共享/个人状态及备份；不以删除或手改配置文件作为默认恢复办法。

Map service 0.9.2 adds diagnostics to exported logs and `probe.txt`: stream SPS, decoder output order, frame completion by marker/next timestamp, assembly delay and decoder-held frames. Use the current app's supported log export and compare the same phone/navigation/output combination. Missing fields can reflect an unmeasured stream path, not a fault. This release's logging and renderer 0.4.2's layer capacity are not evidence of higher frame rate.

地图服务 0.9.2 起的日志和 `probe.txt` 可区分帧组装等待与解码缓冲；使用当前应用支持的导出入口，记录同一手机、导航和显示目标组合。未测量的路径可能不输出某些字段，不能据此认定故障；图层容量增加和诊断增强都不等于帧率提升。

## Boot instability and executable permissions / 启动异常与权限

Capture boot IDs, uptime, service results, relevant crash/manager logs, current versions and verified original hashes/modes when reachable. Check whether a boot recovery already restored a patch. A reconnect is not proof that recovery finished.

In the earlier case, original CarPlay bytes with a non-executable-for-service mode were a material failure mechanism. That does not prove every loop is a permission bug. The successful session checked 0755 on carplay/aapd, stable processes and the upstream deferred verification result.

此前案例中，原始 CarPlay 字节配上不适合服务执行的权限，是重要故障机制；不能推断所有循环启动都由权限导致。成功会话核对了文件权限、进程稳定和上游启动验证结果。

Use current upstream patch removal/recovery that verifies file provenance and preserves mode/owner. Do not blindly chmod unidentified files, overwrite another firmware's binary, stop/restart critical projection services or repeatedly request resets. If the current supported recovery fails, stop that write path, preserve evidence and identify the next supported option.

使用会验证来源并保留权限/所有者的上游恢复流程。不对未知文件盲目 chmod，不跨固件覆盖，不反复重启关键投屏服务。恢复失败后停止该写入路径并留存证据。

If SSH is lost, first diagnose access. Reflashing SSH is not a file rollback. If no supported maintenance access remains and the HU cannot stay up, report that this skill cannot execute firmware rescue and identify required professional tools/help.

SSH 丢失先排查访问；重刷 SSH 不等于回滚文件。没有维护通道且车机无法稳定启动时，应明确当前无法执行固件救援。

## Removal order / 移除顺序

1. Clarify whether the owner wants only the map, a component, all Store-managed software, or SSH itself removed.
2. Remove map patches through the app when applicable; verify originals and restart state. If removing the app/tool, follow current Store dependency order (normally app, then unused tool).
3. Use official Store/component removal. Check deactivation success; do not delete version folders manually.
4. Full official Store uninstall has a larger blast radius and can remove apps/tools, updater data and deployment backups. Inventory/export needed recovery resources first and require that scope in the owner's request.
5. Remove persistent SSH last, only if requested, after other verification is complete. It may end the remaining maintenance connection.

只撤销地图补丁、卸载地图组件、移除整套商店和关闭 SSH 是不同范围。先确认终点，按依赖移除，保留必要备份；关闭 SSH 放最后。不能把卸载所有内容作为默认排错动作。
