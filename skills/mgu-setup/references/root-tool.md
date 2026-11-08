# Root tool preparation / Root 工具准备

Read only for first root, access repair, or updating the computer's Root tool.
Working SSH and Store/app updates do not require downloading or running Root again.

仅首次解锁、访问修复或更新电脑上的 Root 工具时读取。已有 SSH 正常、仅更新商店/应用时跳过。

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
