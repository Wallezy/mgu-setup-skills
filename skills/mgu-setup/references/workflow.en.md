# Setup and maintenance workflow

## 1. Scope and local readiness

Identify the requested endpoint: preparation, first root, Store repair/install, map/HUD setup, update, rollback or removal. Read instructions in every checkout used. Preserve owner choices and unrelated changes.

Run `scripts/check_environment.py` with the Python intended for the SSH source tool. It checks Python, cryptography, Node and OpenSSH locally; it does not certify vehicle readiness.

| Platform | Check |
|---|---|
| macOS | Dock Ethernet interface, link-local address and routes alongside hotspot/VPN; interface names vary |
| Windows | OpenSSH availability, selected Python dependencies, upstream administrator requirements for ENET; PowerShell syntax |
| Linux | Link, permissions, OpenSSH and routing; do not copy macOS interface-binding options |

Source SSH setup needs Python 3.9+ and upstream `requirements.txt`; a Windows executable is an alternative. Direct `mgu-install.js` needs Node 18+. Current shell/PowerShell wrappers provide another runtime setup route. Verify current minimums and prefer a maintained compatible runtime.

Review current README, releases and relevant known failures. Pin downloaded installer source to an inspected revision when practical. Case-study versions are not permanent recommendations. Do not disable TLS verification to work around computer certificate errors.

Before planned vehicle writes, prepare missing dependencies in the selected environment and rerun the appropriate check profile. Download the selected upstream tools and scoped artifacts/dependencies locally using section 5. Record source, version, size, supplied checksum and local hash; inspect the archive. Do not begin first flash or installation with required downloads still pending.

Root assets must match the selected architecture and remain private. Read-only vehicle identification may precede downloads to select them. Once the vehicle and resources match, record a readiness result in the session template. Re-evaluate if the target or release selection changes.

## 2. Vehicle identity and backup preparation

Discover the gateway/HU through upstream read-only status/discovery. Observe architecture, firmware, interface, IP and vehicle identity. Do not reuse another session's VIN or gateway. Do not change coding or arm debug merely to discover an already accessible unit.

Before first flash, establish that the car is parked, awake and on power appropriate for programming. Confirm the pre-flash HU/MGU coding backup, selected module, tool and location. Keep these categories outside the public repository:

| Backup | Coverage and verification |
|---|---|
| Coding | A compatible coding tool's HU/MGU backup; owner completes unavailable tool steps. Does not restore executables. |
| Access | Matching root key, enrollment metadata and connection information; a key is not necessarily unique per vehicle. |
| Deployment | Before-state, versions, registry/tile state and deploy snapshots. Check archive contents, exit status and retention. |
| Patch originals | Verified originals, patch records, modes and owners for changed files. Not a firmware image. |

The current root README documents loss of coding/CAFD and Digital Key pairings on flashing. Coding backups do not cover Digital Keys. Do not promise a recovery time or guaranteed rescue.

## 3. Root SSH: branch before writing

Try existing authorized credentials against the discovered HU first. If root login works, skip bootstrap.

For an unprovisioned unit, inspect the checkout's CLI help and architecture handling. At review time the upstream CLI documents:

```text
python ssh_enable.py status
python ssh_enable.py flash --vin <verified-vehicle-vin> --persist
```

These are workflow examples, not commands for every connection. Use a verified VIN and explicitly select the supported architecture when required. Execute flash only for an authorized first setup with prerequisites satisfied. The GUI's combined “Flash + Enable” may already perform persistence and debug shutdown.

For provisioned SSH that fails, distinguish timeout, changed host key and public-key rejection. Check routing, wake state and credentials first. `enable` repairs existing setup; it is not routine connection setup. `fix-key` reflashes and requires a separate repair decision plus flash prerequisites. Do not enable optional key replacement by default.

After bootstrap, verify fresh root login and intended persistence/debug state. Restore pre-flash coding with the appropriate tool when required by the procedure or actual state, then verify normal startup/access. Do not repeatedly flash to repair missing coding.

## 4. Official Store installation or repair

Use the current installer from `robertnisipeanu/mgu-store`, not deployment code from an old localized checkout. Check current Chinese support before deciding a fork is needed.

For the inspected standalone installer:

```text
node mgu-install.js first-install --from <prepared-folder>/mgu-repo/mgu-store --identity <private-key-path>
```

Use the locally prepared, verified catalog from section 5. If choosing an online updater path for later apps, retain the verified local artifacts and confirm the HU can access the same intended release; do not silently change versions between preparation and install.

