# Diagnostics / 诊断模式

Use this route for “基础诊断 / basic diagnostics”, “诊断某个应用 / diagnose an app”,
or a request for a diagnostic bundle. A diagnostic request authorizes observation
only. It does not authorize repair, upgrades, restarts, service activation, patch
changes, scans or source changes. Preserve 国内版 / 官方版 and the active source;
no edition question is needed to inspect existing evidence.

## Connect and collect / 连接并采集

Use [collect_diagnostics.py](../scripts/collect_diagnostics.py) on the computer to
connect over **existing verified SSH access** and create a private ZIP containing
`report.md`, `report.json` and redacted logs. Reuse the session's literal HU IP,
port, user, key/SSH agent and verified `known_hosts` file. A diagnostic request
authorizes this read-only connection; do not ask for the same authorization again.
Ask for missing connection details only. Verify a new or changed host key through
the physical ENET/session identity before adding it to a private trust record;
never disable strict host-key checking or silently replace a trusted key.

Agent-side invocation from the installed skill directory:

```sh
python3 scripts/collect_diagnostics.py --host <verified-HU-IP> --identity <existing-private-key> --known-hosts <verified-known-hosts> --output <new-private-case.zip>
python3 scripts/collect_diagnostics.py --host <verified-HU-IP> --identity <existing-private-key> --known-hosts <verified-known-hosts> --output <new-private-waze.zip> --app waze
python3 scripts/collect_diagnostics.py --host <verified-HU-IP> --identity <existing-private-key> --known-hosts <verified-known-hosts> --output <new-private-updater.zip> --app mgu-updater
```

Omit `--identity` to use an already unlocked SSH agent. An encrypted key that is
not available to the agent requires local unlocking; never put its passphrase in
a command or report. The helper is noninteractive and does not retry authentication,
change key permissions, enable Root, scan a subnet or install anything.
Supply verified nondefault `--port` / `--user` when needed.

The helper reads existing app registration, package/component manifests,
deployment inventory, installation origins, firmware/runtime/boot context,
updater rollback markers, systemd properties and journals, and known rotating
log files. It runs a fixed read-only Node probe on stdin; nothing is installed or
staged on the HU. Journal and updater file-log collection remain available when
the HU's Node probe cannot run. No installed application JS or deployment wrapper
is executed. Waze scope includes its app, projection service and cluster renderer.

Windows/macOS/Linux use the local OpenSSH client. SSH configuration, forwarding
and connection sharing are excluded; host trust remains mandatory. SSH itself
can create normal server authentication/audit records; “read-only” here means
no application/configuration writes, service activation or vehicle-state change.

The default overall deadline is **120 seconds**, each command at most **12 seconds**
and connection setup **5 seconds**. Journals include at most **200 records per
stream** in the absolute window, without follow or socket activation. The app
and dependencies are prioritized before base logs; at most **32 components**
and **4 service units/component** are queried. Remaining work is marked missing,
timed out or budget limited. Node, journal or file failures preserve other evidence.
An SSH failure produces a failure report and exit 1; it is never successful
collection. Review `vehicle_contacted`, stream status, truncation and time coverage.

Use the symptom time for `--until` when appropriate. Compare the computer and
vehicle clock in the report before interpreting an empty window; do not change
the HU clock. Current observations do not prove historical component state.
Default paths cover the reviewed layout; custom paths, DLT-only events, lost
volatile history or manager-specific logs can remain unavailable.

## Offline evidence / 离线证据

The separate [diagnose.py](../scripts/diagnose.py) processes existing local exports
with no network or vehicle execution. Normalize observations into the contract below **locally**.
Use recorded values and timestamps, not the current online catalog as a substitute
for installed versions. Preserve the raw export privately outside the output.
Do not download new releases, run an installer, or touch Root desktop settings.
If no connection or compatible export is available, report the missing evidence.
An invalid/missing export manifest can still produce a partial report, but this is
not vehicle log collection; an unwritable output is an explicit failure.

## Entry points / 一键入口

Examples of owner requests:

- “做一次基础诊断，只采集，不修改。” → basic route.
- “诊断 Waze 地图不显示。” → app `waze`; include all three map components.
- “诊断氛围灯提示车身模块未响应。” → app `ambient`.
- “诊断 car_vitals。” → exact app ID; include its recorded dependencies.

For existing exports, agent-side **offline** invocations:

```sh
python3 scripts/diagnose.py --input /private/case-export --output /private/basic-diagnostics.zip
python3 scripts/diagnose.py --input /private/case-export --output /private/waze-diagnostics.zip --app waze
python3 scripts/diagnose.py --input /private/case-export --output /private/ambient-diagnostics.zip --app ambient
```

