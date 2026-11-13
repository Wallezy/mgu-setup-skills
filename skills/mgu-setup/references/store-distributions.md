# Full distributions / 整套发行版

<a id="choose-edition"></a>
## First installation: one choice / 首次安装：只选一次

| Edition / 版本 | Recommend when / 推荐场景 | Updates and differences / 更新与区别 |
| --- | --- | --- |
| **Walle 国内版 / CN** | Mainland China / 中国大陆 | Store, core components and maps update through domestic HTTPS catalogs. 中文适配，由维护者审阅、合并上游后发布；不保证与上游同时更新。无 GitHub 登录、令牌或 GitHub 软件源功能。 |
| **官方版 / Official** | Other regions, or users wanting upstream/GitHub sources / 其他地区，或希望直接使用上游与 GitHub 源 | Direct upstream releases with GitHub source support. 先直连下载，访问不畅时使用经过校验的备用源；仍然是官方版。内置商店/基础组件在线更新仍使用 GitHub。 |

Both remain available by choice. Both need a working vehicle network for online
updates; a region recommendation is not a connectivity guarantee.

1. Reuse the current explicit choice, then the saved choice. On existing installs,
   preserve the installed edition unless a switch is requested.
2. For a new install with no choice, use a region already stated in the conversation
   or private record: recommend CN for mainland China, official elsewhere. Do not
   infer location from Chinese, IP or timezone. State the recommendation briefly;
   a general install request may proceed with it within existing authorization.
3. If the region is unknown, ask **one edition question** using the short explanation
   below. Do not separately ask region, map source and release channel. Before an
   answer, continue independent environment/resource checks, not an edition write.
4. Record the edition and effective source privately. Use the matching installer
   and production release; do not add the official OSS map mirror to CN. For
   official downloads, reuse an explicit source choice; otherwise try direct
   upstream access and use verified fallback resources when needed. Preserve
   versions/hashes and explain only “改用备用源 / using a backup source”.
   Do not ask for another source choice or offer a third edition.

Suggested Chinese explanation (only add the final question if a choice is missing):

> **国内版（大陆推荐）**：商店、基础组件和地图走国内在线更新，含中文适配；上游更新由维护者合并后发布，不支持 GitHub 软件源。
>
> **官方版（其他地区推荐）**：直接跟随上游发布，支持 GitHub 软件源；下载时自动选择直连或备用源。
>
> 你想安装哪一版？

English: “**CN (recommended in mainland China):** domestic online updates and
Chinese adaptations; upstream changes arrive after maintainer review, without
GitHub sources. **Official (recommended elsewhere):** upstream releases and GitHub
sources, with direct or backup downloads selected for the connection.
Which edition would you like?”

**Operator detail: backup source ≠ CN edition.** The official-package OSS mirror changes only
where original bytes are downloaded. It does not replace the official Store's
built-in GitHub update source; the separate map mirror covers map apps only.
Use [network-mirrors.md](network-mirrors.md) when that transport is needed.
Do not expose Gitee/OSS/download preferences as installation choices. If official
built-in online updates are unreachable, state that specific limit and use a
supported offline path; do not claim the backup makes all online updates work,
silently switch to CN, or ask the user to diagnose the network.

CN keeps component IDs/settings, normalizes known official/mirror definitions
and isolates catalog caches. GitHub source/account features are disabled without
automatic fallback; retained account data is for recovery. Compatible third-party
HTTPS/local sources remain separate. Do not install a second Store/updater or
silently remove unrelated apps. After setup verify the running updater's
`distribution: "walle-cn"`, `github: false` and effective managed sources.

<a id="switch-distribution"></a>
## Switch the full distribution / 切换整套发行版

Use this route for "switch to CN", "return to official" or a change of fork,
including the installer. Same-edition upgrades use [maintenance](maintenance-update.md);
the same upstream bytes from another host use [mirrors](network-mirrors.md).
Neither an official installation nor a backup source alone implies an upgrade
fault. Reuse the user's target; ask only when "switch version" remains ambiguous.

1. **Inventory and match.** Use saved records and verified read-only observations
   to identify the installed distribution, architecture, components, sources and
   available package fingerprints. A Chinese interface or an OSS row is not proof
   of the installed edition. Identify another fork by provenance, not its title.
   With no car, finish local preparation and mark the installed state unverified.
2. **Freeze one complete plan.** Cover every row below before writing. Bind the
   exact target installer/bootstrap, catalogs, source revisions, package hashes,
   dependencies and supported migration entrypoint. Reuse verified matching local
   resources; never run the official network bootstrap to install CN packages.
3. **Check the actual transition.** Same version and identical bytes can be retained;
   same version with different bytes needs explicit replacement support. Higher
   versions still need cross-edition compatibility; lower versions need a supported
   [restore path](recovery.md). Preserve settings, source/origin/alias records and
   verified prior payloads. Metadata or coding backups alone cannot restore programs.
4. **Migrate through supported operations.** Execute the plan's installer/Store
   entrypoint and declared dependency order, not a universal hard-coded sequence.
   Commit required updater self-update checks before dependent operations. Missing
   support blocks the affected writes, not preparation. Do not guess a CLI flag,
   remove the working Store first or edit versions/firmware markers to force a retry.
