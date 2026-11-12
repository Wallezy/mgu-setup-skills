# Stable and Beta / 正式与测试通道

Use one Skill and one set of component IDs. Default to **Stable**. Use **Beta**
only when the owner explicitly selects it; reuse that selection during the
session. A missing Stable release is not permission to substitute Beta.

普通用户默认 Stable；维护者可明确选择 Beta。不用另发一份容易过期的测试版 Skill，
也不同时安装两套商店。Root 工具仍按自己的审阅版本选择，不随商店通道切换。

| Channel | Root | Admission |
| --- | --- | --- |
| Stable | `https://mgu.walle.pw/mgu/cn/` | Validated candidate promoted without rebuilding payloads, then public acceptance |
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

Review upstream -> adapt CN/localization -> CI and candidate build -> publish
Beta -> owner vehicle validation -> promote the same tested bytes -> Stable
publication and public acceptance.

`release/prepare_cn.py --channel beta`, `release/promote_cn.py` and
`release/publish_cn.py` belong to the reviewed CN Store checkout. Read its
`docs/CN-RELEASE-CHANNELS.md` for the exact interfaces. Source/package preparation,
public upload and vehicle execution are separate actions with separate evidence.

Promotion binds the exact Beta manifest hash and real private validation report.
It requires recorded installation, migration, component-order, restart, settings,
download-channel, self-update and rollback results. It preserves package, icon,
bootstrap and corresponding-source bytes; do not rebuild after vehicle testing.
Keep vehicle identifiers, credentials and raw private logs out of public evidence.
When a trial uses two snapshots, the evidence names the final online-updated
snapshot and records the path from the initial migration snapshot. Pending
screen, update, rollback or component-order checks remain pending; do not mark
them passed just because the owner says the installation finished.

Numeric component versions stay compatible with the updater; channel identity
is separate metadata. Published package bytes are immutable: another code change
needs another component version, including Beta iterations. Beta-to-Stable does
not force a downgrade; use compatible Stable bytes/newer versions or the supported
transaction recovery.

The daily maintenance task tracks those stages and recommends adaptations.
Automatic official mirror sync does not authorize automatic CN source merges,
Beta/Stable publication, vehicle writes or marking tests passed.