Do not hand these to the owner as vehicle shell steps. Choose a new local output
filename for each case; output overwrite is refused. There is no automatic upload.
If the export is historical, supply `--until` with its actual capture time, e.g.
`--until 2026-11-17T17:00:00+08:00`. Do not relabel old evidence as current.

Defaults: the preceding **30 minutes**, **256 KiB read/output per log**, **4 MiB
of log output overall**, at most **8 logs/component**, **128 components**, and a
**1 MiB input manifest**. `--minutes` accepts 1–1440; `--file-kib` 1–1024;
`--total-kib` 1–16384. Metadata/reports are additional to the log budget. Byte
truncation, omitted files, unknown timestamps and empty windows are explicit.
App scope budgets prioritize the selected app/map group before base logs.
Limits apply before log parsing; the helper never reads an entire large log.

Only absolute ISO 8601 timestamps with timezone are accepted. `iso-lines` uses
one timestamp at the start of each line, followed by a space and message;
`jsonl` uses an object with `timestamp`. Untimed lines are excluded, including
unanchored stack-trace continuations. A converter may propagate a preceding
record's timestamp only if the source format establishes that association; it
must not invent an event time. Preserve the export's actual timezone. Unsupported
formats are reported unavailable rather than silently included outside the window.

## Evidence contract / 本地证据格式

`capture.json` describes observations and references files **inside the same local
directory**. Absolute paths, parent traversal, symlinks and special files are
rejected. Do not extract untrusted archives into this directory without validating
their members. Do not point the helper at a mounted vehicle filesystem.

```json
{
  "schema": 1,
  "captured_at": "2026-11-17T17:00:00+08:00",
  "components": {
    "ambient_config": {
      "version": "2.5.1",
      "requires": {"mgu-render": ">=0.6.0"},
      "source": {
        "edition": "国内版",
        "id": "recorded-source-id",
        "url": "https://example.invalid/catalog.json",
        "version": "2.5.1",
        "sha256": "recorded artifact SHA256, if available",
        "observed_at": "2026-11-17T17:00:00+08:00"
      },
      "service": {
        "unit": "actual observed unit name",
        "load": "loaded",
        "active": "failed",
        "sub": "failed",
        "result": "exit-code",
        "restarts": 2,
        "observed_at": "2026-11-17T17:00:00+08:00"
      },
      "logs": [
        {"path": "ambient.log", "format": "iso-lines"},
        {"status": "timeout"}
      ]
    }
  }
}
```

The example is synthetic, including its dependency. Missing fields mean
**unavailable**, not “not installed” or “healthy”. An empty `requires` object
means the observed manifest declared no requirements; do not substitute it for
an unread manifest. Failed log capture uses `status` of `missing`, `failed`,
`timeout` or `denied`. One failure does not discard other observations.

Base scope: Store (`robertn_store`), updater, deploy, uplink, renderer, Python,
app privacy and `app-manager` (a logical observation ID, **not a guessed unit
name**). App scope adds the chosen app and the transitive dependency IDs present
in its observed `requires`; cycles are bounded. Always associate
`robertn_waze_cluster` (Waze app), `waze-on-cluster`, and `cluster-render` when any
one is requested. Do not infer the phone's navigation state from those services.

The metadata report preserves version, declared dependencies, observed source
identity/artifact digest and selected service status fields. It does not solve
version constraints, certify artifact provenance, or equate `active` with a
working UI. Compare requirements and versions in the report; distinguish a
missing observation from a confirmed missing or incompatible dependency.

## Passive evidence sources / 采集适配边界

Reviewed path anchors: CN Store commit
`146ee917ce36e7dfa491d573de80ff3a3293590d`, Apps commit
`6aa4cb1ea310dfbe75f0e81e58230364547106d6`. These identify source review, not the
latest release or the customer's installed version. Verify the actual source
checkout/installed layout before using a path; do not assume a default project
directory is current.

