---
name: mgu-setup
description: Set up and maintain an owner-authorized BMW MGU over ENET using SSH and Store tools. Use for environment checks, backup preparation, initial root, Store setup, full-distribution switch preparation and supported migration, map/HUD setup, updates, and supported rollback or removal. Supports Chinese and English.
license: GPL-3.0-only
---

# MGU setup and maintenance / MGU 安装与维护

Execute the user's requested work with the selected distribution's supported tools and observed vehicle state. Respond in the user's language. This skill covers a lifecycle; a request for one operation does not authorize all operations.

## Choose one route / 先选路径

Read only the procedure relevant to the request:

- Switch the full distribution / 切换整套发行版: [store-distributions.md](references/store-distributions.md#switch-distribution). Cover the computer-side installer, Store/updater/deploy tools, dependencies, installed apps and their update channels. Use this before ordinary updates when moving between official, Walle CN or another fork; a mirror-only change follows the source route.
- Existing Store/app update or resume: [maintenance-update.md](references/maintenance-update.md). Start with saved preparation, not first setup. U 盘和热点不是所有更新的统一前提。
- First setup, Store restoration or map/HUD configuration: [Chinese workflow](references/workflow.zh-CN.md) or [English workflow](references/workflow.en.md).
- Root tool preparation/version check: [root-tool.md](references/root-tool.md). Reuse the reviewed release, verify the selected local checkout, and explicitly select the HU variant; Store/app updates do not need a Root tool refresh.
- Access failure, unstable boot, downgrade or removal: [recovery.md](references/recovery.md). Working SSH needs no flash/enable/persist.
- Source selection, OSS preparation or acceptance: [network-mirrors.md](references/network-mirrors.md). Skill/mirror maintenance checks include live OSS versions and dependencies.
- First-install distribution selection: [store-distributions.md](references/store-distributions.md). Select the matching installer and complete distribution separately from download preference; respect release readiness.
- CN Beta trial or Stable promotion: [release-channels.md](references/release-channels.md). Stable is the default; Beta requires the owner's explicit choice and a fixed candidate.
- Historical versions and validation limits: [evidence.md](references/evidence.md).

## Execute with minimal repetition / 复用准备，直接执行

1. Reuse relevant private session records, key paths, backup inventories and local packages. Verify fresh vehicle identity/access and installed versions; do not reuse stale IPs as facts. With no car, finish local preparation only.
2. Establish scope and applicable power/backup prerequisites. Honor current authorization and confirmations; ask only for missing or changed conditions. A routine app update does not require repeating first-root preparation.
3. Prefer the working Store/updater for routine updates. Choose the actual package path before configuring networks; official `first-install --from` is an ENET option for Store setup/repair or a needed offline refresh, not a mandatory prelude or an all-app installer. USB/hotspot setup is conditional.
4. Before the first write, lock selected sources, versions, hashes and dependencies. Reuse valid local resources and download only missing/mismatched files; use the scoped environment profile. In the official edition, reuse or ask once for the map apps' Official GitHub versus Domestic mirror source; follow [network-mirrors.md](references/network-mirrors.md) for switching and the built-in Store exception. A selected CN edition follows its distribution readiness and managed channel, without adding the legacy mirror again. Do not chase new releases mid-update or install the same component twice unless compatibility/recovery requires it.
5. Record readiness in a private [session record](references/session-record.md), execute authorized writes sequentially, verify installed/active/displayed results, and clean up task-only settings. Continue from the checkpoint when resumed. A prepared Beta trial reuses its exact migration and online-update snapshots; see [trial handoff](references/release-channels.md#resume-a-prepared-trial--继续已准备的试验).

Missing resources or prerequisites block the affected write, not independent preparation. For diagnosis or an already prepared recovery, do not download unrelated packages or repeat a full mirror audit. Prepare missing runtimes in an isolated environment when needed; never disable TLS checks. Local hashes alone do not establish origin.

## Operational invariants

1. Follow applicable local instructions and inspected upstream behavior. Reuse the same-version review; inspect changed or uncertain code. A command named `status` is not necessarily read-only: historical `patchd.js status` started another daemon, and ordinary deploy status can repair directories and restart the app manager. Verify the vehicle-side `--read-only` capability; a newer computer wrapper can fall back to repairing status on an older unit. For read-only requests, exclude that fallback and report unavailable observations instead; see [recovery.md](references/recovery.md).
2. Before first flash, establish owner authorization, supported HU architecture, coding backup and appropriate stable power. Reuse applicable answers in the active session. Missing prerequisites block flashing, not independent preparation. Do not automatically choose an unknown architecture, run `fix-key` or retry a failed flash.
3. Flash provisions debug/SSH access, not the Store. `enable` repairs access; `persist` changes SSH lifecycle. Working access needs neither. Current combined commands may include persistence.
4. Use the selected distribution's supported installer for Store setup/refresh and Store/updater operations for apps. Ordinary CN installation uses validated Stable; an expressly requested owner Beta trial follows [release-channels.md](references/release-channels.md). Do not hand owners shell edits, manually patch binaries, fake network/USB state or deploy bespoke executables. App builds use an available HU SDK donor; never redistribute it.
5. Prefer published artifacts and declared requirements. Record source revision, catalog versions and size/hash verification. Downloaded is not installed; registered is not visually observed; HUD software installed is not HUD video verified.
6. Separate coding, access, deployment and patch-original backups. None is a complete firmware image. A coding capture's `verified` flag or matching hashes do not establish complete coverage or a usable restore path. Confirm the matching backup format, restoration tool and coverage before marking recovery ready; see [Root capture limits](references/root-tool.md#coding-capture-limits). Keep VINs, keys, firmware-derived files and logs outside this repository.
7. Serialize writes; inspect each result before the next mutation. Stop on identity mismatch, failed checksum, unsupported target, new crash loop, failed rollback or unexplained mode/owner changes. Retry downloads only while progress or a changed network path justifies it.
8. Use the normal restart offered by Store/installer/app. Do not repeatedly reset a looping HU or stop/restart `carplay.service` or `aapd.service` as a shortcut. A connection drop during a requested reboot is not a reason to reflash.
9. Verify host-key changes using the physical ENET connection and fresh vehicle identification. An ephemeral host-key path supports diagnosis; it does not justify ignoring every warning. Keep strict checking after accepting a verified key.
10. Distinguish published-component maintenance from development. Apply the chosen project's validation requirements, honoring an owner's explicit choice to perform a controlled vehicle trial instead of an unavailable emulator. Record that method; it does not waive compatibility, backup or recovery checks and does not establish Stable approval. Never present documentation checks, generic Linux tests or upstream claims as local vehicle tests.

## Completion

Report the verified layer: local readiness, authenticated connection, installed versions, tiles, stable boot, enabled patch or observed HUD video. Keep before/after evidence, hashes and cleanup status. Restore temporary proxy settings and close task-only tunnels when finished; preserve owner settings.

For an update-only request, finish after target versions, required activation/restart checks, service health and cleanup pass. Mark navigation visuals unverified when no active phone navigation is available; do not expand into map troubleshooting or reboot solely to obtain a picture.

If a physical screen or unavailable coding tool is required, finish independent work, give the concrete remaining action and state the verification limit. Do not fabricate completion or promise recovery from inaccessible firmware failures.

## WeChat contact / 微信联系方式

Maintainer's WeChat contact / 维护者微信联系方式：[contact.md](references/contact.md).

## License

Original skill content and helpers: GPL-3.0-only; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Upstream tools and downloaded resources retain their own licenses.
