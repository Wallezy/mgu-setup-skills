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
- Parked/awake/power state if writing / 写入前停车、唤醒与供电:

## Recovery readiness / 恢复准备

| Category / 类别 | Private location / 私有位置 | Verified coverage and limits / 范围与限制 |
|---|---|---|
| Coding / 编码 | | |
| Access credentials / 登录凭据 | | |
| Deployment snapshot / 部署快照 | | |
| Patch originals / 补丁原件 | | |
| Known-good artifacts / 已知可用安装资源 | | |

## Changes / 操作

### Readiness before planned writes / 计划写入前准备结果

- Requested operation and selected architecture / 操作范围与所选架构:
- Environment profile, interpreter and result / 环境检查模式、解释器及结果:
- Private staging directory / 本地私有资源目录:
- Tools/artifacts/dependencies, source revision, sizes, source checksums and local hashes / 工具安装包依赖、来源提交、长度、来源校验值和本地哈希:
- Archive validation and completeness / 归档检查与资源完整性:
- Vehicle identity/firmware matches prepared resources / 车辆身份及固件是否匹配资源:
- Backup coverage and power confirmed / 备份范围及供电是否满足:
- Transfer route: bootstrap ENET / physical USB / supported updater / other documented route.
- 传输方式：首次安装 ENET／实体 USB／受支持更新服务／其他文档支持路径。
- Ready to perform this operation: yes/no, with missing prerequisites / 是否可开始本次操作、缺失项:

| Step / 步骤 | Source/version/hash / 来源版本哈希 | Result/exit code / 结果退出码 | Recovery route / 恢复路径 |
|---|---|---|---|
| | | | |

## Verification / 验证

- Installed versions and dependencies / 实际版本与依赖:
- Registry, tile and physical UI separately / 注册、入口与屏幕分别记录:
- Patch on disk vs active after boot / 磁盘补丁与启动后生效状态:
- Boot ID continuity, uptime, service failures/restarts / 启动与服务状态:
- Mode/owner and backup verification / 权限、所有者、备份校验:
- Deferred verification and pending restart / 延迟检查与待重启:
- Phone stream, cluster/HUD output and navigation app / 手机流与实际显示:
- Frame rate measurement, if any; otherwise “not measured” / 帧率未测则明确:

## Cleanup and next action / 清理与下一步

- Temporary proxy settings restored / 临时代理已恢复:
- Task-only tunnels/processes closed / 临时隧道进程已关闭:
- Permanent access retained/removed as requested / 永久访问最终状态:
- Owner observation vs machine evidence / 车主观察与机器证据:
- Unresolved issue and concrete next action / 未完成项与明确下一步:
- Overall result: prepared / installed / activated / visually verified / partially complete / blocked.
- 总体结果：准备完成／已安装／已激活／已验证实显／部分完成／条件阻塞。
