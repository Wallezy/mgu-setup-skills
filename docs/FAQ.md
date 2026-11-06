# FAQ / 常见问题

## Is this a one-click flasher? / 是一键刷机程序吗？

It is a skill an agent reads and follows using upstream tools. The environment helper itself never connects to or writes to a car. The agent can execute authorized steps, but physical checks and coding-tool backups may need the owner.

它是 AI 按步骤执行的 skill，不是独立刷机程序。环境脚本不连接或写入车辆；屏幕确认和编码备份可能需要车主完成。

## Is Python enough? / 只需要 Python 吗？

The source SSH workflow uses Python, cryptography and OpenSSH. The direct Store installer also uses Node.js. Current upstream wrapper installers may prepare runtimes; the skill checks the selected route.

源码解锁需要 Python、cryptography 和 OpenSSH；直接运行商店安装器还需要 Node.js，具体由选择的上游流程决定。

## Does it download first? / 会先下载吗？

Planned installs require scoped local resources and verification before vehicle writes. An initial environment check comes first so the download/install tools can run. Read-only identification may happen earlier to select the correct HU architecture.

计划安装先检查本机环境，再下载本次资源及依赖并校验，满足条件后才写入。为了选择正确架构，可以提前只读识别车辆。

## Must I root again for an update? / 更新时需要重新 root 吗？

No. If existing root access works, skip bootstrap. Store updates and a missing app tile are not reasons to repeat SSH flashing.

已有 root 访问正常就跳过首次设置。更新商店或恢复入口，不应重复刷写 SSH。

## Can the computer download for an offline car? / 车机不能访问 GitHub 怎么办？

Prepare official offline resources on the computer. Bootstrap can use the verified local Store folder over ENET; later apps can use physical USB media through the Store. A supported reachable proxy is another option. A computer folder alone is not a car USB source.

电脑可以准备官方离线资源；首次安装通过 ENET 传输本地商店资源，后续应用可使用实体 USB 媒体或受支持代理。电脑目录不会自动变成车机 USB 源。

## Are all “installed” components launchable? / 已安装的组件都有入口吗？

No. Renderers and native helpers are background services. Check the app's own registration and tile separately.

渲染器、底层工具是后台服务，本来就没有入口。应单独检查用户应用的注册和图标。

## Does installation guarantee HUD video? / 安装成功就代表 HUD 出图吗？

No. Patch activation, a normal restart, display selection and a compatible phone navigation stream are separate checks. HUD support is experimental upstream. This repository does not certify every map app or frame rate.

还需核对补丁激活、正常重启、显示位置和手机导航视频流。HUD 属上游实验性功能，本仓库不保证所有地图软件或固定帧率。

## Can I always downgrade or recover? / 一定能降级或救回来吗？

No. Recovery depends on reachable maintenance access, compatible retained packages, valid backups and the installed tool's capabilities. Coding backups, deployment snapshots and patch originals cover different things; none is a complete firmware image. See [recovery decisions](../skills/mgu-setup/references/recovery.md).

恢复取决于维护通道、保留包、备份与工具能力。编码、部署快照和补丁原件的覆盖范围不同，均不等同于完整固件镜像。

## What is actually tested? / 实际验证到哪一步？

See [evidence](../skills/mgu-setup/references/evidence.md) and [validation](../VALIDATION.md). The recorded vehicle session was macOS + ENET + iDrive 7. Cross-platform CI checks repository software, not a car.

实车记录来自 macOS + ENET + iDrive 7。跨平台 CI 验证的是仓库代码与文档，不是实车兼容性。
