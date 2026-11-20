# SPDX-License-Identifier: GPL-3.0-only
import datetime as dt
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/mgu-setup/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('live_diagnostics', SCRIPTS / 'collect_diagnostics.py')
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)
END = dt.datetime.now(dt.timezone.utc)
STAMP = (END - dt.timedelta(minutes=1)).isoformat()


class VehicleFixture:
    def __init__(self, node=True, failed=False):
        self.node = node
        self.failed = failed
        self.contacted = False
        self.calls = []
        self.metadata = {
            'context': {'node': 'v8.16.2', 'vehicle_time': END.isoformat(),
                        'firmware': 'fixture', 'updater_rolled_back': '0.8.52'},
            'inventory': {'apps': [{'id': 'ambient_config', 'version': '2.7.14'}]},
            'components': {
                'mgu-updater': {'version': '0.8.48', 'requires': {'mgu-deploy': '0.8.28'},
                                'source': {'id': 'walle/mgu-store-cn'}},
                'ambient_config': {'version': '2.7.14', 'app_home': '/var/opt/public/oap/oap_12345',
                                   'requires': {'mgu-render': '0.6.0'}, 'registered': True}
            }}

    def run(self, command, data=b'', limit=256 * 1024):
        self.calls.append(command)
        if self.failed:
            return {'status': 'host-key-rejected', 'data': b''}
        self.contacted = True
        if command == '/usr/bin/node -':
            return {'status': 'ok' if self.node else 'failed',
                    'data': json.dumps(self.metadata).encode() if self.node else b''}
        if command.startswith('systemctl show'):
            return {'status': 'ok', 'data': b'LoadState=loaded\nActiveState=active\nSubState=running\nResult=success\nNRestarts=2\nExecMainStatus=1\n'}
        if command.startswith('journalctl'):
            record = {'__REALTIME_TIMESTAMP': str(int((END - dt.timedelta(minutes=1)).timestamp() * 1e6)),
                      'MESSAGE': 'startup failure\nError: Cannot find module\npassword=short-secret'}
            return {'status': 'ok', 'data': (json.dumps(record) + '\n').encode()}
        if 'mgu-updater.log.1' in command:
            return {'status': 'ok', 'data': (STAMP + ' supervisor returned to old version\n').encode()}
        if 'mgu-updater.log' in command:
            return {'status': 'ok', 'data': (STAMP + ' new updater failed token=token-secret\n').encode()}
        if 'ambient_config.log' in command:
            return {'status': 'ok', 'data': (STAMP + ' lights: none found\n').encode()}
        if command.startswith('if [ -L'):
            return {'status': 'failed', 'code': 44, 'data': b''}
        return {'status': 'ok', 'data': b'fixture system observation\n'}


class LiveDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.trust = self.root / 'known_hosts'
        self.trust.write_text('fixture host key\n')

    def capture(self, transport=None, app='mgu-updater', **kwargs):
        transport = transport or VehicleFixture()
        output = self.root / 'case.zip'
        report = live.collect_live(transport, output, app, **kwargs)
        with zipfile.ZipFile(output) as archive:
            contents = {name: archive.read(name) for name in archive.namelist()}
        return transport, report, contents

    def test_updater_journal_file_rotation_and_exit_status_are_retained(self):
        vehicle, report, contents = self.capture()
        self.assertTrue(report['vehicle_contacted'])
        self.assertFalse(report['repairs_performed'])
        self.assertEqual(report['evidence'], 'live-ssh')
        text = b'\n'.join(contents.values()).decode()
        for expected in ('Cannot find module', 'returned to old version', 'new updater failed', 'ExecMainStatus'):
            self.assertIn(expected, text)
        for secret in ('short-secret', 'token-secret'):
            self.assertNotIn(secret, text)
        self.assertNotIn('未连接车辆', contents['report.md'].decode())
        self.assertTrue(any('mgu-updater.log.1' in c for c in vehicle.calls))

    def test_node_failure_still_collects_early_service_and_file_errors(self):
        _, report, contents = self.capture(VehicleFixture(node=False))
        self.assertTrue(report['vehicle_contacted'])
        self.assertEqual(report['status'], 'partial')
        self.assertEqual(report['collection_failures'][0]['probe'], 'metadata')
        self.assertIn('Cannot find module', b'\n'.join(contents.values()).decode())

    def test_connection_failure_does_not_claim_vehicle_evidence(self):
        _, report, contents = self.capture(VehicleFixture(failed=True))
        self.assertFalse(report['vehicle_contacted'])
        self.assertEqual(report['status'], 'partial')
        self.assertIn('host-key-rejected', contents['report.json'].decode())
        self.assertIn('未建立有效连接', contents['report.md'].decode())
        self.assertFalse(any(name.startswith('logs/') for name in contents))

    def test_maps_collect_three_components_and_passive_patch_journals(self):
        vehicle, report, _ = self.capture(app='waze')
        ids = [x['id'] for x in report['components']]
        self.assertTrue(all(name in ids for name in live.diag.MAP))
        self.assertTrue(any('waze-on-cluster-patchd.service' in c for c in vehicle.calls))
        self.assertTrue(any('cluster-render.service' in c for c in vehicle.calls))
        for command in vehicle.calls:
            words = shlex.split(command)
            self.assertNotIn('restart', words)
            self.assertNotIn('start', words)
            self.assertNotIn('enable', words)
            self.assertNotIn('--follow', words)
            self.assertNotIn('mgu-deploy.sh', words)

    def test_ambient_log_is_taken_from_registered_app_home(self):
        vehicle, report, contents = self.capture(app='ambient')
        self.assertEqual(report['components'][0]['id'], 'ambient_config')
        self.assertTrue(any('/oap_12345/data/ambient_config.log' in c for c in vehicle.calls))
        self.assertIn('lights: none found', b'\n'.join(contents.values()).decode())
        self.assertTrue(report['component_observations']['ambient_config']['registered'])
        self.assertIn('apps', report['deployment_inventory'])

    def test_recorded_dependencies_expand_scope_without_becoming_declared_requires(self):
        fixture = VehicleFixture()
        fixture.metadata['components']['ambient_config'].pop('requires')
        fixture.metadata['components']['ambient_config']['recorded_requires'] = {'extra-service': '1.0.0'}
        fixture.metadata['components']['extra-service'] = {
            'version': '1.0.0', 'units': ['extra-service.service'], 'requires': {}}
        vehicle, report, _ = self.capture(fixture, app='ambient')
        self.assertTrue(any('extra-service.service' in c for c in vehicle.calls))
        self.assertIn('extra-service', [x['id'] for x in report['components']])
        ambient = report['components'][0]
        self.assertEqual(ambient['metadata']['requires']['status'], 'unavailable')

    def test_untrusted_manifest_cannot_inject_paths_or_units(self):
        fixture = VehicleFixture()
        fixture.metadata['components']['ambient_config'].update(
            app_home='/etc; rm -rf /', units=['bad; reboot.service', '../../bad.service'])
        vehicle, _, _ = self.capture(fixture, app='ambient')
        self.assertFalse(any('rm -rf' in c or 'bad; reboot' in c or '../../bad' in c for c in vehicle.calls))

    def test_timeout_and_truncation_are_explicit_and_budget_is_bounded(self):
        fixture = VehicleFixture()
        original = fixture.run
        def run(command, *args, **kwargs):
            if command.startswith('journalctl'):
                return {'status': 'timeout', 'data': b''}
            return original(command, *args, **kwargs)
        fixture.run = run
        _, report, contents = self.capture(fixture, total_bytes=80, file_bytes=80)
        self.assertEqual(report['status'], 'partial')
        self.assertIn('timeout', json.dumps(report))
        self.assertLessEqual(sum(len(v) for k, v in contents.items() if k.startswith('logs/')), 80)

    def test_journal_multiline_timestamp_and_private_key_redaction(self):
        message = 'first\n-----BEGIN PRIVATE KEY-----\nPRIVATEBODY\n-----END PRIVATE KEY-----\nlast'
        record = {'__REALTIME_TIMESTAMP': str(int(END.timestamp() * 1e6)), 'MESSAGE': message}
        result = live.normalize_log((json.dumps(record) + '\n').encode(), 'journal').decode()
        self.assertNotIn('PRIVATEBODY', result)
        self.assertIn('last', result)
        self.assertTrue(all(l.startswith(str(END.year)) for l in result.splitlines()))

    def test_strict_ssh_uses_existing_trust_and_no_forwarding_or_config(self):
        ssh = live.SSH('169.254.1.2', None, self.trust)
        args = ssh.argv
        self.assertIn('StrictHostKeyChecking=yes', args)
        self.assertIn('BatchMode=yes', args)
        self.assertIn('ClearAllForwardings=yes', args)
        self.assertIn('-F', args)
        with self.assertRaises(ValueError):
            live.SSH('host; reboot', None, self.trust)
        with self.assertRaises(ValueError):
            live.SSH('169.254.1.2', None, self.root / 'missing')

    def test_transport_bounds_remote_output_and_reports_deadline(self):
        ssh = live.SSH('169.254.1.2', None, self.trust)
        ssh.argv = [sys.executable, '-c', "import sys; sys.stdout.buffer.write(b'x'*1000000)"]
        result = ssh.run('ignored', limit=100)
        self.assertEqual(result['status'], 'truncated')
        self.assertEqual(len(result['data']), 100)
        ssh.deadline = time.monotonic() - 1
        self.assertEqual(ssh.run('ignored')['status'], 'timeout')

    def test_host_key_rejection_stops_further_connections(self):
        ssh = live.SSH('169.254.1.2', None, self.trust)
        ssh.argv = [sys.executable, '-c',
                    "import sys; sys.stderr.write('Host key verification failed.'); sys.exit(255)"]
        self.assertEqual(ssh.run('ignored')['status'], 'host-key-rejected')
        with patch.object(live.subprocess, 'Popen', side_effect=AssertionError('must not retry')):
            self.assertEqual(ssh.run('ignored')['status'], 'host-key-rejected')

    def test_transport_enforces_deadline_for_a_hung_read(self):
        ssh = live.SSH('169.254.1.2', None, self.trust)
        ssh.argv = [sys.executable, '-c', 'import time; time.sleep(10)']
        ssh.deadline = time.monotonic() + 0.1
        began = time.monotonic()
        self.assertEqual(ssh.run('ignored')['status'], 'timeout')
        self.assertLess(time.monotonic() - began, 3)

    def test_cli_bad_scope_and_existing_output_never_connect(self):
        output = self.root / 'existing.zip'
        output.write_bytes(b'original')
        with patch.object(live.SSH, 'run', side_effect=AssertionError('must not connect')):
            code = live.main(['--host', '169.254.1.2', '--known-hosts', str(self.trust),
                              '--output', str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(output.read_bytes(), b'original')
            code = live.main(['--host', '169.254.1.2', '--known-hosts', str(self.trust),
                              '--output', str(self.root / 'new.zip'), '--app', '../../bad'])
            self.assertEqual(code, 1)

    @unittest.skipUnless(shutil.which('node'), 'local Node is needed for the filesystem probe fixture')
    def test_real_metadata_program_only_reads_and_distinguishes_registry(self):
        # Execute the actual stdin probe in a VM with a read-only filesystem
        # adapter; filesystem/child_process writes and network imports are absent.
        files = {
            '/var/opt/mgu-deploy/state.json': json.dumps({'apps': {
                'ambient_config': {'uid': 12345, 'version': 'old-retained'}}}),
            '/var/opt/public/oap/oap_12201/data/apps/ambient_config.json': '{"userId":12345}',
            '/var/opt/public/oap/oap_12345/source/package.json':
                '{"name":"ambient_config","version":"2.7.14"}',
            '/var/opt/mgu-updater/state/origins.json':
                '{"ambient_config":{"source":"walle/apps","requires":{"mgu-render":"0.6.0"}}}',
            '/var/opt/mgu-render/current/component.json':
                '{"id":"mgu-render","version":"0.6.0","requires":{},"units":[{"name":"mgu-render.service"}]}'
        }
        harness = """
const vm = require('vm'), files = JSON.parse(process.argv[1]);
const fds = new Map(); let next=1;
const fs = {constants:{O_RDONLY:0,O_NONBLOCK:2048},
 openSync(p,flags) {if(!(p in files)) throw Error('missing'); const fd=next++;fds.set(fd,p);return fd;},
 fstatSync(fd){return {isFile:()=>true,size:Buffer.byteLength(files[fds.get(fd)])};},
 readSync(fd,b,off,len){const value=Buffer.from(files[fds.get(fd)]);value.copy(b,off,0,len);return Math.min(value.length,len);},
 closeSync(fd){fds.delete(fd);}};
vm.runInNewContext(process.argv[2], {require(name){if(name==='fs') return fs;throw Error('unexpected import');},
 Buffer,process:{version:'v8.16.2'},console});
"""
        source = 'var OPTIONS = {"ids":["ambient_config"]};\n' + live.METADATA
        result = subprocess.run(['node', '-e', harness, json.dumps(files), source],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        app = data['components']['ambient_config']
        self.assertEqual(app['version'], '2.7.14')
        self.assertEqual(app['deployment_record']['version'], 'old-retained')
        self.assertNotIn('requires', app)  # No manufactured manifest requirements.
        self.assertIn('mgu-render', data['components'])


if __name__ == '__main__':
    unittest.main()
