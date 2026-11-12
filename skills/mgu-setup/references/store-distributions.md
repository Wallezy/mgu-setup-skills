# Full distributions / 整套发行版

Choose the Store edition separately from the computer's download preference.
Reuse an explicit choice. If the user asks to switch editions, identify the
installed updater and preserve its sources, origins, aliases and recovery
inventory before preparing the matching release. An existing, healthy SSH
connection needs no Root reflash.

An edition selection covers the computer's installer and the vehicle's complete
managed software set. It is not merely a Store UI replacement or a source URL.
Components retain their own versions; one release plan binds their compatible
versions, hashes, installer and update channels.

发行版选择包括电脑端安装器、车端商店和更新服务、部署工具、基础依赖及已安装应用。
各组件保留各自版本号，由同一份发行计划固定兼容组合；不要求所有版本数字相同。

| Edition | Source | Install status |
| --- | --- | --- |
| Official upstream | `robertnisipeanu/mgu-store`, `robertnisipeanu/idrive-apps` | Use reviewed published releases and the supported workflow |
| Walle CN | `Wallezy/mgu-store-cn`, `Wallezy/idrive-apps-cn` | Development: no approved vehicle installation release |

The official edition can use a verified mirror for local package preparation.
That does not replace its built-in GitHub update source. Keep the existing
[mirror/source guidance](network-mirrors.md) for this edition.

The CN fork's intended behavior is domestic catalogs for Store, updater,
dependencies and map apps, while retaining component IDs and settings. It
normalizes known official/mirror source definitions, disables GitHub sources
and account functionality, and isolates cached catalogs. Compatible HTTPS/local
sources remain separate. It is an alternative distribution of the same
components, not a second Store/updater to install alongside them.

国内版目标是商店、基础组件与地图应用都使用国内目录，保留组件身份和已有设置。
这与原版商店“新增一个 OSS 来源”不同。不得把原版镜像包称为国内版，也不得同时
安装两套更新器。国内版移除 GitHub 登录、令牌管理和 GitHub 来源功能，不自动
访问或回退 GitHub；已有相关资料保留用于恢复。其他作者的应用可通过完整 HTTPS
目录或本地包提供。GitHub 源码仓库与作者署名不属于车机运行时下载功能。

<a id="switch-distribution"></a>
## Switch the full distribution / 切换整套发行版

Use this route for "switch to CN", "return to official" or a change of fork,
including the installer. Same-edition upgrades use [maintenance](maintenance-update.md);
the same upstream bytes from another host use [mirrors](network-mirrors.md).
Neither an official installation nor a domestic mirror alone implies an upgrade
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
**当前 Walle CN 已有开发中的迁移入口，但尚无通过车机集成验收的换装发布。**
Skill 仍只完成本地检查与资源准备，不能把离线测试通过当作车机安装许可。

## Current readiness / 当前可用状态

As of 2026-11-12, the CN repositories contain source, offline migration tests
and local release candidates.
They have not passed the required head-unit integration, migration, update
order, self-update and recovery checks. Their reserved paths are:

- `https://mgu.walle.pw/mgu/cn/mgu-store/catalog.json`
- `https://mgu.walle.pw/mgu/cn/idrive-apps/catalog.json`
- `https://mgu.walle.pw/mgu/cn/bootstrap/mgu-install.js`

These are not approved installation links. If CN is requested now, complete
local preparation and report the missing integration/release evidence. Do not
silently substitute the official edition or install a development branch.
Do not mark the CN option ready because the repositories exist, unit tests
pass, an HTTP request succeeds, or a catalog contains higher version numbers.

目前选择国内版只能准备代码与资源，不能直接换装。选择官方版可继续既有维护路径；
用户明确要求国内版时，不擅自替换为官方版，也不把开发分支作为正式发布安装。

## Enabling a verified CN release

Before changing the status above, record a fixed release with:

1. Exact source commits for both forks and successful
   `release-check/cn-integration` statuses for those commits, backed by actual
   integration records. Local fixture tests do not establish these statuses.
2. Packages, icons, licenses, corresponding sources and bootstrap checksums.
   Verify dependency closure and all public HTTPS bytes under the dedicated
   CN prefix. Catalogs/manifests need revalidation caching; immutable resources
   retain version/hash paths.
3. Proven fresh-install and existing-install migration, each supported
   component-update order, CN-to-CN self-update, failed-update recovery and
   supported return to the prior working installation.
4. A supported Store/installer migration entry point for the selected installed
   version. Do not improvise by overwriting source/origin files or uninstalling
   the working Store first.

