# SPDX-License-Identifier: GPL-3.0-only
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/mgu-setup/scripts/diagnose.py'
spec = importlib.util.spec_from_file_location('diagnose', SCRIPT)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)
END = diag.timestamp('2026-11-17T09:00:00Z')


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fixture(self, extra=()):
        components = {}
        for name in (*diag.BASE, *extra):
            (self.root / (name + '.log')).write_text('2026-11-17T08:50:00Z service observed\n', encoding='utf-8')
            components[name] = {'version': '1.2.3', 'requires': {},
                'source': {'id': 'test-source', 'url': 'https://example.invalid/catalog.json'},
                'service': {'unit': name + '.service', 'active': 'active', 'load': 'loaded'},
                'logs': [{'path': name + '.log', 'format': 'iso-lines'}]}
        return {'schema': 1, 'captured_at': END.isoformat(), 'components': components}

    def save(self, value):
        (self.root / 'capture.json').write_text(json.dumps(value), encoding='utf-8')

    def run_capture(self, value=None, **kwargs):
        if value is not None:
            self.save(value)
        return diag.collect(self.root, end=END, **kwargs)

    def test_basic_archive_is_read_only_private_and_complete(self):
        fixture = self.fixture()
        self.save(fixture)
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        report, payloads = self.run_capture()
        self.assertEqual(report['status'], 'complete')
        output = self.root / 'case.zip'
        diag.write_bundle(output, report, payloads)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p != output})
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn('report.md', archive.namelist())
            self.assertFalse(json.loads(archive.read('report.json'))['vehicle_contacted'])
        if os.name != 'nt':
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            diag.write_bundle(output, report, payloads)

    def test_missing_corrupt_manifest_still_produces_report(self):
        for content in (None, '{broken', '{"schema":2}', '{"schema":1,"components":[]}'):
            if content is not None:
                (self.root / 'capture.json').write_text(content)
            report, payloads = self.run_capture(app='ambient')
            self.assertEqual(report['status'], 'partial')
            self.assertTrue(report['capture_error'])
            self.assertIn('ambient_config', [x['id'] for x in report['components']])
            self.assertFalse(payloads)

    def test_maps_expand_and_dependencies_cycle_is_bounded(self):
        value = self.fixture(diag.MAP)
        value['components']['cluster-render']['requires'] = {'extra': '>=2.0.0'}
        value['components']['extra'] = {'requires': {'cluster-render': '>=1.0.0'}}
        for alias in (*diag.MAP, 'waze', 'maps'):
            report, _ = self.run_capture(value, app=alias)
            ids = [x['id'] for x in report['components']]
            self.assertTrue(all(x in ids for x in diag.MAP))
            self.assertEqual(ids.count('extra'), 1)
            self.assertEqual(len(ids), len(set(ids)))

    def test_partial_failures_do_not_discard_working_logs(self):
        value = self.fixture(('ambient_config',))
        value['components']['mgu-updater']['logs'] = [{'status': 'timeout'}]
        value['components']['mgu-deploy']['logs'] = [{'path': 'missing.log'}]
        value['components']['mgu-python'] = None
        report, payloads = self.run_capture(value, app='ambient')
        self.assertEqual(report['status'], 'partial')
        self.assertIn('logs/ambient_config/0.log', payloads)
        self.assertTrue(any('未证明已修复' in x for x in report['notes']))
        self.assertIn('timeout', json.dumps(report))

    def test_secret_redaction_in_every_artifact(self):
        value = self.fixture(('ambient_config',))
        value['components']['ambient_config']['source']['url'] = 'https://bob:secretpass@example.invalid/?signed=SIGNEDSECRET'
        value['components']['ambient_config']['service']['unit'] = 'token=UNITSECRET'
        value['components']['ambient_config']['requires'] = {'password': 'DEPSECRET'}
        (self.root / 'ambient_config.log').write_text(
            '2026-11-17T08:50:00Z VIN=WBA12345678901234 password="p a s s" token=tokensecret\n'
            '2026-11-17T08:50:01Z Authorization: Bearer eyJ.secret.value\n'
            '2026-11-17T08:50:02Z https://user:pw@example.invalid/a?sig=URLSECRET\n'
            '2026-11-17T08:50:03Z alice@example.com 192.168.1.9 35.123456,139.123456\n'
            '2026-11-17T08:50:04Z -----BEGIN PRIVATE KEY-----\n'
            '2026-11-17T08:50:05Z PRIVATEBODY\n-----END PRIVATE KEY-----\n', encoding='utf-8')
        report, payloads = self.run_capture(value, app='ambient')
        output = self.root / 'case.zip'
        diag.write_bundle(output, report, payloads)
        with zipfile.ZipFile(output) as archive:
            all_text = b'\n'.join(archive.read(n) for n in archive.namelist()).decode()
        for secret in ('WBA12345678901234', 'p a s s', 'tokensecret', 'eyJ.secret.value', 'URLSECRET',
                       'alice@example.com', '192.168.1.9', '35.123456', 'PRIVATEBODY', 'UNITSECRET', 'DEPSECRET', 'secretpass', 'SIGNEDSECRET'):
            self.assertNotIn(secret, all_text)
        self.assertIn('[REDACTED', all_text)

    def test_jsonl_nested_redaction_and_time_bounds(self):
        value = self.fixture()
        value['components']['mgu-deploy']['logs'] = [{'path': 'events', 'format': 'jsonl'}]
        rows = [
            {'timestamp': '2026-11-17T08:29:59Z', 'message': 'TOO_OLD'},
            {'timestamp': '2026-11-17T08:30:00Z', 'nested': {'access_token': 'NESTEDSECRET'}, 'message': 'start'},
            {'timestamp': '2026-11-17T18:00:00+09:00', 'message': 'end'},
            {'timestamp': '2026-11-17T09:00:01Z', 'message': 'FUTURE'},
            {'message': 'UNTIMED'},
        ]
        (self.root / 'events').write_text('\n'.join(json.dumps(x) for x in rows))
        report, payloads = self.run_capture(value)
        data = payloads['logs/mgu-deploy/0.log'].decode()
        for absent in ('TOO_OLD', 'FUTURE', 'UNTIMED', 'NESTEDSECRET'):
            self.assertNotIn(absent, data)
        self.assertIn('start', data)
        self.assertIn('end', data)
        record = next(x for x in report['components'] if x['id'] == 'mgu-deploy')['logs'][0]
        self.assertEqual(record['untimed_lines_excluded'], 1)
        self.assertEqual(record['outside_window_lines'], 2)

    def test_app_logs_have_priority_under_total_budget(self):
        value = self.fixture(('ambient_config',))
        report, payloads = self.run_capture(value, app='ambient', total_bytes=50)
        self.assertEqual(report['components'][0]['id'], 'ambient_config')
        self.assertIn(b'service observed', payloads['logs/ambient_config/0.log'])
        self.assertEqual(report['status'], 'partial')

    def test_log_limits_count_and_utf8(self):
        value = self.fixture()
        (self.root / 'many.log').write_text(('2026-11-17T08:50:00Z 日志 token=秘密\n') * 10000, encoding='utf-8')
        value['components']['robertn_store']['logs'] = [{'path': 'many.log'}] * 20
        report, payloads = self.run_capture(value, file_bytes=1024, total_bytes=1600)
        self.assertLessEqual(sum(map(len, payloads.values())), 1600)
        self.assertTrue(all(len(p) <= 1024 for p in payloads.values()))
        for data in payloads.values():
            self.assertNotIn('秘密', data.decode('utf-8'))
        self.assertEqual(report['components'][0]['logs_omitted_by_count'], 12)
        self.assertEqual(report['status'], 'partial')

    def test_path_traversal_symlinks_and_special_files(self):
        value = self.fixture()
        for path in ('../outside.log', '/etc/passwd'):
            value['components']['robertn_store']['logs'] = [{'path': path}]
            report, _ = self.run_capture(value)
            self.assertEqual(report['components'][0]['logs'][0]['status'], 'unavailable')
        if os.name != 'nt':
            (self.root / 'link').symlink_to('/etc/passwd')
            os.mkfifo(self.root / 'fifo')
            for path in ('link', 'fifo'):
                value['components']['robertn_store']['logs'] = [{'path': path}]
                report, _ = self.run_capture(value)
                self.assertEqual(report['components'][0]['logs'][0]['status'], 'unavailable')

    def test_manifest_size_limit_and_stale_capture(self):
        (self.root / 'capture.json').write_bytes(b' ' * (diag.MANIFEST_MAX + 1))
        report, _ = self.run_capture()
        self.assertTrue(report['capture_error'])
        value = self.fixture()
        value['captured_at'] = '2020-01-01T00:00:00Z'
        report, _ = self.run_capture(value)
        self.assertEqual(report['status'], 'partial')
        self.assertFalse(report['capture_time_in_window'])

    def test_empty_window_is_not_complete_coverage(self):
        value = self.fixture()
        (self.root / 'robertn_store.log').write_text('2020-01-01T00:00:00Z old observation\n')
        report, _ = self.run_capture(value)
        self.assertEqual(report['components'][0]['logs'][0]['status'], 'empty')
        self.assertEqual(report['status'], 'partial')

    def test_empty_service_source_do_not_count_as_observed(self):
        value = self.fixture()
        value['components']['robertn_store']['source'] = {}
        value['components']['robertn_store']['service'] = {}
        report, _ = self.run_capture(value)
        for field in ('source', 'service'):
            self.assertEqual(report['components'][0]['metadata'][field]['status'], 'unavailable')

    def test_source_digest_preserved_credentials_discarded(self):
        value = self.fixture()
        value['components']['robertn_store']['source'].update(sha256='a' * 64, credentials='SOURCESECRET')
        report, _ = self.run_capture(value)
        source = report['components'][0]['metadata']['source']['value']
        self.assertEqual(source['sha256'], 'a' * 64)
        self.assertNotIn('SOURCESECRET', json.dumps(report))

    def test_multilingual_and_incomplete_private_material_redaction(self):
        text = diag.redact('密码：short-secret\n令牌=short-token\n-----BEGIN PRIVATE KEY-----\nremaining-body')
        for secret in ('short-secret', 'short-token', 'remaining-body'):
            self.assertNotIn(secret, text)

    def test_sensitive_identifier_does_not_leak_via_archive_members(self):
        vin = 'WBA12345678901234'
        value = self.fixture((vin,))
        report, payloads = self.run_capture(value, app=vin)
        self.assertNotIn(vin, json.dumps(report))
        self.assertNotIn(vin, str(list(payloads)))

    def test_invalid_app_does_not_become_archive_path(self):
        with self.assertRaises(ValueError):
            self.run_capture(self.fixture(), app='../../bad')

    def test_cli_creates_partial_bundle_without_vehicle_or_input(self):
        output = self.root / 'empty.zip'
        result = subprocess.run([sys.executable, str(SCRIPT), '--input', str(self.root / 'absent'),
                                 '--output', str(output), '--app', 'waze', '--until', END.isoformat()],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('coverage=partial', result.stdout)
        self.assertTrue(output.exists())


if __name__ == '__main__':
    unittest.main()
