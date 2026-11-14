# MGU Setup Skills

[简体中文](README.zh-CN.md)

[![Validate](https://github.com/Wallezy/mgu-setup-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/Wallezy/mgu-setup-skills/actions/workflows/validate.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

A bilingual agent skill for owner-authorized BMW MGU setup and maintenance: environment checks, backup preparation, initial root SSH, Store installation, map/HUD setup, updates and supported recovery.

The skill guides an agent to **perform authorized work with upstream tools**, inspect the result and produce a session record. It is not a firmware flasher or a promise of automatic recovery from every failure.

## On the owner's iDrive 7

| App entries | Store |
| --- | --- |
| ![Store and Waze on cluster entries](docs/images/app-entries.jpg) | ![Store interface on the head unit](docs/images/store.jpg) |
| **Cluster and HUD settings** | **HUD map output** |
| ![Cluster map and the display target selector](docs/images/cluster-and-hud.jpg) | ![Map rendered on the HUD while parked](docs/images/hud-map.jpg) |

Photos supplied by the owner show one iDrive 7 installation, including actual
HUD output. They do not establish compatibility or frame rate for other cars,
phones or map apps. HUD remains experimental. [Full-size gallery / 实车效果图](docs/SHOWCASE.md).

## Use

1. Get this repository using **Code → Download ZIP**, or clone it:

   ```sh
   git clone https://github.com/Wallezy/mgu-setup-skills.git
   cd mgu-setup-skills
   ```

2. Give your agent the absolute path to `skills/mgu-setup/SKILL.md`, or install the complete skill folder as described below.
3. Start with an environment check and the specific operation you want. Keep the car disconnected if you only want preparation.

Copy the complete [`skills/mgu-setup`](skills/mgu-setup) directory into your agent's skill directory, keeping references and scripts together. Tools that read a local skill directly can use the absolute path to `skills/mgu-setup/SKILL.md`.

Your agent needs local file access and command execution to perform installation; a chat-only assistant can explain the procedure but cannot operate the computer. Skill folder locations and invocation syntax depend on the host tool.

> Use $mgu-setup to inspect my computer and connected head unit, recommend an edition, prepare backups, and install root SSH, Store and the map/HUD app. Reuse working access and verify each completed stage.

Other supported requests:

- “The Store disappeared. Diagnose and restore its entry.”
- “Update only the Store and map app, preserving my settings.”
- “Inspect the boot loop and identify a supported rollback.”
- “Remove the map patch and app; retain the Store.”
- “Uninstall the whole Store-managed setup; keep SSH.”
- “The Store is removed; undo SSH persistence and close access.”
- “Prepare offline resources now; the car is not connected.”
- “Prepare a full switch to Walle CN, including the installer and installed components; preserve my settings.”

[Full-distribution switching](skills/mgu-setup/references/store-distributions.md#switch-distribution)
covers the installer, Store, updater, deploy tool, dependencies, installed apps
and update sources. Walle CN installation and updates use the production release
without asking the user to select a release channel. The agent checks current
published resources, versions, compatibility and recovery prerequisites, and
records publication and vehicle validation separately.

The agent should execute within the request's scope, not just print a tutorial. Physical display checks and coding-tool operations may still need the owner. Installing this skill does not authorize vehicle writes.

## Preparation order

For planned setup or updates, the skill requires **local environment check → local resource download and verification → read-only vehicle identification and backup checks → readiness decision → vehicle writes → result verification**.

The agent stages only the requested tools/packages and their dependencies outside the repository, records versions and hashes, and reuses verified cached files. Vehicle identification can happen earlier when needed to select the correct architecture. Missing dependencies, resources or required backups block the corresponding write.

The environment helper reports problems; the agent prepares missing dependencies in the chosen environment and checks again. This is an agent workflow, not a standalone automatic flasher. Local packages reach the HU through official bootstrap transfer or supported Store/USB/update paths; copying files to the computer alone does not make the car offline-ready. Read-only diagnosis and recovery do not require downloading unrelated apps.

## Coverage

| Task | Behavior |
|---|---|
| Environment and connection | Check runtimes, ENET interface, routing, identity and existing SSH |
| Backup preparation | Separate coding, credentials, deployment snapshots and patch originals |
| Initial root | Use current upstream first-time setup only when needed |
| Store setup and repair | Matching edition's installer; registry/tile checks for missing entries |
| Maps and HUD | Install dependencies; configure through the app; verify actual output |
| Updates | Published releases, dependency resolution and post-start verification |
| Distribution switching | Prepare the matching installer and full component plan; execute only through a verified release and migration entrypoint |
| Downgrade/rollback | Check retained versions and compatibility; use supported paths only |
| Restore/remove | Patch/components, complete Store uninstall, SSH close/persistence removal; no factory firmware restoration |
| Failure diagnosis | Network, authentication, coding, missing tiles and startup failures |
| Handoff | Record versions, checks, temporary settings and remaining owner actions |

## Which edition?

Choose between two editions; both use the production release by default:

| Edition | Recommended for | Difference |
| --- | --- | --- |
| **CN** | Mainland China | Domestic online updates for Store, core components and maps; Chinese adaptations. Upstream changes arrive after maintainer review; no GitHub source support. |
| **Official** | Other regions, or users wanting upstream directly | Upstream releases and GitHub source support; direct or verified backup downloads selected for the connection. |

The skill reuses existing choices and recommends by a known region, never
guessing from language or IP. If unknown, it asks for the edition once, not a
download route. When direct official downloads fail, it says “using a backup
source” and keeps the same official version. Built-in official online updates
still need GitHub access. Existing installs do not change edition automatically.
See [selection and switching](skills/mgu-setup/references/store-distributions.md).

The Skill is also available on [Gitee](https://gitee.com/walle7/mgu-setup-skills).
Backup-source configuration and acceptance are [maintainer work](docs/DOMESTIC-MIRROR.md),
not settings users need to choose during installation.

## Platforms and evidence

Upstream source workflows target Windows, macOS and Linux. Source SSH setup requires Python 3.9+, `cryptography` and OpenSSH. Direct Store installation uses Node.js 18+ and OpenSSH; current upstream wrappers offer runtime preparation, so inspect requirements before choosing a route.

**The recorded vehicle experience is macOS + ENET + iDrive 7.** Windows, Linux and iDrive 8 are upstream-supported targets, not hardware-tested here. HUD is experimental upstream; background checks do not prove visual output on every car.

Local checks only, with no vehicle or network access:

```sh
python3 skills/mgu-setup/scripts/check_environment.py --json
```

On Windows select the intended Python, for example `py -3`. A passing report is not vehicle compatibility or flash readiness.

Use `--profile store` for direct Store installation prerequisites, `--profile root` for source SSH prerequisites, or `--profile inspect` for preparation only. Exit code 1 means required local checks are missing or unverified; it does not mean a vehicle operation failed. The script never installs missing dependencies.

## Documentation

- [FAQ](docs/FAQ.md): prerequisites, offline use, root persistence and recovery boundaries.
- [Skill entrypoint](skills/mgu-setup/SKILL.md).
- [Root release preparation](skills/mgu-setup/references/root-tool.md): reviewed v1.4.0, local revision checks and source/Windows routes.
- [English workflow](skills/mgu-setup/references/workflow.en.md) / [中文流程](skills/mgu-setup/references/workflow.zh-CN.md).
- [Recovery decisions / 恢复判断](skills/mgu-setup/references/recovery.md).
- [Evidence and sources / 经验与来源](skills/mgu-setup/references/evidence.md).
- [Session record / 会话记录](skills/mgu-setup/references/session-record.md).
- [Validation scenarios / 验证场景](VALIDATION.md).
- [Contributing](CONTRIBUTING.md): translations, tests and sanitized compatibility reports.
- [Photos / 实车效果图](docs/SHOWCASE.md): app entries, Store, cluster and HUD.
- [Backup-source maintenance / 备用源维护](docs/DOMESTIC-MIRROR.md): Gitee synchronization and OSS acceptance for maintainers.

## Upstream projects

This project coordinates existing tools and documents practical experience. It is an independent community project, not a BMW product or a replacement for upstream software:

- [idrive7-8-ssh-root](https://github.com/cauliflowermossgrape/idrive7-8-ssh-root): initial SSH access.
- [mgu-store](https://github.com/robertnisipeanu/mgu-store): Store, official installer and updater.
- [idrive-apps](https://github.com/robertnisipeanu/idrive-apps): map application and cluster/HUD components.

Report skill instructions, translations and helper defects [here](https://github.com/Wallezy/mgu-setup-skills/issues/new/choose). For an upstream software defect, identify the responsible component and link the upstream issue instead of assuming the skill can repair it.

## WeChat contact

Connect with Walle to discuss MGU setup and usage. Scan the image below with
WeChat to get in touch; please mention “MGU”.

<img src="skills/mgu-setup/assets/wechat-code.png" alt="Walle's WeChat contact" width="300">

[Full-size image](skills/mgu-setup/assets/wechat-code.png) · [Contact details](skills/mgu-setup/references/contact.md)

## Development

No additional Python packages are required for repository validation:

```sh
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
python3 tools/package_skill.py
```

Packaging produces `dist/mgu-setup.zip` and `dist/SHA256SUMS`. The archive includes the complete skill and GPL license; it does not contain downloaded vehicle resources. CI checks the helper and documentation on Windows, macOS and Linux. These are software checks, not vehicle tests.

No firmware, BMW SDK, root keys, VINs or vehicle logs are distributed here. Keep session data outside the repository. Publishing private evidence requires redaction and owner authorization.

Before advertising another platform or head unit as tested, contribute sanitized environment details, exact versions, observed results and recovery limitations. Documentation/helper checks do not replace hardware validation.

## License

Original repository content is licensed under **GNU GPL version 3 only** (`GPL-3.0-only`). See [LICENSE](LICENSE). The standalone skill carries the same license and its [notice](skills/mgu-setup/NOTICE.md). Referenced or downloaded third-party tools, firmware and resources retain their respective licenses; they are not relicensed by this repository.