After release acceptance, follow the fixed release's migration procedure,
check one row per managed component, chosen update sources, active versions,
restart health and a subsequent CN update. A source switch alone is not an
installed update. Preserve the earlier real-vehicle evidence with its own
versions; do not apply it to this fork.

## Maintainer separation

The existing `tools/sync_oss.py` mirrors **unmodified upstream** packages under
`/mgu/mgu-store/` and `/mgu/idrive-apps/`. Its daily job must not publish those
catalogs as CN releases or write `/mgu/cn/`. The four existing Gitee mappings
also remain official-source mirrors; they do not mirror these new forks.

The Store fork's release tooling prepares the independent CN snapshot.
Uploading that snapshot and public acceptance are separate from GitHub code
pushes. Keep credentials, car data, private keys, firmware and SDK donors out
of both repositories and all public snapshots.

## Chinese localization and unchanged versions / 汉化与同版本迁移

The initial `idrive-apps-cn` localization keeps `robertn_waze_cluster` at
`0.6.7`, `waze-on-cluster` at `0.9.10` and `cluster-render` at `0.5.4`.
These are preparation baselines, not permanent recommended or frozen versions.
The fork's `release/cn-localization-versions.json` and its test track all version
fields; a future reviewed upstream upgrade updates that baseline deliberately.

Chinese coverage includes the control app's menus and known dynamic status/error
messages, the native log-download web page, and catalog titles/descriptions.
The app defaults to Chinese when the HMI language is unknown and follows an
explicit supported language. Raw logs, IDs and machine protocol fields retain
their original form; unknown diagnostic details are preserved rather than guessed.

Changing UI text changes artifact bytes even if the displayed version stays the
same. Keep the exact CN source commit, catalog and SHA-256 as part of the selected
edition. Never replace an already published same-version artifact, change its
recorded hash or rewrite a tag to disguise the modification.

The updater normally compares numeric versions. An installed upstream app with
the same number will not necessarily offer a CN localization update. Before
first migration, establish a tested same-version reinstall/migration entrypoint
that preserves settings and recovery data. A source switch, translated catalog
title or an empty update list is not proof the Chinese app package is installed.
Do not uninstall first as a shortcut. If no tested path is available, finish
local preparation and report that specific blocker.

The development installer exposes `migrate-cn` with `--from` and `--plan-only`,
or an exact `--expect-plan`, plus `migration-status`, `migration-verify` and
`migration-rollback` for a recorded transaction. Inspect the selected release's
`docs/CN-MIGRATION.md` before using these interfaces. The combined snapshot must
include the exact running installer, both catalogs and checked package bytes.
An `installReady: false` snapshot refuses execution before connecting; do not
edit that flag or create a success attestation to bypass integration.

The current implementation targets ID7 -> Walle CN. It preserves ordinary
same-version app data with independent recovery packages and permits only the
reviewed Waze log-presentation change at the same native version. Same-version
Store/updater/deploy replacements, downgrades, unknown source identities and
unmapped installed components are refused. The management candidate uses Store
0.9.38, updater 0.8.42 and deploy 0.8.15; the three map versions above stay unchanged.
These are preparation versions, not an instruction to install or a permanent
recommendation.

Ordinary `first-install --from` still skips healthy same-version apps. Do not
retry it as migration, relax the updater guard or set firmware-repair flags.
An interrupted transaction is inspected and restored through its own recovery
runner; do not start another installation or remove its journal. Verification
checks installed content and active CN catalog ownership; a genuine later online
update remains separate evidence. Returning to arbitrary official releases is
not implemented by these commands; rollback restores that transaction's old bytes.

首次迁入保留版本号的中文包，需要核对源码与哈希，并使用验证过的迁移或重新安装
入口。后续正常升级仍遵守版本和依赖规则，不能反复用同一个版本号发布不同内容。
官方原包镜像与国内版汉化包分别维护，定时任务不得相互覆盖。
当前迁移代码已具备离线测试覆盖，但缺少车机集成与公开发行验收。反复首次安装、
修改来源、提升标志或伪造修复状态都不能代替验收；中断后先读取事务，不从头重刷。

For the owner's later vehicle validation, record the actual CN channel
(`distribution: "walle-cn"`, `github: false`), installed package identity,
Chinese tile/settings/status/error/log pages, and an online update when a
genuinely newer compatible version exists. Retain before/after versions,
hashes, settings and restart/service results. Do not manufacture an update by
editing version numbers or overwrite packages merely to make an update appear.
Offline checks and owner photos remain separate from completed vehicle tests.
