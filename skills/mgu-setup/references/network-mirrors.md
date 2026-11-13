# Official backup sources / 官方版备用源

Use one skill and one vehicle workflow. Source preference changes download locations, not installation checks or authorization.

This document covers mirrors of unmodified upstream releases. For the
separate CN Store edition, read [store-distributions.md](store-distributions.md);
its production catalogs are separate from the official-package mirror.

## Preference / 优先级

Read `network-sources.json`. Supported preferences:

| Preference | First choice | Fallback |
| --- | --- | --- |
| `domestic-first` | Gitee source + configured OSS packages | Official upstream, with a recorded reason |
| `upstream-first` | Official GitHub source/releases | Configured OSS |
| `auto` | Official GitHub source/releases | Configured OSS |

These are internal **official-package download preferences**, not an installation
menu. Users choose only CN or official via [edition selection](store-distributions.md#choose-edition).
Reuse an explicit/recorded preference; otherwise use `auto`: try direct upstream
access, then verified backup resources when the selected catalog/artifact is
unreachable. Tell the user “改用备用源 / using a backup source”, not “choose a
domestic mirror edition”. No additional source question is needed.
Keep shared configuration at `auto`; save personal preferences via an external
`--config`. CN Store/app updates use CN catalogs, not this official mirror planner.

The planner limits each catalog/metadata request to 20 seconds with no retries before trying the next configured source on failure; this is not a 20-second bound for the entire plan. Package downloads keep their longer timeout, retries and integrity checks. Once a usable source is selected, do not repeatedly probe the failed source during the same update without new evidence. Confirm the installed updater's source/origin mapping before using a mirror to update existing apps.

用户只选择“国内版／官方版”。官方版按网络情况使用直连或备用源，无需再选下载线路。
`domestic-first` 等名称只用于内部配置；对用户统一称“备用源”。
下载备用源不会自动切换车端内置更新源；GitHub/Gitee 代码同步与 OSS 包同步分别维护。

## Configure and plan / 配置与计划

An operator sets the real public HTTPS root after OSS upload. Do not invent or substitute a placeholder URL:

```text
python scripts/mirror_resources.py configure --base-url <实际OSS根地址> --preference domestic-first
python scripts/mirror_resources.py plan --output <仓库外目录>/source-plan.json
```

Paths are relative to this skill folder. Windows may use the selected Python launcher. `configure` updates `references/network-sources.json`; use `--config <path>` for an external preference file instead. Planning downloads catalogs and records exact versions and hashes, without touching a vehicle. Catalog success does not prove package downloads work.

The mirror root contains `mirror-manifest.json`, `mgu-store/catalog.json`, `idrive-apps/catalog.json` and `bootstrap/mgu-install.js`. The upstream links in provenance and bundled README files are attribution, not runtime package dependencies.

The maintained domestic root is `https://mgu.walle.pw/mgu/`, backed by the
Hangzhou bucket `walle-mgu`. Preserve the requested source preference:
`auto`/`upstream-first` still prefer GitHub; `domestic-first` prefers this root.
The Beijing mirror is retained for existing clients, not the default for new
domestic preparation. Do not silently fall back to it after a route failure.

国内镜像使用杭州自定义域名；海外/官方优先策略保持不变。
旧北京地址保留兼容，但不能在新地址失败时未经检查又退回已知路由冲突的旧地址。

Published catalog icons use relative `icons/<sha256>/<name>.png` paths on the
same OSS origin. The manifest records their official Release URLs, sizes and
hashes; these source URLs are provenance, not the rewritten runtime icon URL.
Validate icon bytes as well as packages. Do not interpret an external icon
URL or an unlisted icon as a complete domestic snapshot.

发布目录图标也须来自同一 OSS，使用带哈希的相对路径；官方来源仅用于溯源。
图标缺失、未入清单或仍指向外部运行时地址，均不能判为镜像完整。

Root tools use a separate [release preparation path](root-tool.md), not either
Store catalog. Verify the selected Gitee tag against the reviewed official
commit; the current OSS manifest does not supply a Root source or Windows bundle.
Root 工具单独按正式版本准备；Gitee 需核对标签/提交，不能把商店 OSS 完整缓存当成 Root 也已齐备。

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

This converts the mirror catalogs into the official flat USB layout. Apply only the previously authorized operation, with vehicle and backup prerequisites met.

At reviewed Store commit `efbdcc0d68bd7faf5c5939fa6240050e5e3a449f`,
`usb-repo` copies packages but does not copy catalog PNG icons, even though it
retains their paths. Local verification covered all ten package files, not
USB icon display. OSS catalogs and a complete `fetch` snapshot include the
icons; do not describe upstream USB conversion as an icon-complete copy.
本次审阅的原版 USB 转换器不复制图标，不能把包校验通过等同于 USB 图标显示已验证。

For Store setup or a compatible Store-bundle refresh:

```text
node <verified-mirror>/bootstrap/mgu-install.js first-install --from <existing-folder>/mgu-repo/mgu-store --identity <private-key-path>
```

The mirror's nested, hash-addressed package layout is for HTTPS/`usb-repo` input; do not assume it is already the flat `first-install --from` layout. The installer sends that Store bundle over SSH/ENET without needing physical USB or HU internet; the inspected implementation supports rerunning and preserves newer installed components. It does not install arbitrary app catalogs. Other app installation uses Store UI/USB or another supported updater path; preparing a computer folder does not mount it on the HU.

For existing apps, choose the actual transfer path using [maintenance-update.md](maintenance-update.md) before preparing a proxy. Adding an OSS HTTPS source selects online downloads, not files already cached on the computer. In updater 0.8.30 a configured proxy still requires an uplink lease for network requests; the local USB reader is separate. Do not generalize that gate into a requirement that every offline update must connect to a hotspot.

## Keep car updates on the chosen source / 车端更新源

The unmodified installer seeds GitHub sources on a fresh unit. A successful offline first installation does not switch future updates to OSS.

For an authorized official app install/update, reuse explicit source preferences.
Otherwise use direct GitHub when reachable and the verified backup when needed;
briefly state the fallback without another selection question. This route covers
the removable `idrive-apps` source, not the built-in Store infrastructure.
Use the catalog URL, not the bare domain:

```text
https://mgu.walle.pw/mgu/idrive-apps/catalog.json
```

按实际网络使用直连或备用源，复用明确偏好，不同时保留两份相同地图目录。
这是官方版内部的线路处理，不是第三个版本；不改不可删除的商店内置源或其他作者的来源。

With both sources present, installed components keep their origin and the
mirror's duplicate IDs can be blocked. In inspected updater 0.8.32/0.8.38,
when the old removable source no longer lists an installed component,
`openLead()` can select a remaining source by matching its installed title.
HTTPS `copyOf` is not a mirror alias. Do not assume this fallback works for
every component or version.

For an authorized switch:

1. Save source definitions, actual installed versions, recorded origins and
   error state privately. Verify the selected catalog and dependencies first.
2. Add the chosen source through supported Store source management if absent.
   Remove only the matching, removable duplicate source, without uninstalling
   its components. Preserve unrelated sources and the built-in source.
3. Check each affected installed ID has one row, unchanged installed version,
   the chosen effective update source, and no `blocked`/unlisted condition.
   Check dependency sources separately. If selection fails, restore the saved
   source definition and report the failure; do not edit origin files.
4. Record effective source selection separately from persisted install origin
   and successful installation. Historical download errors may remain in the
   state after switching; do not erase them or start an install merely to
   clear them. Installing/updating is a separate authorized operation.

移除来源不是卸载应用。本车 updater 0.8.32 实测：移除官方 `idrive-apps` 来源后，
三个地图组件只剩单条、有效更新源为杭州 OSS、`blocked=null`，已安装版本保持不变。
这只证明来源选择与去重，不是整包下载或安装成功；旧错误记录及安装归属分别记录。

The reviewed updater 0.8.31 retains a built-in GitHub Store source and refuses its removal; adding OSS does not replace it. The mirrored installer and updater remain unmodified. `domestic-first` is a preference with possible upstream fallback, not an enforced domestic-only network policy.

审阅的 updater 0.8.31 不允许移除内置 GitHub 商店源；新增 OSS 不是替换内置源。镜像保留原版安装器/更新器。`domestic-first` 允许记录原因后回退官方源，不能宣称整个过程绝不访问外网。

Do not add a duplicate Store HTTPS source by default on these versions.
The Store mirror catalog at `https://mgu.walle.pw/mgu/mgu-store/catalog.json`
remains useful for verified computer-side package preparation and supported
offline Store maintenance. It cannot transparently replace the built-in
GitHub source. When GitHub is unreachable, use a supported proxy or the
scoped offline maintenance path; a map-source switch does not repair this.
Keep existing owner sources unless removal is authorized.

基础组件仍由内置官方源管理；GitHub 不可达时，仅更换地图备用源无法更新这些组件。
可用已验证代理或官方本地包维护路径，不能宣称纯 OSS 在线更新已实现。
地图未来若要求更高版本的基础组件，也必须先解决该依赖的获取路径。

## Online but downloads fail / 在线但来源失败

An uplink lease establishes a connection, not DNS/TLS/artifact reachability.
Check the exact catalog and a required package through the actual downloader's
network context. The 2026-11-11 case found a main-table `59.0.0.0/8` route
intercepting the Beijing endpoint; the hotspot DNS also returned loopback for
a GitHub download hostname. These are independent of origin conflicts.
The Hangzhou custom domain passed a complete small-file GET, TLS and SHA-256
check over that vehicle's hotspot without proxy. It does not certify every
future DNS address, other vehicles or an application update.

When local and HU results differ, distinguish DNS answers, selected routes,
TLS failures and HTTP responses. Preserve certificate checking and original
vehicle routes. Use the supported proxy path for an authorized temporary
workaround, record its dependency on the computer/ENET, and restore temporary
settings when finished. Do not repeatedly refresh catalogs or reflash Root.

热点“在线”不代表下载可用；电脑代理的虚拟 DNS 地址也不能作为车机公网路径证据。
换域名后的成功只证明当时路径可达，不能代替更新来源归属及安装验收。

## Acceptance after upload / 上传后验收

The maintainer provides a stable HTTPS download root without login, cookies or expiring query tokens. HTTPS public reads must work from the intended clients. CORS is not needed for the native installer/updater download path.

Use `fetch --base-url <实际根地址> --output <新的验收目录> --manifest-sha256 <本地清单SHA256>` to verify every uploaded file against the prepared manifest. Also test the official `usb-repo` conversion locally; it does not require or contact a vehicle. These checks validate distribution, not vehicle compatibility.

Do not report the domestic path publicly available until this remote acceptance succeeds. Preserve TLS verification.

## Update review and upload handoff / 更新检查与上传交接

When reviewing upstream or skill updates, compare both published upstream catalogs with live OSS, including their complete dependencies. A current Gitee checkout or reachable OSS index does not establish that its packages are current or available. Keep unresolved mirror differences visible in later reports.

For an authorized mirror refresh, use the repository's `tools/prepare_oss.py` to generate and verify a new complete snapshot outside the checkout. Compare it with a verified live snapshot to identify uploads. Provide exact object paths, new/replaced files, versions, hashes, cache settings and upload order. Clearly distinguish prepared files from recommendations; never invent paths or checksums. A delta is sufficient only when all omitted files still match on OSS.

Upload versioned packages, content-addressed PNG icons and source archives first, followed by changed supporting files, both catalogs, and finally `mirror-manifest.json`. Keep old packages for rollback and active downloads. Use `Cache-Control: public,max-age=31536000,immutable` for content-addressed packages/icons and commit-addressed sources, `Content-Type: image/png` for PNGs, and `Cache-Control: no-cache` for catalogs, manifest and other replaced fixed-path files. Verify these headers on all indexed resources, including reused files. The two catalogs and manifest are not an atomic update: avoid installs during publication and complete remote acceptance afterwards. A new snapshot prefix provides stronger isolation.

Trace later download URLs as well as catalog artifact URLs: check installer defaults, updater sources, dependency downloads and external runtime assets. Distinguish attribution/source links from required network access. Offline preparation and relative OSS artifact URLs do not disable the Store's built-in GitHub checks. Report unverified paths and unsupported source-management controls rather than claiming an entirely offline/domestic workflow.

更新检查必须同时对照官方发布与实时 OSS，列出需要新增或替换的准确路径、版本、哈希、依赖和缓存设置。先完整生成并校验资源，再与已验证的线上快照比较；仅当省略文件在线上仍一致时，才可交付增量上传包。先资源、再目录、最后清单；上传窗口内避免安装，完成后重新远端验收，保留旧包。

还须检查安装器、更新器和运行时的后续下载依赖，区分溯源链接与必需联网路径。镜像目录可用不等于车端所有更新都走 OSS。用户自行上传时，交付文件和步骤，不代为上传、删除或宣称上线成功。

For explicitly authorized maintainer automation, the source repository provides `tools/sync_oss.py --publish` (not bundled in the standalone skill). It accepts an external private ossutil config, verifies live/upstream snapshots, publishes a delta with cache metadata and performs public acceptance; failures attempt restoration of prior mutable indexes. Read the repository's `docs/DOMESTIC-MIRROR.md` for invocation and scope. Keep credentials out of instructions and public artifacts; only report success after the script's remote acceptance. Automation of mirror uploads does not authorize vehicle updates or repository pushes.

维护者明确授权自动上传时，可使用源码仓库的 `tools/sync_oss.py --publish`，配置保存在仓库外，按脚本结果报告同步、验收或回滚状态。独立 Skill 不包含该维护工具，不能假定它已安装。自动镜像同步不等于自动升级车辆。