| Observation | Candidate evidence and limit |
|---|---|
| Installed apps/tools | `/var/opt/mgu-deploy/state.json` records plus actual registry and installed manifests; distinguish retained payloads from active/registered apps. |
| Declared dependencies | Matching installed `component.json` / app release metadata; do not use today's catalog to fill an unknown installed manifest. |
| Source | Existing updater `sources.json` and `state/origins.json` exports; select identity/URL/version/hash fields locally, never copy credential files. An enabled catalog alone does not establish an app's installation origin. |
| Services | Passive `systemctl show` properties (`LoadState`, `ActiveState`, `SubState`, `Result`, restart count, exit status), with reviewed or manifest-declared unit names and timestamps. App manager registration and a tile are separate evidence. |
| Logs | Existing app file logs and base component journals. Waze includes capture/patch service and renderer journals; missing streams stay missing. No Save logs action or logging toggle is invoked. |
| Context | Existing uptime/boot, observed HU family/firmware, symptom time, selected output, driver shared/own setting; keep identifying context in the private case record, not raw profile files in the bundle. |

**No repair fallback.** Do not call ordinary deploy `status`,
a wrapper that can fall back to repairing status, guessed daemon arguments,
service start/restart, logging toggles, map patch probes with unknown side effects,
UDS/BDC reads or “重新查找” to fill missing data. `status --read-only` requires
verified vehicle-side support and review; it is not used by the collector.

Map **Save logs** is not assumed passive. The reviewed service has socket
activation and a `Wants=waze-on-cluster-logs-fw.service` relationship; related
capture code changes/restores logging configuration. Existing exports can be
analyzed, but diagnostic-only intent does not silently authorize creating one
through that action. See [recovery.md](recovery.md) for the status/repair boundary.

## Ambient coverage / 氛围灯覆盖案例

“车身模块未响应，暂时无法自定义颜色” does not identify one cause or prove BDC
hardware failure. Collect the actual app version, symptom time and **existing**
TASU initialization/channel errors or busy events, rejection/timeout evidence,
DA5F/E3D1 observations, empty/short records and concurrent-scan timing when logged.
No new diagnostic request, retry, scan or color write is performed.

记录已知车型/年份、原厂或后装、是否仅刚启动发生、原车颜色能否切换、车主此前手动
重新查找是否恢复；无需完整 VIN，也不让车主为了报告重试。现有日志可能把空记录与
超时都写成 `lights: none found`，缺少细分证据时结论是“原因未确定”。这仅是诊断采集
覆盖；不宣称已经修复初始化失败恢复、重叠扫描或车型协议兼容问题。

## Updater rollback / 更新服务回退

`<new> did not start; <old> kept` means the supervisor restored the old updater
without a recorded `trial-reason`. It does not identify a network error or prove
the download failed. Inspect the incident window in the existing
`mgu-updater.service` journal and `/tmp/mgu-updater.log` plus `.1`, along with
installed deploy/Python/updater versions, firmware, Node version, boot time and
service exit/restart observations. Syntax/module errors and failures before the
updater's file logger may appear only in the service journal. The supervisor can
also roll back after its trial deadline; preserve the actual timings.

Keep `not kept: <reason>` distinct: it records failed deploy/catalog/network
validation. Do not disable rollback, bypass requirements or reinstall repeatedly
to collect evidence. Default journal/file logs may be lost after a reboot or
rotation. Record missing earlier events explicitly.

Use live collection with `--app mgu-updater` for both service journals and rotating
file logs, rollback markers and installed versions. This path does not depend on
the updater working or the phone page being enabled. If SSH is unavailable but
the owner already has access to the Store phone management page, its Logs section
can supply updater file logs and relevant service journals for the offline helper.
Do not enable that page silently as a diagnostic fallback.

## Privacy and reporting / 脱敏与报告

Redaction is on by default with no raw-output switch: structured sensitive keys,
credential assignments, authorization headers, URL userinfo/query/fragment,
VINs, PEM/SSH material, long opaque strings, emails, IPv4/MAC and common coordinate
pairs. Unrecognized personal data can remain; inspect the output privately before
sharing. No raw input paths or arbitrary exception text enter the bundle. Source
SHA256 fields retain valid digests as provenance observations, not verification.

Report scope, capture time and time window first, then observed failures,
unavailable/truncated evidence, hypotheses and the next useful observation.
`complete` means the requested evidence fields and nonempty logs were present;
it is **not** a health verdict. `partial` still yields a usable ZIP. Exit 0 means
a bundle was written, including partial cases; the live collector also requires
an observed SSH connection. Exit 1 means no verified connection or output/argument
failure (argparse usage errors use exit 2). Never report “fixed” from collection.

Keep local tests, simulation and vehicle results separate. Fixture tests exercise
the actual filesystem probe against a read-only adapter, bounded SSH process I/O,
host-key refusal, Node failure, journal/rotation collection, redaction and failure
isolation. They do not establish actual firmware coverage, ECU response behavior
or visual operation. This collector does not perform ECU diagnostic requests.
