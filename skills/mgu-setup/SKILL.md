---
name: mgu-setup
description: Set up and maintain an owner-authorized BMW MGU over ENET using upstream SSH and Store tools. Use for environment checks, backup preparation, initial root, Store installation or missing tiles, map/HUD setup, updates, and supported rollback or removal. Supports Chinese and English.
license: GPL-3.0-only
---

# MGU setup and maintenance / MGU 安装与维护

Execute the user's requested work with current upstream tools and observed vehicle state. Respond in the user's language. This skill covers a lifecycle; a request for one operation does not authorize all operations.

## Prepare locally before vehicle writes

For planned root setup, installation or updates, use this order:

1. Inspect the task and local prerequisites. Prepare missing runtimes/dependencies in an isolated environment where appropriate; respect machine permissions. Run the environment helper with that same interpreter and the relevant profile.
2. Download the inspected upstream tool/installer and the requested published packages plus their complete declared dependency set into a private local staging directory outside this repository. Use the official `usb-repo` workflow for Store/app artifacts. For first root, verify the selected architecture's required upstream assets locally without redistributing them.
3. Verify origin, versions, sizes and supplied checksums; record local SHA-256 values and archive readability. A locally computed hash alone is not proof of origin. Reuse a verified cache instead of downloading it again.
4. Inspect the connected vehicle read-only, choose the applicable target/architecture, and verify backup coverage, stable power and existing access. Read-only identification may occur earlier when needed to select resources. If the target changes, repeat resource selection and compatibility checks.
5. Record a readiness decision with the intended operation, environment result, resource manifest, transfer method, backup status and vehicle match. Start writes only when applicable prerequisites are satisfied; no new permission question is needed when already authorized.
6. Execute through the official setup/Store path, then verify results and clean up temporary settings.

Missing resources, failed verification or unmet environment/backup prerequisites block the corresponding planned write. Continue independent preparation and explain the concrete missing item. Do not begin flashing while waiting for a required package to download.

Prepare only the requested scope, not every community app. A local folder is not automatically accessible to the HU: use official bootstrap transfer, physical USB media or the supported updater path. Source packages may still build on the HU using its own SDK donor; do not distribute that donor.

For read-only diagnosis, do not require unrelated installation downloads. For recovery, identify and verify the specific recovery resources first; a fresh full catalog download must not delay an already supported, prepared recovery action.

## Read the relevant procedure

- Chinese: [workflow.zh-CN.md](references/workflow.zh-CN.md).
- English: [workflow.en.md](references/workflow.en.md).
- Failure, downgrade, rollback or removal: also read [recovery.md](references/recovery.md).
- Platform claims, historical lessons or source review: [evidence.md](references/evidence.md).
- Record work using [session-record.md](references/session-record.md), outside the public repository.

## Select from actual state

| State/request | Route |
|---|---|
| No car attached | Local checks, source review and offline preparation |
| First root, SSH not provisioned | Verify compatibility, identity, coding backup and power; upstream bootstrap |
| Root login already works | Skip flash, enable and persistence mutations |
| SSH fails | Separate network, host identity and authentication diagnosis |
| Store missing | Compare history with actual registry, tile state and manager health |
| Store usable | Install/update through Store UI or supported updater operations |
| Map/HUD requested | Install app/dependencies; configure in app; verify video output |
| Boot instability | Stop adding installs; classify failure with recovery reference |
| Rollback/removal | Inventory dependencies, retained artifacts and recovery coverage |

## Operational invariants

1. Inspect local instructions, current upstream docs and the exact command implementation. Do not assume `status` exists or is read-only. The historical `patchd.js status` invocation started a second daemon; do not repeat it.
2. Before first flash, establish owner authorization, supported HU architecture, coding backup and appropriate stable power. Reuse applicable answers in the active session. Missing prerequisites block flashing, not independent preparation. Do not automatically choose an unknown architecture, run `fix-key` or retry a failed flash.
3. Flash provisions debug/SSH access, not the Store. `enable` repairs access; `persist` changes SSH lifecycle. Working access needs neither. Current combined commands may include persistence.
4. Bootstrap/restore the Store with the official first-install workflow. Afterwards use Store UI or supported updater requests. Direct read-only inspection is useful; do not hand owners arbitrary shell edits, manually patch binaries or deploy bespoke executables.
5. Prefer published artifacts and declared requirements. Record source revision, catalog versions and size/hash verification. Downloaded is not installed; registered is not visually observed; HUD software installed is not HUD video verified.
6. Separate coding, access, deployment and patch-original backups. None is a complete firmware image. Verify recovery applicability and archive completeness. Keep VINs, keys, firmware-derived files and logs outside this repository.
7. Serialize writes; inspect each result before the next mutation. Stop on identity mismatch, failed checksum, unsupported target, new crash loop, failed rollback or unexplained mode/owner changes. Retry downloads only while progress or a changed network path justifies it.
8. Use the normal restart offered by Store/installer/app. Do not repeatedly reset a looping HU or stop/restart `carplay.service` or `aapd.service` as a shortcut. A connection drop during a requested reboot is not a reason to reflash.
9. Verify host-key changes using the physical ENET connection and fresh vehicle identification. An ephemeral host-key path supports diagnosis; it does not justify ignoring every warning. Keep strict checking after accepting a verified key.
10. Distinguish published deployment from development. Custom code must meet applicable upstream emulator requirements before vehicle deployment. Documentation checks and upstream support statements are not hardware tests.

## Completion

Report the verified layer: local readiness, authenticated connection, installed versions, tiles, stable boot, enabled patch or observed HUD video. Keep before/after evidence, hashes and cleanup status. Restore temporary proxy settings and close task-only tunnels when finished; preserve owner settings.

If a physical screen or unavailable coding tool is required, finish independent work, give the concrete remaining action and state the verification limit. Do not fabricate completion or promise recovery from inaccessible firmware failures.

## License

Original skill content and helpers: GPL-3.0-only; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Upstream tools and downloaded resources retain their own licenses.
