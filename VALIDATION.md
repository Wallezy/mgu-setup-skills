# Validation / 验证

The environment helper must remain a local-only report: no package installation, network access, vehicle access or configuration writes. The separate mirror helper downloads HTTPS resources and saves source preferences locally; it never contacts a vehicle. Skill validation checks packaging, not vehicle compatibility.

环境检查脚本只生成本地报告，不安装依赖、不联网、不连车、不改配置。独立的镜像脚本可下载 HTTPS 资源和保存本地源偏好，不连接车辆。Skill 校验不证明车辆兼容。

## Repeatable local checks

```sh
python3 skills/mgu-setup/scripts/check_environment.py --json
python3 -m unittest discover -s tests -v
```

The skill-creator package's `quick_validate.py` can also validate `skills/mgu-setup` when available. It is an authoring tool, not a runtime dependency.

## Behavioral scenarios for maintainers

| Scenario / 场景 | Expected behavior / 预期 |
|---|---|
| Car disconnected / 未连车 | Prepare locally; no fabricated vehicle status |
| Required artifact not downloaded / 所需资源未下载完成 | Complete/verify staging before the corresponding planned vehicle write |
| Artifact checksum mismatch / 资源校验不符 | Block installation; reacquire from the intended source |
| Vehicle architecture changes after staging / 准备后更换架构 | Re-select compatible resources and repeat readiness checks |
| Existing supported recovery ready / 已有可执行恢复准备 | Do not delay recovery to download unrelated catalogs/apps |
| Root already works / root 正常 | Skip flash/enable/persist mutations |
| First flash, no coding backup / 无编码备份首次刷写 | Complete preparation; stop flash at missing backup |
| Read-only diagnosis with deploy 0.8.8 / 使用新版部署工具只读排查 | Exclude root `status`, including JSON/wrapper polling; observe passively or report unavailable data, never repair implicitly |
| Authorized manager repair / 已授权管理器修复 | Preserve before-state, use supported operation and record actual side effects; reuse applicable authorization |
| Only preflight records with verified=true / 仅采集记录且校验通过 | Mark supplemental; restoration readiness remains unmet without a compatible backup/restore path |
| Sparse coding DIDs or early scan stop / 编码编号不连续或提前结束 | Record coverage as incomplete/unknown; matching captured blocks and hashes do not certify completeness |
| Unknown HU architecture / 未知架构 | Do not assume ID7 or write an arbitrary image |
| Old install record, no tile / 有记录无入口 | Inspect registration and manager, official repair |
| Repeating animation, stable boot ID / 动画重复但启动未变 | Investigate UI/service; do not claim full reboot loop |
| Changed host key after restart / 重启后密钥变化 | Verify vehicle and route; do not globally disable checks |
| API works, asset times out / API 通资源不通 | Test asset; offline media or supported proxy |
| New app with old native dependencies / 新应用旧依赖 | Use declared dependency resolution |
| Retained target has known permission defect / 回滚目标有已知缺陷 | Refuse that target and identify a supported alternative |
| ID7 app rollback / ID7 应用回滚 | Check installed deploy capability, retained package and dependencies |
| ID8 app rollback / ID8 应用回滚 | Honor current implementation's refusal; no ID7 extrapolation |
| Snapshot from another firmware / 跨固件快照 | Honor firmware restrictions; no forced system-file restore |
| User asks only map removal / 只移除地图 | Do not remove Store or SSH |
| HUD installed, no video / 安装后无视频 | Distinguish install/activation/stream/display evidence |
| No supported recovery access / 无可用维护通道 | Preserve evidence and state firmware-recovery limits |

These are review scenarios, not claims that each was executed on hardware or by an independent agent. Add actual results and platform evidence before expanding the tested-support matrix.

这些是审查场景，不表示已经逐项实车或独立 agent 测试。扩大验证范围前必须补充实际结果。

## Authoring validation: 2026-11-09, diagnosis and capture boundaries

The entrypoint, recovery/Root references, both workflows and session template
distinguish passive diagnosis from repair, and capture integrity from restoration
readiness. Repository validation (21 Markdown files, 109 local links),
skill-creator quick validation, standalone packaging (18 files) and
`git diff --check` passed. The scenario rows above are review criteria, not
executed vehicle or independent-agent tests. No helper code or vehicle state changed.

