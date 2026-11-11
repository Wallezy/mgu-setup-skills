# Store editions / 商店发行版

Choose the Store edition separately from the computer's download preference.
Reuse an explicit choice. If the user asks to switch editions, identify the
installed updater and preserve its sources, origins, aliases and recovery
inventory before preparing the matching release. An existing, healthy SSH
connection needs no Root reflash.

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

## Current readiness / 当前可用状态

As of 2026-11-11, the CN repositories contain source and local test work.
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
