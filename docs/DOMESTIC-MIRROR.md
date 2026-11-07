# 国内镜像与 OSS 分发 / Domestic mirror distribution

同一份中英文 Skill 同时支持官方源和国内镜像。源码、文档和 Skill 放 GitHub/Gitee，正式安装包和目录放 OSS。镜像资源不是经过实车验证的版本推荐。

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

脚本读取两项目的正式发布目录，保存上游版本、提交、目录和来源信息，下载已发布的全部组件，校验每个包的大小、SHA-256、归档路径及 SDK 排除项，核对跨仓库依赖。包使用带 SHA-256 的目录，不覆盖既有快照。发现缺包、依赖不满足、非预期外部图标字段或校验失败，停止生成完整上传目录。

输出包括：

```text
oss-upload/
  mirror-manifest.json
  NOTICE.txt
  bootstrap/mgu-install.js
  mgu-store/catalog.json
  mgu-store/upstream-catalog.json
  mgu-store/packages/<sha256>/<id>@<version>.tgz
  mgu-store/source/<commit>.zip
  mgu-store/LICENSE
  mgu-store/README.md
  idrive-apps/...
```

`catalog.json` 只把资源下载 URL 改为目录内相对路径，保留其他字段及安装包字节。`upstream-catalog.json` 和上游 README 中的 GitHub 链接用于溯源。`mirror-manifest.json` 记录上传文件的大小和哈希；其哈希应单独保存，上传验收时用于固定本次快照。

SSH 工具源码从已知 Gitee 镜像获取，并核对上游版本及实际内容。不把本地 root 凭据、车辆数据、BMW SDK、固件资产或捐赠包上传公共 OSS。

## OSS 上传

1. 把 `oss-upload` **里面的内容**上传到所选 OSS 前缀，保留相对目录结构。
2. 对使用者提供稳定 HTTPS 读取；不依赖登录页面、Cookie、防盗链 Referer 或会过期的签名链接。
3. 包文件及 source 压缩包先上传；两个 `catalog.json` 接着上传；根 `mirror-manifest.json` 最后上传。
4. `packages/<sha256>/` 和按提交命名的源代码 ZIP 可长缓存。`catalog.json` 与 `mirror-manifest.json` 使用 `Cache-Control: no-cache` 或短缓存，并按 CDN 配置刷新。
5. 首次上线可直接上传到一个新前缀。维护更新时保留旧包供已开始的下载使用，不删除用户可能需要的恢复资源。

仅原生安装器/更新服务下载不需要 CORS。OSS 根地址是 `mirror-manifest.json` 所在目录的 HTTPS 地址，不是控制台地址、桶管理地址或单个包的链接。

## 地址确定后的配置和验收

```text
python skills/mgu-setup/scripts/mirror_resources.py configure --base-url <实际HTTPS根地址>
python skills/mgu-setup/scripts/mirror_resources.py fetch --base-url <实际HTTPS根地址> --output <新的验收目录> --manifest-sha256 <本地清单SHA256>
```

仓库默认保持 `auto`，方便海外用户优先官方源。国内用户可加 `--preference domestic-first` 保存自己的偏好。验证通过后重新打包 Skill，发布更新后的配置到 GitHub/Gitee；安装资源不必因为配置了根地址而重新上传。

用下载后的原版安装器在本机执行 `usb-repo` 转换，校验官方离线输入兼容性；此命令不接触车辆。实际车端安装及 UI 添加更新源，按 [网络源流程](../skills/mgu-setup/references/network-mirrors.md)执行。

## 后续同步

每次同步先生成新的完整快照，验证后先上传缺少的不可变包，再更新两个目录，最后更新根清单。需要更强的发布隔离时，使用按快照命名的 OSS 前缀并在验证后切换 Skill 的根地址。Gitee 代码同步成功不代表 OSS 资源同步成功。

交付增量上传文件时，先验证实时 OSS 快照，再按路径、大小及 SHA-256 与新快照比较。清单应列出新增包、源码归档及需要替换的固定路径文件。未变化文件可以省略，但不能只提供引用尚未上传安装包的新目录。固定路径的 `upstream-catalog.json`、README、安装器如有替换，也使用 `no-cache`；带哈希的包及按提交命名的源码归档可长期缓存。

两个目录与根清单分开上传，发布窗口内避免安装或更新，上传完再执行远端验收。新资源本地准备成功不代表线上更新完成，也不代表已经实车测试。

`prepare_oss.py` 只准备本地资源。需要自动上传时，使用下方独立的维护者工具；它不提交仓库，也不执行车端安装。

## 授权后的 CLI 自动同步 / Authorized CLI synchronization

仓库提供 `tools/sync_oss.py`，使用维护者安装的官方 ossutil v2。凭据通过仓库外的专用 ossutil 配置文件读取；POSIX 系统要求配置权限仅当前用户可读。不要把 AccessKey 写进命令行参数、自动任务提示、仓库或报告。

```text
python tools/sync_oss.py --ossutil <ossutil可执行文件> --config <仓库外私有配置> --destination oss://<bucket>/<prefix> --base-url https://<bucket>.oss-<region>.aliyuncs.com/<prefix>/ --work-dir <仓库外运行记录目录> --cache <仓库外下载缓存> --publish
```

- 省略 `--publish` 只准备、比较和验证，不上传；`--prepared <目录>` 可使用已准备快照，但必须仍与官方发布目录一致。
- 每次读取并校验线上快照，再检查两个官方发布目录。版本和目录一致、缓存头正确时报告 `unchanged`，不重新上传。
- 先上传变化的版本化资源并下载验收，再更新固定路径文件，最后更新根清单。固定路径使用 `no-cache`，带哈希/提交号资源使用长期缓存；不删除旧包、不修改 ACL 或桶策略。
- 完成后重新下载全部清单文件，校验 SHA-256、依赖与缓存头。发布中失败则尝试恢复此前验证过的可变文件和清单，验收回滚结果；不删除已上传但未被引用的新包。
- 工作目录使用独占锁，防止本机任务重叠。进程意外终止留下锁时，先确认没有运行中的同步，再人工处理；不自动忽略锁。
- 每次保存 `plan.json`、`result.json`；成功后更新 `latest-success.json`。发布不是多对象原子操作，执行期间避免安装；多个维护者应协调发布窗口。

可由本机定时任务或 CI 在明确授权后调用。任务只自动同步这个镜像目标，验证后再提出 Skill 适配建议；提交代码、发布评论和操作车辆属于不同授权。CLI 与私有配置需在执行机器上可用。独立 Skill 压缩包不包含仓库 `tools/` 或凭据。
