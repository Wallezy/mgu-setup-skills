# Session record / 操作记录

Copy this template to a private directory outside the repository. Omit secrets and full VINs from any shareable report.

复制到仓库外的私有目录；公开版本删除凭据、完整 VIN 和其他个人信息。

## Request and baseline / 请求与基线

- Date/time/timezone / 时间与时区:
- Requested endpoint and existing authorization / 终点与授权范围:
- Computer OS, Python, Node, OpenSSH / 本机环境:
- Interface, route and vehicle identity match / 网卡、路由、身份核对结果:
- HU architecture and firmware / 架构与固件:
- Root access, coding state, Store visibility / 初始访问、编码与商店:
- Current apps/native components and source / 初始版本与来源:
- Selected Store edition, active distribution/GitHub capability and package hashes / 商店发行版、实际通道与 GitHub 能力、安装包哈希:
- Distribution switch: current/target edition, exact local installer/bootstrap, per-component identities and retain/migrate/unmapped decisions, supported entrypoint / 整套换版：当前与目标发行版、电脑安装器/引导脚本、逐组件身份及保留/迁移/无对应项、受支持入口:
- Parked/awake/power state if writing / 写入前停车、唤醒与供电:

## Recovery readiness / 恢复准备

| Category / 类别 | Private location / 私有位置 | Verified coverage and limits / 范围与限制 |
|---|---|---|
| Coding / 编码 | | |
| Access credentials / 登录凭据 | | |
| Deployment snapshot / 部署快照 | | |
| Patch originals / 补丁原件 | | |
| Known-good artifacts / 已知可用安装资源 | | |

- Coding backup: matching vehicle/module, format, restore tool and supported restoration route / 编码备份对应车辆与模块、格式、恢复工具和支持的恢复路径:
- Supplemental capture, if used: revision, read consistency, coverage/stop reason; restorability separately confirmed or unknown / 补充采集（如有）：提交、复读一致性、范围/停止原因；可恢复性单独标记已确认或未知:
- Coding recovery readiness: met/unmet with evidence; capture verification alone is insufficient / 编码恢复条件：满足或未满足及依据；采集校验不能单独满足:

## Changes / 操作

### Readiness before planned writes / 计划写入前准备结果

- Requested operation and selected architecture / 操作范围与所选架构:
- Read-only or authorized repair; query entrypoint/version and known side effects / 只读或已授权修复；查询入口、版本及已知副作用:
- Vehicle-side read-only capability and wrapper fallback behavior (repair fallback excluded for read-only requests) / 车端只读能力及包装器回退行为（只读任务禁止修复回退）:
- Environment profile, interpreter and result / 环境检查模式、解释器及结果:
- Private staging directory / 本地私有资源目录:
- Reused snapshot, installer and verified-package manifest paths / 复用快照、安装器及已校验包清单路径:
- Missing/changed resources only; latest-release freshness separately / 仅缺失或变化资源；最新版本查询状态单独记录:
- Frozen execution manifest and lock time: current/target versions, source/origin, catalog revision, hashes, dependencies / 锁定执行清单及时间：当前/目标版本、来源归属、目录提交、哈希与依赖:
- Tools/artifacts/dependencies, source revision, sizes, source checksums and local hashes / 工具安装包依赖、来源提交、长度、来源校验值和本地哈希:
- Archive validation and completeness / 归档检查与资源完整性:
- Vehicle identity/firmware matches prepared resources / 车辆身份及固件是否匹配资源:
- Backup coverage and power confirmed / 备份范围及供电是否满足:
- Transfer route: bootstrap ENET / physical USB / supported updater / other documented route.
- 传输方式：首次安装 ENET／实体 USB／受支持更新服务／其他文档支持路径。
- Where the HU actually reads each package; network requirement and evidence / 车机实际从哪里读取包；联网要求及依据:
- Ready to perform this operation: yes/no, with missing prerequisites / 是否可开始本次操作、缺失项:

| Step / 步骤 | Source/version/hash / 来源版本哈希 | Result/exit code / 结果退出码 | Recovery route / 恢复路径 |
|---|---|---|---|
| | | | |

## Verification / 验证

- Installed versions and dependencies / 实际版本与依赖:
- Registry, tile and physical UI separately / 注册、入口与屏幕分别记录:
- HMI language, Chinese menus/status/errors/log page; untranslated unknown diagnostics / 车机语言、中文菜单/状态/错误/日志页；保留原文的未知诊断:
- Patch on disk vs active after boot / 磁盘补丁与启动后生效状态:
- Boot ID continuity, uptime, service failures/restarts / 启动与服务状态:
- Mode/owner and backup verification / 权限、所有者、备份校验:
- Repairs actually triggered, before/after evidence and manager restarts / 实际触发的修复、前后证据和管理器重启:
- Deferred verification and pending restart / 延迟检查与待重启:
- Phone stream, cluster/HUD output and navigation app / 手机流与实际显示:
- Display target / Off, HUD pop-up preference and active shared/own driver profile / 显示目标或关闭状态、HUD 弹窗偏好、当前共享或个人配置:
- Exported diagnostics and covered time range; unavailable earlier events / 日志导出及覆盖时段；缺失的早期事件:
- Frame rate measurement, if any; otherwise “not measured” / 帧率未测则明确:
- Update acceptance vs optional navigation/visual testing; reason for any restart / 更新验收与导航实显分开；重启原因:
- First same-version edition migration versus a later higher-version update / 首次同版本发行版迁移与后续更高版本升级分别记录:
- Whole-distribution result: installer used, management tools/dependencies/apps covered, unmapped items, settings retained and each component's update source / 整套迁移结果：实际安装器、管理工具/依赖/应用覆盖、无对应项、设置保留及逐组件更新源:
- Phase durations: preparation, install, required restart, verification / 各阶段耗时：准备、安装、必要重启、验收:

## Cleanup and next action / 清理与下一步

- Temporary proxy settings restored / 临时代理已恢复:
- Task-only tunnels/processes closed / 临时隧道进程已关闭:
- Permanent access retained/removed as requested / 永久访问最终状态:
- Owner observation vs machine evidence / 车主观察与机器证据:
- Unresolved issue and concrete next action / 未完成项与明确下一步:
- Overall result: prepared / installed / activated / visually verified / partially complete / blocked.
- 总体结果：准备完成／已安装／已激活／已验证实显／部分完成／条件阻塞。
