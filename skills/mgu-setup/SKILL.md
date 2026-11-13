---
name: mgu-setup
description: Set up and maintain an owner-authorized BMW MGU over ENET using SSH and Store tools. Use for environment checks, backup preparation, initial root, Store setup, full-distribution switch preparation and supported migration, map/HUD setup, updates, and supported rollback or removal. Supports Chinese and English.
license: GPL-3.0-only
---

# MGU setup and maintenance / MGU 安装与维护

Use the selected distribution's supported tools to complete the requested operation. Respond in the user's language; one task does not authorize the whole lifecycle.

## Choose the edition once / 只选一次版本

- First installation: **mainland China → recommend Walle CN; other regions → recommend official**. Honor an explicit choice first. Use a known region from the conversation/record; do not infer it from language or IP. If unknown, offer the two-line choice in [edition selection](references/store-distributions.md#choose-edition), without a separate location questionnaire.
- CN uses domestic online catalogs for Store, core components and maps; official follows upstream releases. For official downloads, try direct access, then verified same-version fallback resources according to network availability. Tell users **“改用备用源 / using a backup source”**; do not introduce a third edition or another source question. A backup download does not change the built-in update source. Match the installer to the edition and verify active sources after setup.
- Existing installation: preserve edition, source and settings. A region recommendation never authorizes migration; an explicit switch uses [full-distribution switching](references/store-distributions.md#switch-distribution).
- Use the published **正式版 / production release**. Do not offer channel choices or Beta fallbacks. Only explicit Beta requests, maintenance of a recorded explicit Beta installation, or maintainer release work load [release-channels.md](references/release-channels.md); preserve an existing chosen channel. Publishing both channels does not authorize a vehicle trial.

用户说明保持简短：**大陆推荐国内版，方便后续国内在线更新；其他地区推荐官方版，直接跟随 GitHub 上游。两者均可自行选择。** 复用已选版本，不重复询问地图源、地区和发布通道。

## Read only the needed route / 按需读取

| Task | Reference |
| --- | --- |
| First setup, Store repair, maps/HUD | [中文流程](references/workflow.zh-CN.md) / [English workflow](references/workflow.en.md); CN installer/readiness in [distributions](references/store-distributions.md) |
| Existing Store/app update or resume | [maintenance-update.md](references/maintenance-update.md); skip first-root preparation |
| Change edition, including installer and installed components | [store-distributions.md](references/store-distributions.md#switch-distribution) |
| First root, access repair, Root tool preparation | [root-tool.md](references/root-tool.md); healthy SSH needs no flash/enable/persist |
| Failure, downgrade or rollback | [recovery.md](references/recovery.md) |
| Uninstall Store or disable Root/SSH | [removal scope and order](references/recovery.md#removal); SSH removal is not factory firmware restoration |
| Official backup source or mirror maintenance | [network-mirrors.md](references/network-mirrors.md); not needed for ordinary CN online updates |

Historical versions and validation limits: [evidence.md](references/evidence.md). Never treat a historical version as the current recommendation.

## Execute and verify / 执行与验证

1. Reuse private records, credentials, backups and verified packages. Freshly verify vehicle identity, access and installed versions; ask only for missing or changed prerequisites. With no car, finish local preparation.
2. Choose the actual transfer path and scoped environment profile. Prefer a working Store/updater for routine updates. Official `first-install --from` covers Store setup/repair or a compatible offline refresh, not all apps. USB and hotspots are conditional; a computer cache is not an HU USB source.
3. Freeze sources, versions, hashes and dependencies before writing; fetch only missing/mismatched resources. Reuse same-version code reviews; inspect changed or uncertain behavior. Do not chase releases mid-update, disable TLS checks or treat a local hash as proof of origin.
4. Save readiness in a private [session record](references/session-record.md). Serialize authorized writes and inspect each result. Stop the affected path on identity/hash mismatch, unsupported target, new crash loop, failed rollback or unexplained permissions. Missing prerequisites block that write, not independent preparation.
5. Verify target versions, required activation/restart checks, service health and source ownership. Distinguish downloaded, installed, registered and visually observed. Restore temporary proxies and close task-only tunnels; preserve owner settings and a resumable checkpoint.

For update-only tasks, finish after these checks. Without active phone navigation, report visuals unverified; do not expand into map troubleshooting or reboot just for a picture. Record local, emulator and vehicle evidence separately; never invent a passed check.

## Boundaries / 操作边界

- **Read-only means verified behavior.** Unknown daemon arguments can start services; ordinary deploy `status` may repair the manager. Check vehicle-side `--read-only` support and exclude a wrapper's repairing fallback for read-only tasks. See [recovery](references/recovery.md).
- **Flash only for an authorized, prepared need.** Establish supported HU architecture, coding recovery and stable power; explicitly select the variant. Never automatically retry flash or choose `fix-key`. Flash enables access, not the Store.
- **Use supported operations.** No owner shell edits, manual binary patches, fake network/USB state or bespoke vehicle executables. Use published artifacts and an available HU SDK donor for builds; do not redistribute the SDK.
- **Backups have different scopes.** Coding, access, deployment and patch originals are not full firmware backups. Check format, coverage and restoration capability; a `verified` flag is insufficient. See [capture limits](references/root-tool.md#coding-capture-limits). Keep vehicle identifiers, keys, firmware-derived files and logs private.
- **Restart and access deliberately.** Use the offered normal restart; no repeated resets or `carplay.service`/`aapd.service` shortcuts. Verify changed host keys over physical ENET with fresh identity and retain strict checking. A reboot disconnect is not a reason to reflash.
- **Report limits honestly.** Apply project checks and the authorized release policy; distinguish publication from vehicle validation. Finish independent work when a physical screen/coding tool is unavailable and state the remaining action. Firmware rescue is outside this skill.

Contact / 微信：[contact.md](references/contact.md). Original content: GPL-3.0-only, [LICENSE](LICENSE), [NOTICE.md](NOTICE.md). Third-party resources retain their licenses.
