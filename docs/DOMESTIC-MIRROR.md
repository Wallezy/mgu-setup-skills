# 备用源维护与自建分发 / Backup-source maintenance

本文面向维护者。用户只选择[国内版或官方版](../skills/mgu-setup/references/store-distributions.md#choose-edition)；
官方版按网络使用直连或备用源，不再让用户选择“国内镜像版”。这里的“镜像”仅为内部维护术语。

自建 C 入口、A 主源和 B 备用源的发布接入见
[维护者发布传输](PUBLICATION-TRANSPORT.md)。直接向 A/B 发布，C 入口验收通过后才记录公开发布成功。
源码、文档和 Skill 放 GitHub/Gitee，官方原包及目录放自建 A/B 节点；CN 发行版使用独立发布流程。
备用源资源不代表实车验证结果。

备用源公开根地址：`https://mgu.walle.pw/mgu/`。商店读取
`mgu-store/catalog.json`，应用读取 `idrive-apps/catalog.json`。
历史 OSS 文件保留，不参与新发布、同步或自动回退。

## 用户选择

- 国内优先：`domestic-first`，先使用 Gitee 源码与备用源资源。
- 官方优先：`upstream-first`，先使用上游 GitHub。
- 自动：`auto`，先检查官方目录，再尝试配置过的备用源。

不通过 IP、界面语言或时区判断所在地。`auto` 只检查目录，下载的每个包仍需完整校验。发生回退时，记录原因、实际来源和版本。源不可达不能成为跳过校验或安装其他版本的理由。

给 AI 的示例：

> 使用 mgu-setup，设置为国内优先。先下载并校验本次所需资源，车辆未连接时只完成本地准备。

## 维护者生成上传资源

需要 Python 3.9+ 和 curl，使用系统证书校验 HTTPS；本阶段须能够访问 GitHub 官方发布资源。以下命令从本仓库根目录运行：

```text
python tools/prepare_oss.py --output <仓库外的新目录>/mirror-upload --cache <仓库外目录>/cache
python skills/mgu-setup/scripts/mirror_resources.py verify <仓库外的新目录>/mirror-upload
```

脚本读取两项目的正式发布目录，保存上游版本、提交、目录和来源信息，下载已发布的全部组件，校验每个包的大小、SHA-256、归档路径及 SDK 排除项，核对跨仓库依赖。包和图标使用带 SHA-256 的目录，不覆盖既有内容。目录及图标须匹配官方 Release 附件的大小和 SHA-256；图标仅接受同一 catalog Release 的 PNG 文件名，检查格式、块校验和、尺寸及 1 MiB 大小上限，保留原始字节。缺包、缺失附件摘要、外部图标地址、依赖不满足或校验失败时停止生成。

输出包括：

```text
mirror-upload/
  mirror-manifest.json
  NOTICE.txt
  bootstrap/mgu-install.js
  mgu-store/catalog.json
  mgu-store/upstream-catalog.json
  mgu-store/packages/<sha256>/<id>@<version>.tgz
  mgu-store/icons/<sha256>/<name>.png
  mgu-store/source/<commit>.zip
  mgu-store/LICENSE
  mgu-store/README.md
  idrive-apps/...
```

`catalog.json` 只把安装包和图标 URL 改为目录内相对路径，保留其他字段及原始字节。`upstream-catalog.json` 和上游 README 中的 GitHub 链接用于溯源。`mirror-manifest.json` 记录上传文件的大小、哈希和图标的官方来源；其哈希应单独保存，上传验收时用于固定本次快照。同版本图标的官方摘要发生变化，也会触发镜像更新。

SSH 工具源码从已知 Gitee 镜像获取，并核对上游版本及实际内容。不把本地 root 凭据、车辆数据、BMW SDK、固件资产或捐赠包上传公共下载源。

## 自建发布

使用下方 `sync_mirror.py` 事务发布。A/B 保存完整快照和文件校验清单；C 在两边验证通过后切换。
`prepare_oss.py` 保留历史文件名，只生成本地资源，不连接或依赖 OSS。
发布保留旧包及候选清单，供既有下载和恢复使用；不删除历史文件。
原生安装器/更新服务使用稳定 HTTPS 地址，不需要登录、Cookie 或过期签名链接。

## 地址确定后的配置和验收

```text
python skills/mgu-setup/scripts/mirror_resources.py configure --base-url <实际HTTPS根地址>
python skills/mgu-setup/scripts/mirror_resources.py fetch --base-url <实际HTTPS根地址> --output <新的验收目录> --manifest-sha256 <本地清单SHA256>
```

仓库默认保持 `auto`，方便海外用户优先官方源。国内用户可加 `--preference domestic-first` 保存自己的偏好。验证通过后重新打包 Skill，发布更新后的配置到 GitHub/Gitee；安装资源不必因为配置了根地址而重新上传。

用下载后的原版安装器在本机执行 `usb-repo` 转换，校验官方离线输入兼容性；此命令不接触车辆。实际车端安装及 UI 添加更新源，按 [网络源流程](../skills/mgu-setup/references/network-mirrors.md)执行。

审阅的 Store 提交 `efbdcc0d68bd7faf5c5939fa6240050e5e3a449f` 的 `usb-repo`
只复制安装包，保留图标字段但不复制 PNG。在线目录和完整镜像快照含图标，
USB 转换的包校验通过不能用来宣称 USB 图标显示已验证；此处保留原版安装器。

## 后续同步

### GitHub → Gitee 源码同步

维护者工具 `tools/sync_gitee.py` 使用本机现有 SSH 身份，不需要个人访问令牌。
首次使用前，两站的主机密钥应已核验并保存在 SSH known_hosts 中，
SSH 身份需要能读取 GitHub 来源并推送到 Gitee 目标。

固定映射：

| GitHub 来源 | Gitee 目标 |
|---|---|
| `Wallezy/mgu-setup-skills` | `walle7/mgu-setup-skills` |
| `robertnisipeanu/mgu-store` | `walle7/mgu-store` |
| `robertnisipeanu/idrive-apps` | `walle7/idrive-apps` |
| `cauliflowermossgrape/idrive7-8-ssh-root` | `walle7/idrive7-8-ssh-root` |

```text
python tools/sync_gitee.py --work-dir <仓库外运行目录>
python tools/sync_gitee.py --work-dir <仓库外运行目录> --publish
```

省略 `--publish` 只比较；可用 `--repo mgu-store` 限定仓库，参数可重复。
默认同步公开来源的**默认分支及全部标签**和对应 Git 历史，使用独立 bare 仓库，不覆盖开发目录、
不检出或执行上游代码，也不上传本机私钥、未提交文件、配置或车辆数据。
不同步 Release 附件、Git LFS 对象、Issue、PR 或仓库设置。Root 仓库的 Git
源码同步与 Root Release/固件资源的公开分发是不同操作。

仅新引用和分支快进允许推送。默认分支有 Gitee 独有提交、同名标签指向不同对象时，
整仓阻断并报告。其余已有工作分支保留，差异列入 `preserved_differences`，
未纳入同步的来源工作分支列入 `excluded_source_refs`；不会因临时分支被上游改写而阻塞
默认分支及正式标签。目标独有引用保留，不删除、不强推。
如确需同步全部分支，显式使用 `--all-branches`，此时任一同名分支的非快进变化仍会阻断整仓。
每仓使用原子推送，
服务器不支持时直接报错，不退回非原子方式。四仓不是一个原子事务，
某仓失败不影响其他独立仓库的结果。

推送前再次比较目标，推送后从 Gitee 读回全部分支和标签：核对本次管理范围与来源一致，
并确认保留的引用未改变。报告中的成功只指所列同步范围，不代表所有工作分支一致。
工作目录的独占锁阻止本机重叠运行；遗留锁须先确认进程状态，不自动清除。
每次写入独立 `result.json` 和 `latest-check.json`，全部选定仓库验收成功才
更新 `latest-success.json`。失败后检查目标实际状态，不盲目重试或强制回滚。

每日维护独立执行源码同步与自建资源同步，分别报告结果。
同步 Skill 已发布提交不等于授权自动提交本地 Skill 修改或推送 GitHub。

## 授权后的 CLI 自动同步 / Authorized CLI synchronization

使用私有 `self-hosted` 配置，详细约定见 [维护者发布传输](PUBLICATION-TRANSPORT.md)。

```text
python tools/sync_mirror.py --work-dir <仓库外运行记录目录> --cache <仓库外下载缓存> --publish
```

- 省略 `--publish` 只准备和比较；`--prepared <目录>` 必须仍与官方正式目录一致。
- 校验线上完整快照、上游目录及正式附件摘要，保留跨仓库依赖和来源证据。
- 只把变化的文件直接传到 A/B，两边完整校验后切换 C。包、图标、源码使用不可变路径；固定目录使用 `no-cache`，PNG 使用正确类型。
- 本机锁与 C 进程锁共同限制并发；当前快照有变化时停止，不覆盖另一项发布。
- 官方同步不能写 CN 路径。历史包保留，不删除 OSS 文件；失败不自动回退 OSS。
- 每次保存 `plan.json`、`result.json` 和事务日志，A/B/C 验收通过才更新 `latest-success.json`。准备成功、公开发布和实车验证分别记录。

独立 Skill 不包含维护者 `tools/`、私有部署驱动或凭据。自动镜像同步不授权车辆更新、CN 功能发布或仓库推送。旧 `sync_oss.py` 仅供明确配置的历史部署；当前自建模式会拒绝执行它。
