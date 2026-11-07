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