入口、恢复/Root 参考、中英流程及会话模板已区分只读与修复、采集校验与恢复能力。
本次仅完成文档、结构和打包校验；保留历史实车证据，不新增实车验证声明。

## Authoring validation: 2026-11-06

- Skill frontmatter/structure validation passed.
- Five helper tests passed: absent executable, old Node, OpenSSH stderr output, timeout, and scope-specific readiness without claiming vehicle readiness.
- Local macOS arm64 report correctly identified Python 3.14.0, Node 18.20.3 and OpenSSH 10.5p1; the selected interpreter lacked cryptography, so the full profile returned not-ready.
- No vehicle action was performed while authoring this skill.

以上验证仅针对本次文档包与辅助脚本；本机完整环境检查因缺少 cryptography 返回未齐备，属于预期结果。

## OSS distribution acceptance: 2026-11-07

- Public root: `https://walle-jenkins.oss-cn-beijing.aliyuncs.com/mgu/`.
- The root manifest was fetched anonymously over certificate-verified HTTPS. Its SHA-256 matches the locally prepared snapshot: `0b318cb11e22f90ba51892986f66cf6221b26b5f69b5ebfdf6cec05d32ed2a88`.
- All 22 indexed files (43,442,484 bytes) were downloaded from OSS into a fresh acceptance directory and checked against that manifest. The ten component packages also match their catalogs' original upstream sizes and SHA-256 values.
- Both catalogs passed schema and cross-repository dependency checks; artifact URLs resolve within the OSS catalogs rather than GitHub.
- The pinned, unmodified upstream installer read both OSS catalog URLs directly with Node.js and downloaded all ten components into its official USB repository layout. The domestic-first planner selected OSS successfully. The shared preference remains `auto`.
- Twelve local tests cover environment checks, corrupt files, missing dependencies, invalid paths, failed downloads, source fallback and pinned version/hash mismatches.
- Validation does not establish worldwide reachability, in-car TLS support, installation success or HUD video output. No vehicle operation was performed.
- Cache headers rechecked after the owner's OSS metadata update: the root manifest and `idrive-apps/catalog.json` return `Cache-Control: no-cache`; `mgu-store/catalog.json` has no explicit Cache-Control header in that response.

## Owner-supplied photos: 2026-11-07

Four owner-supplied photos are published in [the showcase](docs/SHOWCASE.md).
They show the app entries, the Store, display-target settings, and actual HUD
map output on the owner's iDrive 7. They are visual evidence from that setup,
not another installation test, frame-rate measurements or a broader compatibility
claim. The photos have no GPS EXIF tag. They are copied without pixel edits.

## Upstream adaptation and local OSS update package: 2026-11-07

- Documentation covers app 0.6.4/service 0.9.3 driver settings, configuration backup/downgrade behavior, latency diagnostics, tile-name diagnosis and firmware-update setup. Historical vehicle evidence retains its recorded versions.
- A new complete mirror snapshot was generated from official catalogs at Store `8cfae23db27e51d86f84e65b13ce0592668d8df9` and apps `05e38eca8ca6f3bcde7e43d67127da664401caa8`. Its 22 indexed files and ten component packages passed size/hash and dependency checks. Catalog fields match upstream except artifact URLs.
- Prepared and remotely downloaded manifest SHA-256: `cb21bf4f988523c2894821e03bc92b95ccc27b495329b3021972fdbb18e39be7`. All 22 indexed files downloaded from OSS match this snapshot; content and cache metadata acceptance passed.
- The live old snapshot was downloaded again and verified before comparison. The upload delta has 12 files: four component packages, two source archives, five supporting/catalog files, and the final manifest. Applying the delta to the verified old snapshot reproduces all newly indexed files while retaining old packages.
- The unmodified installer converted the new local catalogs into its USB layout with all ten components. This test performs no vehicle installation.
- Skill validation, documentation links and twelve helper tests passed. The standalone skill archive was rebuilt.
- After the owner's upload, the original installer downloaded both live OSS catalogs and all ten components into its USB layout. A Node fetch guard restricted these 12 requests to the OSS prefix; they returned HTTP 200 without redirects.
- Final GET checks confirm `Cache-Control: no-cache` on both live catalogs, the root manifest, both upstream catalogs and the apps README. All six downloaded files still match the prepared snapshot byte for byte.
- The built-in GitHub update source remains a network dependency; this work does not introduce a domestic-only network mode or claim emulator/vehicle validation.