5. **Verify the whole result.** Record the installer actually used, active package
   identities, retained settings, one managed row per component, service health and
   every managed component's selected update source. Test catalog/package reachability;
   an actual later update is separate evidence and needs a genuine compatible release.
   Mark a partial transition as partial; switching back to official needs the same
   compatibility and recovery assessment.

| Layer / 层次 | Required coverage / 覆盖范围 |
| --- | --- |
| Computer / 电脑端 | Target installer, shell/PowerShell bootstrap where used, runtime requirements, checksums and local package plan; keep the previous installer privately for recovery |
| Store and control / 商店与管理工具 | `robertn_store`, `mgu-updater`, `mgu-deploy`; self-update and recovery compatibility |
| Base dependencies / 基础组件 | Installed or required Python, privacy, network and renderer components; do not install unrelated optional tools |
| Apps and native tools / 应用及原生工具 | All installed components in scope, including map control, capture service and cluster/HUD renderer; match by stable component ID |
| Update channel / 后续更新 | Catalogs, artifact/icon URLs, source ownership and aliases for the entire managed set; a CN transition must not leave base components updating from GitHub |
| Root access / Root 访问 | Record a compatible Root tool and reuse healthy SSH; selecting a distribution does not require another flash |

For each item record: **current identity -> target identity -> retain / migrate /
unmapped -> supported action and recovery**. Identical shared dependencies can
remain installed when compatible, with their future update ownership verified.
Do not silently remove third-party apps or replace them by similarly named ones.
If the target has no counterpart, preserve it and report the unmapped item; do not
claim that every installed app migrated. Installing every optional app in the target
catalog is a separate request.

“切换到国内版，包含安装器和全部已安装组件，保留设置”会进入整套迁移流程。
普通安装和更新直接使用正式版，不主动介绍测试版或让用户选择发布通道。
只有用户明确要求安装 Beta，或维护此前明确选择的 Beta 安装时，才读取
[测试版内部流程](release-channels.md)。维护者发布任务也使用该参考文档，
但发布授权不等于车端安装请求。离线检查、公开发布和实车通过分别记录。

## Current readiness / 当前可用状态

Check current publication records and the selected release manifest instead of
treating this document as a live release-status register. Production resources use:

- `https://mgu.walle.pw/mgu/cn/mgu-store/catalog.json`
- `https://mgu.walle.pw/mgu/cn/idrive-apps/catalog.json`
- `https://mgu.walle.pw/mgu/cn/bootstrap/mgu-install.js`

These production paths alone do not prove installation readiness. Verify the
published snapshot, compatibility and prerequisites for the requested operation.
If the production release is unavailable or required evidence is missing, finish
independent preparation and explain that concrete blocker without offering a
prerelease or silently substituting another edition. Publication does not prove
complete vehicle validation; keep pending checks pending.

## Installer and migration details / 安装与迁移细节

Use the exact selected CN release's `deploy/README.md` and `docs/CN-MIGRATION.md`
for command support and limits. Reviewed reference:
[CN Store at 6ece1e7](https://github.com/Wallezy/mgu-store-cn/tree/6ece1e71e4ff39db4acff0b6ca28e9eb16b0d823).
Source repositories are `Wallezy/mgu-store-cn` and `Wallezy/idrive-apps-cn`;
official counterparts are `robertnisipeanu/mgu-store` and
`robertnisipeanu/idrive-apps`. Do not use historical candidate numbers as targets.

- `migrate-cn --from ... --plan-only` prepares a transaction; it is not strictly
  read-only. Execution uses its exact plan/snapshot requirements, and
  `migration-status`, `migration-verify`, `migration-rollback` apply to that
  recorded transaction. An `installReady: false` production snapshot blocks execution.
- Same-version localization changes bytes. A source switch or translated catalog
  title does not prove the CN payload is installed. Ordinary `first-install`
  skips healthy same-version apps; do not retry it as migration or falsify versions.
- Inspect actual ID7/ID8, replacement, downgrade and unknown-source restrictions.
  A higher version alone is not migration compatibility. Preserve complete
  runtime and RHMI recovery packages; a package missing the UI cannot restore it.
- Resume interrupted work from its journal. After a later online update, the old
  migration journal is historical, not a blind rollback for new payloads.
  Transaction rollback restores its old bytes, not arbitrary official releases.
- Keep numeric three-part release versions. Record upstream version and CN revision
  in the release's provenance/notes; changed published bytes require a new version.

## Maintainer work / 维护者任务

Read [release-channels.md](release-channels.md) only for release work or an
explicit Beta request. It covers reviewed upstream dual-channel publication,
explicitly authorized small improvements and separate development trials.
Keep publication evidence separate from actual vehicle tests.

`tools/sync_oss.py` mirrors **unchanged official packages** under `/mgu/mgu-store/`
and `/mgu/idrive-apps/`; it must not write `/mgu/cn/`. Existing Gitee mappings
mirror the Skill and official projects, not CN fork releases. CN publication uses
the CN Store's release tools and independent snapshots. Keep credentials, vehicle
data, firmware and SDK donors out of public repositories and packages.
