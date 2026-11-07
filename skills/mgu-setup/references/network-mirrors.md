# Network sources / 网络源

Use one skill and one vehicle workflow. Source preference changes download locations, not installation checks or authorization.

## Preference / 优先级

Read `network-sources.json`. Supported preferences:

| Preference | First choice | Fallback |
| --- | --- | --- |
| `domestic-first` | Gitee source + configured OSS packages | Official upstream, with a recorded reason |
| `upstream-first` | Official GitHub source/releases | Configured OSS |
| `auto` | Official GitHub source/releases | Configured OSS |

`auto` tests catalogs; it does not geolocate users. A Chinese-language request is not a location signal. Honor an explicit preference, keep it for subsequent tasks, and report the selected source. If no preference is known, use `auto`. The shared skill starts in `auto`; users in mainland China can select `domestic-first`.

The planner limits each catalog/metadata request to 20 seconds with no retries before trying the next configured source on failure; this is not a 20-second bound for the entire plan. Package downloads keep their longer timeout, retries and integrity checks. Once a usable source is selected, do not repeatedly probe the failed source during the same update without new evidence. Confirm the installed updater's source/origin mapping before using a mirror to update existing apps.

国内用户选择 `domestic-first`，海外用户选择 `upstream-first`；默认 `auto` 优先尝试官方源，不通过 IP 或系统语言判断所在地。用户指定优先级后，应复用该偏好。GitHub 与 Gitee 的代码同步、OSS 的发布包同步是两件事。

## Configure and plan / 配置与计划

An operator sets the real public HTTPS root after OSS upload. Do not invent or substitute a placeholder URL:

```text
python scripts/mirror_resources.py configure --base-url <实际OSS根地址> --preference domestic-first
python scripts/mirror_resources.py plan --output <仓库外目录>/source-plan.json
```

Paths are relative to this skill folder. Windows may use the selected Python launcher. `configure` updates `references/network-sources.json`; use `--config <path>` for an external preference file instead. Planning downloads catalogs and records exact versions and hashes, without touching a vehicle. Catalog success does not prove package downloads work.

The mirror root contains `mirror-manifest.json`, `mgu-store/catalog.json`, `idrive-apps/catalog.json` and `bootstrap/mgu-install.js`. The upstream links in provenance and bundled README files are attribution, not runtime package dependencies.

## Download and verify / 下载与校验

For an explicitly selected domestic source:

```text
python scripts/mirror_resources.py fetch --output <仓库外目录>/verified-mirror --plan <仓库外目录>/source-plan.json
python scripts/mirror_resources.py verify <仓库外目录>/verified-mirror
```

`fetch` downloads the complete maintenance snapshot, including both catalogs, published components, pinned source archives and license files. It uses the configured OSS URL, verifies sizes/hashes, reuses valid cached files, checks dependencies and never installs anything. The skill itself stays in GitHub/Gitee, so configuring an OSS root does not require uploading all packages again. This is an optional complete-cache path; for a small requested scope, use the official installer's `usb-repo` with the selected catalog(s) and inspect its dependency coverage instead of requiring unrelated downloads.

The fetch command does not switch sources on its own. For upstream selection, use the official GitHub `usb-repo` workflow. On a download failure, compare the fallback catalog against the saved source plan: selected component versions and SHA-256 values must match, with all required dependencies present. Stop if they differ; explain the difference instead of silently installing the fallback's older or newer version.

Use Gitee to obtain source/skill files, not as a `gitee:` updater source. The mirrored root tool's selected revision, structure and architecture assets still need inspection; neither the code mirror nor OSS grants permission to redistribute root credentials, donor SDKs or firmware assets.

## Official offline workflow / 官方离线安装路径

Use the verified, unmodified `bootstrap/mgu-install.js`. First prepare an existing folder outside the mirror tree:

```text
node <verified-mirror>/bootstrap/mgu-install.js usb-repo <existing-folder> <verified-mirror>/mgu-store <verified-mirror>/idrive-apps
```

This converts the mirror catalogs into the official flat USB layout. Apply only the previously authorized operation, with vehicle and backup prerequisites met. For Store setup or a compatible Store-bundle refresh, the official path is:

```text
node <verified-mirror>/bootstrap/mgu-install.js first-install --from <existing-folder>/mgu-repo/mgu-store --identity <private-key-path>
```

The mirror's nested, hash-addressed package layout is for HTTPS/`usb-repo` input; do not assume it is already the flat `first-install --from` layout. The installer sends that Store bundle over SSH/ENET without needing physical USB or HU internet; the inspected implementation supports rerunning and preserves newer installed components. It does not install arbitrary app catalogs. Other app installation uses Store UI/USB or another supported updater path; preparing a computer folder does not mount it on the HU.