Use observed host/port options if discovery chooses the wrong path. Reuse a working interface-bound relay if needed, without hard-coding a case-study port. Inspect SSH argument ordering and effective host-key behavior in the selected installer.

The installer uses published artifacts, catalog size/hash checks and their deploy tool. Capture exit status/logs; reconcile partial success and actual versions.

For a missing Store tile, compare actual app registration, manager state and tile visibility with deployment history. A retained package or stale record is not proof of installation. Restore through official setup/repair; do not manually rewrite registries or flash SSH again.

## 5. Offline resources and network diagnosis

Select the preference using [network sources](network-mirrors.md) and
[configuration](network-sources.json). Domestic-first uses Gitee source and
configured OSS packages; the examples below use official GitHub. There is no
`gitee:` updater source type. Fallback preserves selected versions and SHA-256.

Test computer access and HU updater access separately. GitHub API access does not prove release-asset access; test the required artifact and hash. A connected hotspot does not imply GitHub reachability.

Prefer official offline preparation. Create the destination folder first:

```text
node mgu-install.js usb-repo <existing-folder> github:robertnisipeanu/mgu-store github:robertnisipeanu/idrive-apps
node mgu-install.js first-install --from <existing-folder>/mgu-repo/mgu-store --identity <private-key-path>
```

The second command installs the Store over computer-to-HU transport. Later apps can be installed from prepared physical USB media through the Store's USB page. A computer folder alone does not become a USB source on the car.

Alternatively use the Store's supported HTTP/SOCKS proxy setting with a reachable owner-controlled proxy. Computer loopback does not address the computer from the HU unless a real forwarding path exists. Scope any ENET tunnel to the task, record previous settings and restore them before disconnecting. Do not disable HTTPS checks or disclose proxy credentials in shared logs.

## 6. Maps and HUD

Install `robertn_waze_cluster` from official `idrive-apps` releases through Store UI or its supported updater. Let declared requirements choose `waze-on-cluster` and `cluster-render` versions/order.

Inspect patch state: installation may preserve a previously disabled CarPlay patch. Use the app's Patch control within the requested scope and supported compatibility. Android Auto patching is separate and coding/architecture dependent.

Choose Cluster, HUD or both in the app. HUD is experimental upstream. For cluster output, select the vehicle's central Map view as documented. Reconnect CarPlay if necessary, start navigation, inspect stream/renderer state and obtain actual display evidence.

App 0.6.4 with map service 0.9.3 provides "Own settings for this driver". Settings are shared by default; opting in keeps the display target, HUD size and position per driver, not every map setting. Enable it only when requested and verify settings after switching drivers. An unknown driver or unavailable service can disable the control; this is not a reason to reflash. See [recovery.md](recovery.md) for configuration backup and downgrade considerations.

Use the offered normal restart and respect its cooldown. Afterwards inspect boot ID/uptime, core services, mode/owner, boot verification, registered apps and pending restarts. The recorded build expected 0755 for carplay/aapd; derive expectations from verified originals/current upstream on other builds.

No video can mean patch disabled, restart pending, no phone secondary stream, HUD off, renderer failure or navigation-app incompatibility. Do not promise Amap/Baidu quality or a fixed frame rate without observing that combination.

For latency, map service 0.9.2 onward adds frame assembly, decoder buffering and H.264 diagnostics. Additional logging is not a frame-rate improvement; cluster-render 0.4.2 raises layer capacity without raising video bandwidth.

## 7. Update, downgrade and remove

Record current versions and known-good resources, refresh published catalogs, check dependencies and request only chosen updates. Let the updater resolve requirements, perform necessary restart and verify versions afterwards. Do not falsify version fields to bypass checks.

For a domestic mirror, check the live OSS catalogs and artifacts as well as the skill/Gitee checkout. App 0.6.4 requires map service >= 0.9.3; use the selected release's actual requirements. After a vehicle firmware update, handle "Needs setup / Set up" through the current Store's setup flow, complete any requested restart and verify the result rather than restoring system-file snapshots from the old firmware.

For downgrade, rollback, patch removal, Store removal or SSH removal, read [recovery.md](recovery.md). Native-tool rollback, app downgrade and firmware downgrade are different operations.

## 8. Validation and handoff

Use [session-record.md](session-record.md). Allow the installed release's deferred startup checks to run and inspect their result; elapsed time alone proves nothing. Distinguish background tools with no launcher from user-facing apps with missing tiles.

Restore temporary settings and close task-only tunnels. Preserve permanent SSH if requested; turning it off is another endpoint. Report observed results and any necessary physical-screen or coding-tool action still outstanding.