新版文件及可变目录、清单的缓存元数据已通过 OSS 验收。历史照片不代表新版已实车测试。

## Maintenance efficiency review: 2026-11-08

- Reviewed the separate completed maintenance session. The skill prefers a working updater, freezes targets before writes, reuses private preparation and separates update acceptance from optional map display diagnosis.
- A rerunnable offline Store refresh is documented separately from other app installation; USB/hotspot are conditional paths. No new vehicle-side import capability is claimed.
- Catalog planning limits each request to 20 seconds with zero curl retries. Artifact downloads retain 180-second request limits, two retries and size/hash verification. Thirteen tests passed, including timeout-to-mirror fallback and unchanged package verification behavior.
- A live `domestic-first` plan successfully selected OSS and checked catalog integrity/dependencies. It still lists Store 0.9.29, updater 0.8.31 and uplink 0.7.6; the recorded vehicle update installed newer versions. This probe did not download packages or certify a complete new mirror release.
- Documentation links, skill structure and standalone packaging passed. This is local helper/documentation validation; no vehicle or head-unit emulator was used for this skill revision.

## Authorized OSS CLI synchronization: 2026-11-08

- `tools/sync_oss.py` was exercised with ossutil 2.2.0 against the authorized mirror prefix. A prepared snapshot that no longer matched upstream was refused before upload; regeneration included the newly published mgu-render 0.6.13.
- Published Store catalog commit `5f2ac20566716711b97882ad1f37d11ef0e7deae` and apps catalog commit `05e38eca8ca6f3bcde7e43d67127da664401caa8`. Updated components: Store 0.9.30, updater 0.8.32, uplink 0.7.7, Python 1.0.3 and mgu-render 0.6.13. Map component versions are unchanged.
- Fourteen objects were uploaded, including metadata repairs. All 22 indexed files and ten packages passed public HTTPS size/hash/dependency acceptance; fixed-path files and the manifest have no-cache. Old packages remain; no ACL or bucket policy changes were made.
- Accepted manifest SHA-256: `50d77469608b7729cc744b2a4b4c09a236de58d6fc73c79efc5638a04b4ad630`.
- A second live run returned `unchanged` with an empty upload list. Nineteen local tests cover helper behavior, constrained targets, publication ordering, corrupt-resource refusal, rollback on simulated publication/acceptance failures, locks and cache handling.
- The configuration and CLI are local maintainer resources outside the repository. No credentials, downloaded packages or private vehicle records are distributed with the skill. Mirror validation is not vehicle/emulator installation validation.

## Root stable-release adaptation: 2026-11-08

- Official latest stable Release was v1.3.1 at review time; its tag and an isolated
  source checkout resolve to `1d3ba60a9aa8a79fe16e1c26488a89918ec1d928`.
  The skill records that reviewed revision and official Windows asset metadata.
- Reviewed source requirements, CLI arguments, discovery, enrollment, flash and
  persistence. GUI variant selection is mandatory, but CLI defaults to ID7;
  workflow examples therefore require explicit verified `--arch`.
  Persistence is verified separately from the overall CLI return code.
- The optional `--root-repo` local check passed for the isolated v1.3.1 checkout
  and rejected the existing older `f79134b5dee77a79fe2a72d24d0897f388d91816`
  checkout. It does not fetch, import or execute Root code, and an invalid Root
  checkout does not block a Store-only environment profile.
- Twenty-six tests passed, including seven new source-checkout tests: pinned
  revision, modified/missing tracked files, nested repository paths, missing Git
  metadata, missing Git/timeouts, preserved local data and scope-specific readiness.
