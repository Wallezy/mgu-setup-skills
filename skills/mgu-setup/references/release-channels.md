# Internal release workflow / 内部发布与明确请求的测试版流程

Read this reference only for an explicitly requested Beta installation/trial,
maintenance of a previously explicitly selected Beta installation, or maintainer
release work. It is not a user-facing menu. Ordinary installation and updates use
the production release; call it 正式版, not Stable. Do not proactively mention or
recommend Beta, ask users to choose a channel, or offer Beta when production is
unavailable. “Latest” alone is not an explicit Beta request. A maintainer's request
to publish both channels does not authorize installing Beta on a user's vehicle.

Use one Skill and one set of component IDs. `stable` remains the internal
production identifier. Beta requires the user's explicit request; reuse that
request during the session. Preserve a previously explicitly selected Beta
installation during routine maintenance rather than silently switching it.
Root 工具仍按自己的审阅版本选择，不随商店通道切换。下表仅用于操作者核对路径，
不得作为普通用户安装前的二选一问题。

| Channel | Root | Admission |
| --- | --- | --- |
| Stable | `https://mgu.walle.pw/mgu/cn/` | Reviewed upstream, expressly owner-reviewed or vehicle-validated candidate; exact bytes and public acceptance |
| Beta | `https://mgu.walle.pw/mgu/cn/beta/` | Explicit owner trial, exact candidate/plan, successful offline checks and public package/channel acceptance |

These roots identify channels, not proof that a usable release is published.
Read current publication records and verify the selected snapshot. The official
raw-package mirror under `/mgu/mgu-store/` and `/mgu/idrive-apps/` is neither CN channel.
For an existing Beta installation, retain its recorded explicit channel during
routine maintenance; the Stable default does not silently switch that vehicle.
Official `mirror_resources.py` snapshots and CN `cn-manifest.json` snapshots
use different schemas. Validate CN resources with the matched CN tooling.

## Owner Beta trial / 车主 Beta 实车试验

1. Establish the requested scope and current vehicle architecture, versions,
   access and health using saved records plus fresh observations. Existing
   healthy SSH needs no Root reflash. Reuse confirmed power and backup conditions.
2. Freeze one complete Beta snapshot: installer, both catalogs, component
   dependencies, versions and hashes. Check its source/installer CI and public
   Beta acceptance. Keep original payloads, application settings and source/channel
   state recoverable. A BimmerCode coding backup does not replace those bytes.
3. Use the selected installer's documented trial route. The first implementation
   supports existing-store ID7 migration: `migrate-cn --channel beta --plan-only`
   with the local `--from` snapshot. Planning stages temporary files and compiles
   candidates; it is not a strictly read-only inventory.
4. Execution requires `--channel beta`, `--expect-snapshot` and `--expect-plan`
   for that exact reviewed snapshot/plan. These are operator interfaces; do not
   hand owners shell edits or ask them to set readiness flags. Stable's
   `installReady` and successful integration records stay unchanged during a trial.
5. Observe any normal restart, actual active channel, one row per component,
   Chinese menus/status/log page, settings and boot stability. Verify domestic
   catalogs and downloads. A genuine later component/self-update and recovery
   remain separate tests; never fake higher versions to create an update.

The owner's explicit choice of real-vehicle validation can replace the emulator
step. Keep offline checks, vehicle results and formal release approval separate.
Stop the affected write for an incompatible version, missing old payload,
unexpected identity, failed integrity check or incomplete recovery. Do not
relax downgrade/unknown-source/ID8 refusals to make a trial run.

车主可以选择“跳过不可用模拟器，直接实车试验”，这项选择不是实车通过记录。
默认正式安装和明确 Beta 试验使用不同准入条件，不能要求先实车成功才能首次试验，
也不能因允许试验就给普通用户开放正式安装。

The initial map candidate (app 0.6.7, service 0.9.10, renderer 0.5.4) is not a
permanent target. An installed official service 0.9.11/0.9.12 cannot be silently
downgraded into it. Review the target's map-URL patch/deactivate compatibility
and prepare a compatible newer CN candidate when needed.

### Resume a prepared trial / 继续已准备的试验

