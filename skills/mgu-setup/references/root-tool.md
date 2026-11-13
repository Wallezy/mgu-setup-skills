# Root tool preparation / Root 工具准备

Read only for first root, access repair, requested SSH close/disable, or updating the computer's Root tool.
Working SSH and Store/app updates do not require downloading or running Root again.

仅首次解锁、访问修复、明确要求关闭/撤销常驻 SSH 或更新电脑上的 Root 工具时读取。
卸载范围、顺序及 `close`/`disable` 的验证边界见[卸载说明](recovery.md#removal)。
已有 SSH 正常、仅更新商店/应用时跳过。

## Select and reuse / 选择并复用

[root-tool.json](root-tool.json) records the reviewed stable release, exact commit
and official Windows asset metadata: **v1.3.1**, reviewed on **2026-11-08**.
It is a reviewed baseline, not a permanent claim about the latest release.

For new online preparation, check official stable Releases once. If it still
matches this record, reuse a verified local copy. If a newer stable release or
replacement asset exists, review its relevant changes and requirements before
pinning it in the private session. This helper verifies the recorded baseline;
a newer reviewed release needs equivalent revision/integrity checks recorded
separately until the skill's baseline is updated. Do not substitute moving `main`, a prerelease or an older
mirror silently. An offline resume can reuse its already reviewed/pinned copy
without a new release lookup.

新准备时查询一次最新正式发布；已有本地副本匹配审阅版本就复用。新版本或同版本附件被替换时，
先审阅变化再锁定，不能把 `main`、预发布或滞后的镜像当成所选版本。离线续作复用已审阅的固定版本，
不为重复查询“最新”强制联网。检查器仅核验所附基线；采用更高的已审阅版本时，另行记录等效的
提交与完整性检查，不能把版本不匹配改写成“v1.3.1 校验通过”。

<a id="coding-capture-limits"></a>

## Coding capture limits / 编码采集边界

The 2026-11-09 review of upstream commit
`a43ac32029d9d4f93d1da649042381fb995e7b55` found `mgu7/preflight.py` on
main, outside the reviewed **v1.3.1** release/Windows bundle. This is a
version-specific review, not a claim about future releases. Do not switch to
main or require a new capture for routine Store updates.

该提交的 `preflight` 是补充编码记录，不是已经验证的恢复备份。
它不在本 Skill 审阅的 v1.3.1 正式包中；后续版本应核对实际实现，不能为了采集而追 main。

- `_read_did()` returns `None` for both negative and absent responses;
  `_scan()` stops after 16 consecutive such results. A gap of unsupported DIDs
  can therefore hide later valid blocks. This is static analysis, not a vehicle
  reproduction. 连续 16 个不存在的编号可能导致提前结束扫描，不能把它等同于整段完整读取。
- `verified=true` means a nonempty set of captured coding blocks matched a
  second read. It does not verify unvisited blocks or the full identification
  record. File hashes check file integrity, not capture coverage or restorability.
  两次一致只验证已采到的编码块；哈希一致只验证文件完整性。
- The output includes coding records and restore guidance, but this implementation
  has no automatic restore or verified BimmerCode/E-Sys import path. Do not
  assume `coding_MGU.txt` or `backup.json` can be imported by those tools.
  文本/JSON/恢复说明不是可直接导入编码工具的证明，也不是完整固件备份。

Record capture integrity, scan coverage/stop reason, and restoration capability
separately in the [session record](session-record.md). If only this capture exists,
mark it supplemental and leave coding recovery readiness unmet. Continue local
preparation, but do not authorize first flash on that evidence alone; establish
a compatible tool's matching HU/MGU backup and supported restore path. A confirmed
existing backup can be reused without recapturing it.

分别记录采集一致性、扫描范围/停止原因、可用恢复工具与格式。只有此类采集时，
编码恢复条件仍未满足；可继续本地准备，不能因此放行首次刷写。
已有匹配且确认可用的编码备份应复用，无需重复备份。

## Programming recovery commands / 编程状态恢复命令

The 2026-11-11 review of main commit
`b1fca089a679cecad737ef9ce23fb66762700057` found `enter-prog` / `exit-prog`
outside the reviewed **v1.3.1** release. They change diagnostic/communication
state; `enter-prog` can reset the ECU. They are not read-only probes or automatic
fallbacks for a failed SSH connection. A best-effort `exit-prog` returning
`EXIT_OK` is not proof of recovery: observe actual reachability, boot continuity
and service health separately.

The same main revision removes CLI confirmation prompts for `flash`, `fix-key`
and `close`; `--yes` is a compatibility no-op. Required scope, architecture,
power and backup checks must be established before calling such a reviewed
version, not delegated to an expected interactive prompt.

以上是主分支行为审阅，不代表 v1.3.1 Windows 正式包已包含。编程状态命令可能改变诊断、
通信状态或重启 ECU，不能用于只读检查或自动修复 SSH。退出码不证明车机恢复；
新版 CLI 不再询问确认，也不等于可以省略既有写入条件。

## Prepare source locally / 本地准备源码

Use a private directory outside this skill and outside an existing tool checkout.
For macOS/Linux, or Windows using Python, clone the release tag from the configured
upstream/Gitee source and verify its full commit against `root-tool.json`.
With `domestic-first`, a missing or mismatched Gitee tag requires the configured
official fallback or a report of the missing version; OSS currently mirrors only
Store/apps, not this Root tool.

源码放在 Skill 和已有工具目录之外的私有目录。按来源偏好获取正式标签，并核对完整提交；
Gitee 标签缺失/不同步时，按既有偏好回退官方源或报告缺少版本。现有 OSS 不含 Root 包。

Example local preparation, with a new destination chosen for this session:

```text
git clone --branch v1.3.1 --depth 1 https://github.com/cauliflowermossgrape/idrive7-8-ssh-root.git <private-root-folder>
python -m venv <private-runtime-folder>
<venv-python> -m pip install -r <private-root-folder>/requirements.txt
<venv-python> <skill-folder>/scripts/check_environment.py --profile root --root-repo <private-root-folder> --json
```

Select the actual interpreter path (`bin/python` on macOS/Linux, `Scripts/python.exe`
on Windows). Reuse an existing compatible environment rather than creating one
each time. The source route requires Python 3.9+, cryptography >=41, OpenSSH,
and Git for this checkout verification. It does not require Node.

The helper checks the checkout root, exact revision and tracked-file integrity;
it never imports the downloaded Root code, fetches a repository or contacts a
vehicle. Inspect local untracked executable code before running the upstream
tool: Git's clean tracked state alone is not a complete execution audit.
A source ZIP without Git metadata needs separate provenance/file verification;
do not bypass a failed checkout check by deleting `.git`.

助手应直接完成授权范围内的本地准备，不把这些步骤转交车主。复用已有 Python 环境；
新版放独立目录，不覆盖旧工具、`data/enrollments` 或日志，不把整个旧 `data` 覆盖到新版本。
后续调用使用本次核验的绝对路径，并写入私有会话记录，避免又调用旧项目目录。
检查器只查本地 Git 版本和已跟踪文件，不执行下载代码或访问车辆；未跟踪的可执行代码仍须审阅。

## Windows executable / Windows 发布包

The official Windows ZIP is an alternative to the Python source route. Verify
its size and SHA-256 using the release record, then keep the entire `MGU-SSH`
folder together, including `_internal`, `data` and `locales`. A metadata digest
is not proof until the downloaded file matches it. This route needs system
OpenSSH and upstream's ENET administrator context, but no separate Python.
It is not a macOS app.

Windows 可选官方 ZIP：校验实际下载文件的大小和 SHA-256，保留完整目录，不能只复制 exe。
此路径不需另装 Python，但仍需 OpenSSH 及上游要求的管理员环境。不能在 macOS 使用该 exe。

## Apply the reviewed behavior / 使用已审阅行为

- **Explicit architecture:** v1.3.1 GUI requires a selection, but CLI still
  defaults to `id7`. Always supply the verified `--arch id7`, `id8-bdc3` or
  `id8-bcp` for a Root write. An ID8 family alone does not distinguish BDC3/BCP;
  a VIN or model name alone is insufficient. Do not use `--force` to bypass an
  unsupported BTLD. 未知变体不得默认 ID7，也不能强行越过兼容性检查。
- **Discovery:** v1.3.0 adds macOS/Linux multi-interface discovery; v1.3.1 restores
  Windows broadcast fallbacks. A failure to discover is a network/tool-version
  question before it is an SSH repair decision. 先核对网卡、路由、版本及已观察的网关。
- **Retries:** v1.3.0 handles specific post-reset diagnostic-session delays and
  transient `22 17 2A` / NRC `0x21` readback. Let the reviewed tool perform its
  bounded retries; a final failure stops the write path. Do not automatically
  rerun the whole flash. 内置重试不是失败后无限重刷的授权。
- **Authentication:** distinguish a locally unreadable Windows key file from
  a unit rejecting a readable key. Do not infer `fix-key` from “Permission denied”
  alone. 先区分本地文件权限和车机公钥拒绝，`fix-key` 仍是重新刷写。
- **Completion:** the CLI calls persistence after flash/enable, but its final
  return value does not by itself certify `run_persist()` success. Verify
  persistence/debug state and a fresh root login, and preserve applicable logs.
  Check coding restoration independently; do not equate exit code 0 with all
  stages verified. 编码备份和 Digital Key 配对仍是独立事项。

This review and local preparation do not certify flash, recovery, hardware
compatibility or emulator behavior. Root source updates do not require reflashing
a head unit whose existing SSH remains functional.