- On macOS arm64, the selected existing Python 3.14.0 environment with
  cryptography 46.0.7 and OpenSSH 10.5p1 passed the Root source profile.
  The reviewed upstream CLI's `--help` ran successfully without a diagnostic
  action. The old checkout and desktop application settings were not changed.
- Gitee's v1.3.1 tag resolves to the same reviewed official commit. Fetching that
  tag into the isolated local checkout succeeded and the Root source check passed.
  Domestic-first can select this matching source; fallback still verifies the
  selected revision. OSS contains Store/apps only. No Root artifacts or private
  data were uploaded.
- Skill structure, local documentation links and standalone packaging passed.
  This is local preparation and helper validation, not a vehicle/emulator flash
  test or a Windows executable test; historical vehicle evidence is unchanged.

## Catalog icons and mirror maintenance: 2026-11-11

- Forty-five unit tests passed, including official catalog/icon digest checks,
  PNG format/CRC/dimension limits, icon-only release changes, public MIME/cache
  checks, historical package header repairs, resource-before-index publication,
  rollback, default-branch discovery and preserved divergent working branches.
- Gitee accepted and read back the Store default branch and nine new tags.
  The other three mirrors matched in the default-branch-and-tags scope.
  The divergent `safe-mode` working branch was preserved and reported; no
  force push or deletion occurred. Strict `--all-branches` still blocks on
  such a conflict.
- The authorized OSS prefix accepted 22 object writes: new packages, two
  content-addressed PNGs, source archives, mutable metadata, the final manifest
  and two existing packages uploaded with identical bytes to repair cache headers.
  Public downloads verified all 24 indexed files plus the manifest, dependencies and PNGs;
  cache headers and PNG content types passed, including historical header repairs.
  Manifest SHA-256:
  `f5a248369c415558fb3ffe6a95504cd4da4017c6e79da0d54e38ea1c17cfb3fb`.
- Mirrored versions: Store 0.9.35, deploy 0.8.10, updater 0.8.38, render 0.6.19,
  uplink 0.7.9, Python 1.0.3, app-privacy 1.7.1; map app 0.6.7,
  waze-on-cluster 0.9.10 and cluster-render 0.5.3. A second read-only sync
  returned `unchanged` with no uploads.
- The unmodified published installer converted both local catalogs with Node
  network requests disabled. All ten resulting packages passed size/hash checks.
  Its `usb-repo` retains icon paths without copying PNGs; this check does not
  validate USB icon display. OSS and complete mirror snapshots include both icons.
- Local repository links, skill structure and inspect-profile readiness passed;
  the standalone archive was rebuilt. The inspect profile requires only Python:
  the selected system interpreter lacks cryptography, so this check does not
  certify readiness for a Root write.
- Skill guidance covers vehicle-side read-only capability and wrapper fallback,
  main-only Root recovery commands, HUD Off/profile preferences, crash-log coverage
  and removal dependency checks. Existing vehicle evidence is unchanged.
  No vehicle, emulator or desktop application was modified or tested in this work.

## Hangzhou custom-domain migration: 2026-11-11

- The entire Beijing `walle-jenkins/mgu/` prefix was inventoried: 70 objects
  (69 files and one directory marker), 192,362,542 bytes, including historical
  packages and the existing hidden metadata files. All were copied to
  `walle-mgu/mgu/`; the source and the target's prior test file were preserved.
- Every copied object was read through `https://mgu.walle.pw/mgu/` and checked
  against the staged SHA-256, size and original content/cache/disposition headers.
  Source inventory stability was checked before and after copying. Resource
  files preceded both catalogs, and `mirror-manifest.json` was published last.
  Historical objects retained their original headers, including absent cache
  headers; no claim is made that every archived package uses immutable caching.
- The active manifest remains
  `f5a248369c415558fb3ffe6a95504cd4da4017c6e79da0d54e38ea1c17cfb3fb`;
  this is a relocation of the accepted snapshot, not a component upgrade.
- The maintenance helper accepts the explicitly mapped custom domain and
  verifies its enabled OSS bucket binding and HTTPS certificate through the
  authenticated API. It supplies the correct Hangzhou region/endpoint and a
  positive ossutil attempt count. A same-byte NOTICE upload through that helper
  and subsequent public acceptance passed.
