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
