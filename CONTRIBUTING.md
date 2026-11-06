# Contributing / 贡献指南

Contributions that make the instructions clearer, the helper more reliable, or platform evidence more precise are welcome.

欢迎改进指令、翻译、辅助脚本，以及补充有证据的兼容性记录。

## Scope / 范围

- Keep English and Chinese workflows consistent, especially prerequisites, stop conditions and recovery limits.
- Link the exact upstream release or commit when documenting behavior that can change.
- Separate local tests, emulator tests, vehicle observations and owner reports.
- Keep changes focused. Do not add automatic flashing or recovery writes to the local environment checker.

中英文必须保持操作前提和恢复边界一致。引用具体上游版本；区分本地、模拟器、实车和车主报告，不把推测写成已验证事实。

## Before a pull request / 提交前

```sh
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
python3 tools/package_skill.py
```

Describe the user-facing problem, final behavior and validation. A documentation change does not require a vehicle test. A new on-vehicle action needs its own compatibility evidence and applicable upstream emulator validation.

说明实际问题、最终行为和验证结果。纯文档改动无需实车测试；新增车机动作必须提供相应兼容性证据和上游要求的模拟器验证。

## Shareable evidence / 可公开证据

Include OS, HU family, non-identifying firmware version, tool versions, the operation and a short redacted error. Remove VINs, private keys, enrollment certificates, passwords, tokens, personal account details and precise location. Never upload a full vehicle backup, BMW SDK, firmware binary or generated BMW-linked bundle.

可以提供系统、HU 类型、非个人化固件版本、工具版本、操作和脱敏错误片段。不要上传 VIN、密钥、登记证书、密码、令牌、个人账号、精确位置或完整备份。

Reports about vulnerabilities should use GitHub private vulnerability reporting if it is available; otherwise open a minimal issue requesting a private contact without exploit details or sensitive attachments.

漏洞报告优先使用可用的 GitHub 私密报告入口；未开放时，仅提交请求私下联系的最小 issue，不公开敏感细节。

Original contributions use the repository's GPL-3.0-only license. Retain third-party notices and do not import material you cannot redistribute.