Use the private trial handoff's exact **migration snapshot** and **online-update
snapshot**, with their recorded publication and CI results. Recheck their local
hashes; download or rebuild only a missing/mismatched item. Do not replace a
reviewed snapshot with a newer catalog midway through the vehicle session.
The migration snapshot's archived manifest and local files remain pinned when
the online-update snapshot replaces the public catalog. Do not compare the
older snapshot's mutable catalog paths against the newer live catalog; validate
the current public catalog against the online-update snapshot instead.

The November 12 owner trial uses deploy 0.8.17 with Store 0.9.38 for migration and
deploy 0.8.18 with Store 0.9.39 for the subsequent real online update. Its initial
snapshot requires the complete Store and map-app recovery packages verified
against the saved vehicle files; recheck their hashes on reconnection. Other
starting states use a reviewed snapshot with deploy 0.8.18 or later, whose
preflight also rejects a runtime-only recovery package for an installed UI.
These version numbers are a
recorded test pair, not permanent minimums or proof of vehicle acceptance.
Deploy 0.8.16's migration is a known failed candidate: its check rejects RHMI
files consumed by MainApp, and its runtime-only recovery omits the UI. Do not
reuse that candidate for a new trial.

Before the update, finish the migration verifier and confirm the actual Store
tile opens. Its recovery package must include both the installed runtime bytes
and the complete matching RHMI resources. A registered tile is insufficient.
Once a subsequent update changes payloads, the migration journal is historical:
use that update's supported component rollback, not a blind old-transaction
rollback or a forced migration verification.

Read the updater's own network/source state or use its supported fetch path.
MGU uplink may deny root UID Internet access while the Store's allowed UID is
online; a root `https.get` failure does not establish that the hotspot is down.

上车前把资源、校验、两个固定快照与恢复材料准备完。上车后只做当前身份与版本检查、
执行切换、确认商店入口、在商店里在线更新、正常重启与结果记录。
网络验收走更新器实际使用的访问路径，不用 root 直连探测反复要求用户改热点。

## Promotion and maintenance / 晋升与维护

Use the CN Store's selected release tooling and policy:
[CN-RELEASE-CHANNELS.md at 60585be](https://github.com/Wallezy/mgu-store-cn/blob/60585be972822d0a59dfd9931bd3070f857e2d8a/docs/CN-RELEASE-CHANNELS.md).
Do not reintroduce the old blanket vehicle-test gate:

| Work | Publication and evidence |
| --- | --- |
| Reviewed upstream synchronization and CN compatibility changes | Publish Beta then Stable from the same payloads in one release task; `reviewed-upstream` evidence. Vehicle tests are recorded honestly, not a required gate. |
| Small improvement explicitly authorized for both channels without a car trial | `owner-reviewed` evidence; complete source checks, review and reproducible builds. |
| Separate development feature/trial | Beta only until wider release is requested; preserve it when publishing an unrelated shared change. |
| Claimed vehicle-validated release | Evidence must bind actual installation, migration, update order, restart, settings, download/self-update and rollback results to the exact snapshot. |

All routes bind fixed commits, successful applicable CI, complete dependencies,
immutable versioned payloads, a real review/evidence report and public download
verification. `prepare_cn.py`, `promote_cn.py` and `publish_cn.py` are maintainer
tools; source pushes, public publication and vehicle operations are separate.
Review-only releases must retain `fully_vehicle_validated: false`.

When Beta has a separate trial, compare both channel inventories before building.
Use the supported `owner-reviewed` route for explicitly authorized dual-channel
updates with `channel_variants`: pin each full catalog entry for both channels,
the exact `--stable-base`, and the prepared Stable candidate. Shared components
must match Beta; unchanged Stable-only components use `retained_components`.
Retain a whole repository only when none of its components should change.
Keep the Beta trial in Beta, and publish only the reviewed Stable variant.
Changed Stable baselines require replanning. All source, dependency, reproducibility,
CI and public-download checks still apply; this route does not claim vehicle validation.

Keep three-part numeric versions, with upstream version/CN revision in release
records. Changed published bytes require a new component version, even within
Beta. Promotion preserves payloads; it does not rebuild or force downgrades.
Release notes should be short, user-facing Chinese: what changed and why it
matters, with no invented improvements or internal build details.

For a trial with two snapshots, retain both and record the tested path to the
final snapshot. Pending tests stay pending. Keep private vehicle data out of
public evidence. Daily monitoring and official backup-source synchronization
do not themselves authorize new merges, CN publication or vehicle writes.
