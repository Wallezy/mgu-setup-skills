# 备用源维护与 OSS 分发 / Backup-source maintenance

本文面向维护者。用户只选择[国内版或官方版](../skills/mgu-setup/references/store-distributions.md#choose-edition)；
官方版按网络使用直连或备用源，不再让用户选择“国内镜像版”。这里的“镜像”仅为内部维护术语。
源码、文档和 Skill 放 GitHub/Gitee，官方原包及目录放 OSS；CN 发行版使用独立发布流程。
备用源资源不代表实车验证结果。

国内镜像公开根地址：`https://mgu.walle.pw/mgu/`，存储目标为杭州
`oss://walle-mgu/mgu/`。商店读取 `mgu-store/catalog.json`，应用读取
`idrive-apps/catalog.json`。北京旧前缀保留原文件供现有客户端使用，
后续维护以杭州为目标；保留不表示两地持续同步。

## 用户选择

- 国内优先：`domestic-first`，先使用 Gitee 源码与 OSS 资源。
- 官方优先：`upstream-first`，先使用上游 GitHub。
- 自动：`auto`，先检查官方目录，再尝试配置过的 OSS。

不通过 IP、界面语言或时区判断所在地。`auto` 只检查目录，下载的每个包仍需完整校验。发生回退时，记录原因、实际来源和版本。源不可达不能成为跳过校验或安装其他版本的理由。

给 AI 的示例：

> 使用 mgu-setup，设置为国内优先。先下载并校验本次所需资源，车辆未连接时只完成本地准备。

## 维护者生成上传资源

需要 Python 3.9+ 和 curl，使用系统证书校验 HTTPS；本阶段须能够访问 GitHub 官方发布资源。以下命令从本仓库根目录运行：

```text
python tools/prepare_oss.py --output <仓库外的新目录>/oss-upload --cache <仓库外目录>/cache
python skills/mgu-setup/scripts/mirror_resources.py verify <仓库外的新目录>/oss-upload
```

脚本读取两项目的正式发布目录，保存上游版本、提交、目录和来源信息，下载已发布的全部组件，校验每个包的大小、SHA-256、归档路径及 SDK 排除项，核对跨仓库依赖。包和图标使用带 SHA-256 的目录，不覆盖既有内容。目录及图标须匹配官方 Release 附件的大小和 SHA-256；图标仅接受同一 catalog Release 的 PNG 文件名，检查格式、块校验和、尺寸及 1 MiB 大小上限，保留原始字节。缺包、缺失附件摘要、外部图标地址、依赖不满足或校验失败时停止生成。

输出包括：

```text
oss-upload/
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

SSH 工具源码从已知 Gitee 镜像获取，并核对上游版本及实际内容。不把本地 root 凭据、车辆数据、BMW SDK、固件资产或捐赠包上传公共 OSS。

## OSS 上传

1. 把 `oss-upload` **里面的内容**上传到所选 OSS 前缀，保留相对目录结构。
2. 对使用者提供稳定 HTTPS 读取；不依赖登录页面、Cookie、防盗链 Referer 或会过期的签名链接。
3. 包、图标及 source 压缩包先上传并验证；固定路径元数据及两个 `catalog.json` 接着上传；根 `mirror-manifest.json` 最后上传。
4. `packages/<sha256>/`、`icons/<sha256>/` 和按提交命名的源代码 ZIP 使用 `Cache-Control: public,max-age=31536000,immutable`；PNG 使用 `Content-Type: image/png`。目录、根清单及其他可替换固定路径使用 `Cache-Control: no-cache`，并按 CDN 配置刷新。
5. 首次上线可直接上传到一个新前缀。维护更新时保留旧包供已开始的下载使用，不删除用户可能需要的恢复资源。

仅原生安装器/更新服务下载不需要 CORS。OSS 根地址是 `mirror-manifest.json` 所在目录的 HTTPS 地址，不是控制台地址、桶管理地址或单个包的链接。

## 地址确定后的配置和验收

```text
python skills/mgu-setup/scripts/mirror_resources.py configure --base-url <实际HTTPS根地址>
python skills/mgu-setup/scripts/mirror_resources.py fetch --base-url <实际HTTPS根地址> --output <新的验收目录> --manifest-sha256 <本地清单SHA256>
```

仓库默认保持 `auto`，方便海外用户优先官方源。国内用户可加 `--preference domestic-first` 保存自己的偏好。验证通过后重新打包 Skill，发布更新后的配置到 GitHub/Gitee；安装资源不必因为配置了根地址而重新上传。

用下载后的原版安装器在本机执行 `usb-repo` 转换，校验官方离线输入兼容性；此命令不接触车辆。实际车端安装及 UI 添加更新源，按 [网络源流程](../skills/mgu-setup/references/network-mirrors.md)执行。

审阅的 Store 提交 `efbdcc0d68bd7faf5c5939fa6240050e5e3a449f` 的 `usb-repo`
只复制安装包，保留图标字段但不复制 PNG。OSS 在线目录和完整镜像快照含图标，
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
源码同步与 Root Release/固件资源的 OSS 分发是不同操作。

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

每日维护先独立执行源码同步，再执行 OSS 包同步，分别报告结果。
同步 Skill 已发布提交不等于授权自动提交本地 Skill 修改或推送 GitHub。

### OSS 发布资源同步

每次同步先生成新的完整快照，验证后先上传缺少的不可变包和图标，再更新两个目录，最后更新根清单。需要更强的发布隔离时，使用按快照命名的 OSS 前缀并在验证后切换 Skill 的根地址。Gitee 代码同步成功不代表 OSS 资源同步成功。

交付增量上传文件时，先验证实时 OSS 快照，再按路径、大小及 SHA-256 与新快照比较。清单应列出新增包、图标、源码归档及需要替换的固定路径文件。未变化文件可以省略，但不能只提供引用尚未上传资源的新目录。固定路径的 `upstream-catalog.json`、README、安装器如有替换，也使用 `no-cache`；带哈希的资源及按提交命名的源码归档使用上述长期缓存。

两个目录与根清单分开上传，发布窗口内避免安装或更新，上传完再执行远端验收。新资源本地准备成功不代表线上更新完成，也不代表已经实车测试。

`prepare_oss.py` 只准备本地资源。需要自动上传时，使用下方独立的维护者工具；它不提交仓库，也不执行车端安装。

## 授权后的 CLI 自动同步 / Authorized CLI synchronization

仓库提供 `tools/sync_oss.py`，使用维护者安装的官方 ossutil v2。凭据通过仓库外的专用 ossutil 配置文件读取；POSIX 系统要求配置权限仅当前用户可读。不要把 AccessKey 写进命令行参数、自动任务提示、仓库或报告。

```text
python tools/sync_oss.py --ossutil <ossutil可执行文件> --config <仓库外私有配置> --destination oss://<bucket>/<prefix> --base-url https://<bucket>.oss-<region>.aliyuncs.com/<prefix>/ --work-dir <仓库外运行记录目录> --cache <仓库外下载缓存> --publish
```

- 省略 `--publish` 只准备、比较和验证，不上传；`--prepared <目录>` 可使用已准备快照，但必须仍与官方发布目录一致。
- 自定义域名只接受 `sync_oss.py` 中明确配置的域名、桶、前缀和地域映射；
  发布前通过 OSS API 核对桶上的域名绑定与启用的证书，公开读取仍须通过真实 TLS 校验。
  不关闭目标校验来支持任意域名。执行身份需要读取目标桶 CNAME 的权限。
- ossutil 调用明确设置目标地域、API Endpoint 和 `--retry-times 1`，
  不依赖旧配置中的北京地域；本机 2.2.0 的零尝试设置可触发 SDK 空指针崩溃。
- 每次读取并校验线上快照，再检查两个官方发布目录及图标附件摘要。版本、目录、图标一致，所有缓存头和 PNG 类型正确时报告 `unchanged`，不重新上传。
- 先上传变化的版本化资源并下载验收，再更新固定路径文件，最后更新根清单。固定路径使用 `no-cache`，带哈希/提交号资源使用长期缓存；不删除旧包、不修改 ACL 或桶策略。
- 既有不可变资源缺少缓存头时，可用已验证的相同字节重新上传以修复头部，包括上次清单中本次不再引用的历史包；禁止改变不可变路径的内容。
- 完成后重新下载全部清单文件，校验 SHA-256、依赖、图标格式、缓存头和 PNG 类型；历史资源头部修复也需单独下载验收。发布中失败则尝试恢复此前验证过的可变文件和清单，验收回滚结果；不删除已上传但未被引用的新包。
- 工作目录使用独占锁，防止本机任务重叠。进程意外终止留下锁时，先确认没有运行中的同步，再人工处理；不自动忽略锁。
- 每次保存 `plan.json`、`result.json`；成功后更新 `latest-success.json`。发布不是多对象原子操作，执行期间避免安装；多个维护者应协调发布窗口。

可由本机定时任务或 CI 在明确授权后调用。任务只自动同步这个镜像目标，验证后再提出 Skill 适配建议；提交代码、发布评论和操作车辆属于不同授权。CLI 与私有配置需在执行机器上可用。独立 Skill 压缩包不包含仓库 `tools/` 或凭据。