For existing apps, choose the actual transfer path using [maintenance-update.md](maintenance-update.md) before preparing a proxy. Adding an OSS HTTPS source selects online downloads, not files already cached on the computer. In updater 0.8.30 a configured proxy still requires an uplink lease for network requests; the local USB reader is separate. Do not generalize that gate into a requirement that every offline update must connect to a hotspot.

## Keep car updates on the chosen source / 车端更新源

The unmodified installer seeds GitHub sources on a fresh unit. A successful offline first installation does not switch future updates to OSS.

For domestic use, once the Store opens, use **Settings → Add source** to add the real HTTPS URLs ending in `mgu-store/catalog.json` and `idrive-apps/catalog.json`. Inspect displayed versions/dependencies against the prepared snapshot. Use supported Store controls to disable unwanted upstream checks if available and requested; do not remove built-in sources by editing files. Do not modify vehicle registries, binaries or the bootstrap installer merely to change a mirror URL. If the installed Store cannot manage its sources, report that limit and retain the working USB update path.

The reviewed updater 0.8.31 retains a built-in GitHub Store source and refuses its removal; adding OSS does not replace it. The mirrored installer and updater remain unmodified. `domestic-first` is a preference with possible upstream fallback, not an enforced domestic-only network policy.

审阅的 updater 0.8.31 不允许移除内置 GitHub 商店源；新增 OSS 不是替换内置源。镜像保留原版安装器/更新器。`domestic-first` 允许记录原因后回退官方源，不能宣称整个过程绝不访问外网。

## Acceptance after upload / 上传后验收

The maintainer provides a stable HTTPS download root without login, cookies or expiring query tokens. HTTPS public reads must work from the intended clients. CORS is not needed for the native installer/updater download path.

Use `fetch --base-url <实际根地址> --output <新的验收目录> --manifest-sha256 <本地清单SHA256>` to verify every uploaded file against the prepared manifest. Also test the official `usb-repo` conversion locally; it does not require or contact a vehicle. These checks validate distribution, not vehicle compatibility.

Do not report the domestic path publicly available until this remote acceptance succeeds. Preserve TLS verification.

## Update review and upload handoff / 更新检查与上传交接

When reviewing upstream or skill updates, compare both published upstream catalogs with live OSS, including their complete dependencies. A current Gitee checkout or reachable OSS index does not establish that its packages are current or available. Keep unresolved mirror differences visible in later reports.

For an authorized mirror refresh, use the repository's `tools/prepare_oss.py` to generate and verify a new complete snapshot outside the checkout. Compare it with a verified live snapshot to identify uploads. Provide exact object paths, new/replaced files, versions, hashes, cache settings and upload order. Clearly distinguish prepared files from recommendations; never invent paths or checksums. A delta is sufficient only when all omitted files still match on OSS.

Upload versioned packages and source archives first, followed by changed supporting files, both catalogs, and finally `mirror-manifest.json`. Keep old packages for rollback and active downloads. Use long caching only for content-addressed/versioned objects; use `Cache-Control: no-cache` for catalogs, manifest and other replaced fixed-path files. The two catalogs and manifest are not an atomic update: avoid installs during publication and complete remote acceptance afterwards. A new snapshot prefix provides stronger isolation.

Trace later download URLs as well as catalog artifact URLs: check installer defaults, updater sources, dependency downloads and external runtime assets. Distinguish attribution/source links from required network access. Offline preparation and relative OSS artifact URLs do not disable the Store's built-in GitHub checks. Report unverified paths and unsupported source-management controls rather than claiming an entirely offline/domestic workflow.

更新检查必须同时对照官方发布与实时 OSS，列出需要新增或替换的准确路径、版本、哈希、依赖和缓存设置。先完整生成并校验资源，再与已验证的线上快照比较；仅当省略文件在线上仍一致时，才可交付增量上传包。先资源、再目录、最后清单；上传窗口内避免安装，完成后重新远端验收，保留旧包。

还须检查安装器、更新器和运行时的后续下载依赖，区分溯源链接与必需联网路径。镜像目录可用不等于车端所有更新都走 OSS。用户自行上传时，交付文件和步骤，不代为上传、删除或宣称上线成功。

For explicitly authorized maintainer automation, the source repository provides `tools/sync_oss.py --publish` (not bundled in the standalone skill). It accepts an external private ossutil config, verifies live/upstream snapshots, publishes a delta with cache metadata and performs public acceptance; failures attempt restoration of prior mutable indexes. Read the repository's `docs/DOMESTIC-MIRROR.md` for invocation and scope. Keep credentials out of instructions and public artifacts; only report success after the script's remote acceptance. Automation of mirror uploads does not authorize vehicle updates or repository pushes.

维护者明确授权自动上传时，可使用源码仓库的 `tools/sync_oss.py --publish`，配置保存在仓库外，按脚本结果报告同步、验收或回滚状态。独立 Skill 不包含该维护工具，不能假定它已安装。自动镜像同步不等于自动升级车辆。
