---
name: mgu-setup
description: Set up and maintain an owner-authorized BMW MGU over ENET using upstream SSH and Store tools. Use for environment checks, backup preparation, initial root, Store installation or missing tiles, map/HUD setup, updates, and supported rollback or removal. Supports Chinese and English.
license: GPL-3.0-only
---

# MGU setup and maintenance / MGU 安装与维护

Execute the user's requested work with current upstream tools and observed vehicle state. Respond in the user's language. This skill covers a lifecycle; a request for one operation does not authorize all operations.

## Choose one route / 先选路径

Read only the procedure relevant to the request:

- Existing Store/app update or resume: [maintenance-update.md](references/maintenance-update.md). Start with saved preparation, not first setup. U 盘和热点不是所有更新的统一前提。
- First setup, Store restoration or map/HUD configuration: [Chinese workflow](references/workflow.zh-CN.md) or [English workflow](references/workflow.en.md).
- Access failure, unstable boot, downgrade or removal: [recovery.md](references/recovery.md). Working SSH needs no flash/enable/persist.
- Source selection, OSS preparation or acceptance: [network-mirrors.md](references/network-mirrors.md). Skill/mirror maintenance checks include live OSS versions and dependencies.
- Historical versions and validation limits: [evidence.md](references/evidence.md).

## Execute with minimal repetition / 复用准备，直接执行

1. Reuse relevant private session records, key paths, backup inventories and local packages. Verify fresh vehicle identity/access and installed versions; do not reuse stale IPs as facts. With no car, finish local preparation only.
2. Establish scope and applicable power/backup prerequisites. Honor current authorization and confirmations; ask only for missing or changed conditions. A routine app update does not require repeating first-root preparation.
3. Prefer the working Store/updater for routine updates. Choose the actual package path before configuring networks; official `first-install --from` is an ENET option for Store setup/repair or a needed offline refresh, not a mandatory prelude or an all-app installer. USB/hotspot setup is conditional.
4. Before the first write, lock selected sources, versions, hashes and dependencies. Reuse valid local resources and download only missing/mismatched files; use the scoped environment profile. Follow `network-mirrors.md` for source fallback. Do not chase new releases mid-update or install the same component twice unless compatibility/recovery requires it.
5. Record readiness in a private [session record](references/session-record.md), execute authorized writes sequentially, verify installed/active/displayed results, and clean up task-only settings. Continue from the checkpoint when resumed.

Missing resources or prerequisites block the affected write, not independent preparation. For diagnosis or an already prepared recovery, do not download unrelated packages or repeat a full mirror audit. Prepare missing runtimes in an isolated environment when needed; never disable TLS checks. Local hashes alone do not establish origin.

## Operational invariants

1. Follow applicable local instructions and inspected upstream behavior. Reuse the same-version review; inspect changed or uncertain code. Do not guess read-only commands: historical `patchd.js status` started another daemon.
2. Before first flash, establish owner authorization, supported HU architecture, coding backup and appropriate stable power. Reuse applicable answers in the active session. Missing prerequisites block flashing, not independent preparation. Do not automatically choose an unknown architecture, run `fix-key` or retry a failed flash.
3. Flash provisions debug/SSH access, not the Store. `enable` repairs access; `persist` changes SSH lifecycle. Working access needs neither. Current combined commands may include persistence.
4. Use the official installer for Store setup/refresh and supported Store/updater operations for apps. Do not hand owners shell edits, manually patch binaries, fake network/USB state or deploy bespoke executables. App builds use an available HU SDK donor; never redistribute it.
5. Prefer published artifacts and declared requirements. Record source revision, catalog versions and size/hash verification. Downloaded is not installed; registered is not visually observed; HUD software installed is not HUD video verified.
6. Separate coding, access, deployment and patch-original backups. None is a complete firmware image. Verify recovery applicability and archive completeness. Keep VINs, keys, firmware-derived files and logs outside this repository.
7. Serialize writes; inspect each result before the next mutation. Stop on identity mismatch, failed checksum, unsupported target, new crash loop, failed rollback or unexplained mode/owner changes. Retry downloads only while progress or a changed network path justifies it.
8. Use the normal restart offered by Store/installer/app. Do not repeatedly reset a looping HU or stop/restart `carplay.service` or `aapd.service` as a shortcut. A connection drop during a requested reboot is not a reason to reflash.
9. Verify host-key changes using the physical ENET connection and fresh vehicle identification. An ephemeral host-key path supports diagnosis; it does not justify ignoring every warning. Keep strict checking after accepting a verified key.
10. Distinguish published-component maintenance from development. Apply repository emulator requirements to the actual task; do not repeatedly search for unrelated unavailable tooling. Custom vehicle code needs the required emulator validation. Never present documentation checks or upstream claims as local hardware tests.

## Completion

Report the verified layer: local readiness, authenticated connection, installed versions, tiles, stable boot, enabled patch or observed HUD video. Keep before/after evidence, hashes and cleanup status. Restore temporary proxy settings and close task-only tunnels when finished; preserve owner settings.

For an update-only request, finish after target versions, required activation/restart checks, service health and cleanup pass. Mark navigation visuals unverified when no active phone navigation is available; do not expand into map troubleshooting or reboot solely to obtain a picture.

If a physical screen or unavailable coding tool is required, finish independent work, give the concrete remaining action and state the verification limit. Do not fabricate completion or promise recovery from inaccessible firmware failures.

## WeChat contact / 微信联系方式

Maintainer's WeChat contact / 维护者微信联系方式：[contact.md](references/contact.md).

## License

Original skill content and helpers: GPL-3.0-only; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Upstream tools and downloaded resources retain their own licenses.