- Forty-seven unit tests passed, including custom-domain destination isolation,
  binding/certificate refusal cases and explicit region/retry arguments.
  The skill's live domestic-first planner selected both new catalog URLs without
  fallback. The shared default remains `auto`; source preference is not geolocation.
- A read-only maintenance comparison prepared newer deploy 0.8.11, updater
  0.8.39 and cluster-render 0.5.4 artifacts separately. They were not published
  during this migration; the migrated versions remain those recorded above.
- Skill validation, 114 local links and packaging passed. The daily maintenance
  destination uses Hangzhou; Beijing remains a retained compatibility snapshot.
  No vehicle source, application, network setting or firmware was changed.

## CN distribution routing: 2026-11-11

- The Skill distinguishes the official edition, an unmodified download mirror,
  and the separate Walle CN forks. The CN edition is explicitly development-only:
  no approved vehicle installation release is recorded.
- Existing maintenance and both language workflows route an explicit CN choice
  through distribution readiness, without substituting the official installer
  or adding the legacy removable mirror again.
- Two independent, read-only agent reviews exercised the scenario of a working
  official Store, working SSH, unreachable GitHub and a requested CN switch.
  They identified ambiguous routing in the general update and map-source steps;
  those steps now preserve the chosen edition. This was instruction review, not
  an installer, emulator or vehicle test.
- Forty-seven helper tests, Skill structure validation, 124 local documentation
  links and standalone packaging (19 files) passed. The official Gitee/OSS
  maintenance mappings remain separate from the reserved CN release channel.
- Fork creation, source commits and unit tests do not establish CN migration,
  self-update, recovery or public OSS installation readiness. Historical vehicle
  evidence remains associated with its original versions.

## CN localization preparation: 2026-11-11

- Distribution guidance records the initial CN localization versions
  (`robertn_waze_cluster` 0.6.7, `waze-on-cluster` 0.9.10,
  `cluster-render` 0.5.4), with exact source/package identity separate from
  the displayed numeric version.
- The procedure distinguishes initial same-version migration from a later
  higher-version update. It does not treat translated catalog text or an empty
  update list as proof that a localized application package was installed.
  Published same-version artifacts and tags must not be replaced.
- The session record includes the active edition, GitHub capability, Chinese
  menu/status/error/log-page observations and separate migration/update results.
  The owner's planned vehicle tests are pending; none is recorded as completed.
- Read-only inspection of the CN Store installer and deployer confirms that
  healthy same-version apps are skipped, including with `first-install --from`;
  no supported CN migration entrypoint is implemented at the recorded revision.
  The guidance treats this as a missing capability, not a retry or evidence gap.
- Repository validation (124 local links), Skill structure validation and
  standalone packaging (19 files) passed. These are documentation checks;
  application localization tests are recorded in the application repository.

## Full-distribution switching guidance: 2026-11-12

- The switching route covers the computer-side installer/bootstrap, Store,
  updater, deploy tool, installed dependencies/apps and future update sources.
  A component plan distinguishes retained identical packages, migrations and
  unmapped third-party components; it does not reinstall every optional app.
- Instruction review distinguishes a mirror-only change, a same-edition update,
  a full switch in either direction, an unknown fork and same-version/different-
  content packages. Healthy SSH is reused. An absent migration entrypoint allows
  preparation only; changing a catalog URL cannot establish successful migration.
- Skill structure validation, 133 local links, whitespace checks and standalone
  packaging (19 files) passed. No installer implementation, vehicle operation or
  migration success is established by this documentation change.

## Migration candidate routing: 2026-11-12

- Guidance records the candidate's complete-snapshot installer, exact-plan
  binding, ID7-only scope, retained application data, independent recovery
  packages and separate transaction status/verification/rollback.
- Healthy same-version apps still skip through ordinary first-install.
  Same-version maintenance binaries, unmapped components and unknown ownership
  remain refusals; the agent must not rewrite readiness flags or attestations.
- The recorded deployment, updater and installer tests are offline fixtures.
  Neither a real HU emulator nor a vehicle migration has been validated;
  vehicle-installation readiness remains false.
