#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Collect existing HU evidence over verified SSH and write a redacted local ZIP."""
import argparse
import datetime as dt
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import time

import diagnose as diag

UNIT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.@-]{0,100}\.service$')
BASE_UNITS = {
    'mgu-updater': ['mgu-updater.service'],
    'mgu-deploy': ['mgu-deploy-verify.service'],
    'mgu-uplink': ['mgu-uplink.service'],
    'mgu-render': ['mgu-render.service', 'mgu-render-hmi.service'],
    'app-privacy': ['app-privacy.service'],
    'waze-on-cluster': ['waze-on-cluster.service', 'waze-on-cluster-patchd.service',
                        'waze-on-cluster-capture.service'],
    'cluster-render': ['cluster-render.service'],
}
PROPERTIES = ('LoadState', 'ActiveState', 'SubState', 'Result', 'NRestarts',
              'ExecMainCode', 'ExecMainStatus', 'ExecMainStartTimestamp',
              'ExecMainExitTimestamp')

# This program only reads bounded regular files and process.version. It does not
# import installed JS, invoke deployment tools, write files or contact app sockets.
# It uses the HU Node 8 syntax subset; journals still work if Node cannot start.
METADATA = r"""
var fs = require('fs');
function read(p, limit) {
    var fd;
    try {
        fd = fs.openSync(p, fs.constants.O_RDONLY | fs.constants.O_NONBLOCK);
        var s = fs.fstatSync(fd);
        if (!s.isFile() || s.size > limit) return null;
        var b = Buffer.alloc(s.size), n = fs.readSync(fd, b, 0, b.length, 0);
        return b.slice(0, n).toString('utf8');
    } catch (e) { return null; }
    finally { if (fd !== undefined) fs.closeSync(fd); }
}
function obj(p) { try { return JSON.parse(read(p, 1048576)); } catch (e) { return null; } }
function dict(o) { return o && typeof o === 'object' && !Array.isArray(o); }
var state = obj('/var/opt/mgu-deploy/state.json') || {};
var origins = obj('/var/opt/mgu-updater/state/origins.json') || {};
var out = {components: {}, context: {node: process.version,
    vehicle_time: new Date().toISOString(),
    firmware: read('/etc/os-release-id-dlt', 4096) || read('/etc/os-release', 8192),
    uptime: read('/proc/uptime', 1024),
    boot_id: read('/proc/sys/kernel/random/boot_id', 1024),
    updater_trial: read('/var/opt/mgu-updater/trial', 4096),
    updater_trial_reason: read('/var/opt/mgu-updater/trial-reason', 8192),
    updater_rolled_back: read('/var/opt/mgu-updater/rolled-back', 4096)}};
out.inventory = {};
['apps', 'tools'].forEach(function(kind) {
    var table = dict(state[kind]) ? state[kind] : {};
    out.inventory[kind] = Object.keys(table).slice(0, 128).map(function(id) {
        return {id: id, version: table[id] && table[id].version};
    });
});
var ids = OPTIONS.ids.slice();
for (var i = 0; i < ids.length && i < 32; i++) {
    var id = ids[i], entry = {}, manifest = null;
    if (!/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$/.test(id)) continue;
    var tool = obj('/var/opt/' + id + '/current/component.json');
    if (tool && tool.id === id) manifest = tool;
    if (id === 'mgu-deploy' && !manifest) {
        tool = obj('/var/opt/mgu-deploy/component.json');
        if (tool && tool.id === id) manifest = tool;
    }
    var recorded = dict(state.apps) && state.apps[id];
    var registry = obj('/var/opt/public/oap/oap_12201/data/apps/' + id + '.json');
    var uid = registry && registry.userId;
    // The deployment record is retained separately when registration is missing.
    if (recorded) entry.deployment_record = {version: recorded.version};
    if (/^[0-9]{1,9}$/.test(String(uid))) {
        var home = '/var/opt/public/oap/oap_' + uid;
        var pkg = obj(home + '/source/package.json');
        if (pkg && pkg.name === id) {
            entry.app_home = home;
            entry.registered = true;
            manifest = pkg;
        }
    }
    if (manifest) {
        if (typeof manifest.version === 'string') entry.version = manifest.version;
        if (dict(manifest.requires)) entry.requires = manifest.requires;
        entry.units = (Array.isArray(manifest.units) ? manifest.units : []).map(function(u) {
            return u && u.name;
        });
    }
    var origin = origins[id];
    if (dict(origin) && typeof origin.source === 'string') {
        entry.source = {id: origin.source, observed_at: out.context.vehicle_time};
        // Source requirements are an installation record, not a disk manifest.
        if (dict(origin.requires)) entry.recorded_requires = origin.requires;
    }
    var deps = entry.requires || entry.recorded_requires;
    if (dict(deps)) Object.keys(deps).forEach(function(dep) {
        if (/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$/.test(dep) &&
            ids.indexOf(dep) < 0 && ids.length < 32) ids.push(dep);
    });
    out.components[id] = entry;
}
console.log(JSON.stringify(out));
"""


class SSH:
    def __init__(self, host, identity, known_hosts, port=22, user='root', seconds=120):
        # Use a verified literal HU address, never broad network scanning or aliases
        # whose local SSH configuration might introduce forwards or remote commands.
        ipaddress.ip_address(host)
        if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', user) or not 1 <= port <= 65535:
            raise ValueError('invalid SSH target')
        for path in (known_hosts, identity):
            if path and not Path(path).expanduser().is_file():
                raise ValueError('SSH trust/key file is missing')
        self.argv = ['ssh', '-F', 'NUL' if os.name == 'nt' else '/dev/null', '-T',
                     '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                     '-o', 'UserKnownHostsFile=' + str(Path(known_hosts).expanduser().resolve()),
                     '-o', 'GlobalKnownHostsFile=' + ('NUL' if os.name == 'nt' else '/dev/null'),
                     '-o', 'UpdateHostKeys=no',
                     '-o', 'ConnectTimeout=5', '-o', 'ConnectionAttempts=1',
                     '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=1',
                     '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes',
                     '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
                     '-p', str(port), '-l', user]
        if identity:
            self.argv += ['-o', 'IdentitiesOnly=yes', '-i',
                          str(Path(identity).expanduser().resolve())]
        self.argv += ['--', host]
        self.deadline = time.monotonic() + seconds
        self.contacted = False
        self.unavailable = None

    def run(self, command, data=b'', limit=256 * 1024):
        if self.unavailable:
            return {'status': self.unavailable, 'data': b''}
        left = self.deadline - time.monotonic()
        if left <= 0:
            return {'status': 'timeout', 'data': b''}
        try:
            proc = subprocess.Popen(self.argv + [command], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.unavailable = 'ssh-unavailable'
            return {'status': self.unavailable, 'data': b''}
        chunks, errors = bytearray(), bytearray()
        overflow = threading.Event()

        def reader(stream, target, cap):
            while True:
                part = stream.read(4096)
                if not part:
                    break
                remaining = cap - len(target)
                target.extend(part[:max(0, remaining)])
                if len(part) > remaining:
                    overflow.set()
                    proc.kill()
                    break

        def writer():
            try:
                proc.stdin.write(data)
                proc.stdin.close()
            except (OSError, BrokenPipeError):
                pass

        threads = [threading.Thread(target=reader, args=(proc.stdout, chunks, limit + 1), daemon=True),
                   threading.Thread(target=reader, args=(proc.stderr, errors, 8192), daemon=True),
                   threading.Thread(target=writer, daemon=True)]
        for thread in threads:
            thread.start()
        timed_out = False
        try:
            proc.wait(timeout=min(12, left))
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.wait()
        for thread in threads:
            thread.join(timeout=1)
        proc.stdout.close()
        proc.stderr.close()
        if proc.returncode == 255:
            error = bytes(errors).lower()
            self.unavailable = ('host-key-rejected' if b'host key' in error or b'identification has changed' in error
                                else 'authentication-denied' if b'permission denied' in error
                                else 'connection-failed')
            return {'status': self.unavailable, 'data': b''}
        if timed_out:
            return {'status': 'timeout', 'data': b''}
        if overflow.is_set() or len(chunks) > limit:
            return {'status': 'truncated', 'data': bytes(chunks[:limit])}
        self.contacted = True
        return {'status': 'ok' if proc.returncode == 0 else 'failed',
                'code': proc.returncode, 'data': bytes(chunks)}


def file_command(path, cap, tail=True):
    """Only fixed, validated paths supplied by the collection plan are used."""
    quoted = shlex.quote(path)
    return ('if [ -L {p} ] || [ ! -f {p} ]; then exit 44; fi; '
            'if [ ! -r {p} ]; then exit 45; fi; '
            '{tool} -c {cap} {p}').format(p=quoted, tool='tail' if tail else 'head', cap=cap)


def normalize_log(data, fmt):
    """Journal record timestamps anchor multiline messages; file continuations don't."""
    if fmt != 'journal':
        return diag.redact(data.decode('utf-8', errors='replace')).encode('utf-8')
    records = []
    for raw in data.decode('utf-8', errors='replace').splitlines():
        try:
            record = json.loads(raw)
            when = dt.datetime.fromtimestamp(int(record['__REALTIME_TIMESTAMP']) / 1000000, diag.UTC)
            message = record.get('MESSAGE')
            if not isinstance(message, str):
                continue
            # Redact before splitting: PEM/private material may span several lines.
            for line in diag.redact(message).splitlines():
                records.append(when.isoformat() + ' ' + line)
        except (ValueError, KeyError, TypeError, OverflowError, OSError):
            continue
    return ('\n'.join(records) + ('\n' if records else '')).encode('utf-8')


def plan_files(name, entry):
    paths = []
    if name == 'mgu-updater':
        paths += ['/tmp/mgu-updater.log', '/tmp/mgu-updater.log.1']
    if name in ('cluster-render', 'waze-on-cluster'):
        p = '/var/opt/{0}/log/{0}.log'.format(name)
        paths += [p, p + '.1']
    home = entry.get('app_home', '')
    if re.fullmatch(r'/var/opt/public/oap/oap_[0-9]{1,9}', home):
        paths += [home + '/data/' + name + '.log', home + '/data/' + name + '.log.1']
    return paths


def collect_live(transport, output, app=None, minutes=30, until=None,
                 file_bytes=256*1024, total_bytes=4*1024*1024):
    began = dt.datetime.now(diag.UTC)
    end = until or began
    start = end - dt.timedelta(minutes=minutes)
    ids = diag.selection(app, {})
    seed = ('var OPTIONS = ' + json.dumps({'ids': ids}) + ';\n' + METADATA).encode()
    probe = transport.run('/usr/bin/node -', seed, limit=diag.MANIFEST_MAX)
    failures, context, inventory = [], {}, {}
    components = {}
    if probe['status'] == 'ok':
        try:
            meta = json.loads(probe['data'])
            if not isinstance(meta.get('components'), dict):
                raise ValueError()
            components = {k: v for k, v in meta['components'].items()
                          if diag.ID.fullmatch(k) and isinstance(v, dict)}
            context = diag.clean(meta.get('context', {}))
            inventory = diag.clean(meta.get('inventory', {}))
        except (ValueError, TypeError, AttributeError, RecursionError):
            failures.append({'probe': 'metadata', 'status': 'invalid-response'})
    else:
        failures.append({'probe': 'metadata', 'status': probe['status']})
    # Journal collection does not depend on the installed Node, deploy tool or app.
    # This shell observation also proves SSH access when metadata Node cannot run.
    shell_context = transport.run(
        "date -u '+%Y-%m-%dT%H:%M:%SZ'; "
        "head -c 1024 /proc/uptime; head -c 256 /proc/sys/kernel/random/boot_id; "
        "head -c 4096 /etc/os-release-id-dlt; "
        "head -c 4096 /proc/meminfo; df -Pk /var/opt /run /tmp", limit=16384)
    if shell_context['status'] in ('ok', 'failed'):
        context['passive_system_observation'] = diag.redact(shell_context['data'].decode('utf-8', 'replace'))
    else:
        failures.append({'probe': 'system-context', 'status': shell_context['status']})
    ids = diag.selection(app, components, include_recorded=True)[:32]
    remaining = total_bytes
    captures = []
    with tempfile.TemporaryDirectory(prefix='mgu-diagnostics-') as directory:
        root = Path(directory)
        for name in ids:
            entry = components.setdefault(name, {})
            entry['logs'] = []
            declared = entry.get('units', [])
            declared = declared if isinstance(declared, list) else []
            units = list(dict.fromkeys(BASE_UNITS.get(name, []) + [
                u for u in declared if isinstance(u, str) and UNIT.fullmatch(u)]))[:4]
            observations = []
            for unit in units:
                state = transport.run('systemctl show --no-pager ' + shlex.quote(unit) + ' ' +
                                      ' '.join('-p ' + p for p in PROPERTIES), limit=8192)
                if state['status'] == 'ok':
                    values = dict(line.split('=', 1) for line in
                                  state['data'].decode('utf-8', 'replace').splitlines() if '=' in line)
                    observations.append(dict(unit=unit, observed_at=dt.datetime.now(diag.UTC).isoformat(),
                                             **{p: values[p] for p in PROPERTIES if p in values}))
                    if values.get('LoadState') == 'loaded' and 'service' not in entry:
                        entry['service'] = {'unit': unit, 'load': values.get('LoadState'),
                                            'active': values.get('ActiveState'), 'sub': values.get('SubState'),
                                            'result': values.get('Result'), 'restarts': values.get('NRestarts'),
                                            'observed_at': dt.datetime.now(diag.UTC).isoformat()}
                else:
                    observations.append({'unit': unit, 'status': state['status']})
            entry['service_observations'] = observations
            jobs = [(unit, 'journal',
                     'journalctl --no-pager -o json -n 200 --since @{0} --until @{1} -u {2}'.format(
                         int(start.timestamp()), int(end.timestamp()), shlex.quote(unit))) for unit in units]
            jobs += [(path, 'iso-lines', file_command(path, file_bytes + 1))
                     for path in plan_files(name, entry)]
            for label, fmt, command in jobs[:8]:
                if remaining <= 0:
                    entry['logs'].append({'status': 'failed'})
                    captures.append({'component': name, 'stream': label, 'status': 'budget-exhausted'})
                    continue
                cap = min(file_bytes, remaining)
                if fmt != 'journal':
                    command = file_command(label, cap + 1)
                # journalctl emits complete JSON entries, with an independent local
                # receive cap; oversized entries are reported, never accepted whole.
                result = transport.run(command, limit=cap + 1)
                status = result['status']
                detail = {'component': name, 'stream': label, 'status': status}
                captures.append(detail)
                if status not in ('ok', 'truncated'):
                    entry['logs'].append({'status': 'timeout' if status == 'timeout' else
                                          'missing' if result.get('code') == 44 else
                                          'denied' if result.get('code') == 45 else 'failed'})
                    continue
                raw = result['data']
                cut = status == 'truncated' or len(raw) > cap
                if cut and fmt != 'journal':
                    raw = raw[-cap:].partition(b'\n')[2]
                elif cut:
                    raw = raw[:cap].rpartition(b'\n')[0]
                normalized = normalize_log(raw, fmt)
                if len(normalized) > cap:
                    normalized = normalized[:cap].rpartition(b'\n')[0]
                    cut = True
                local = '{}-{}.log'.format(name, len(entry['logs']))
                (root / local).write_bytes(normalized)
                entry['logs'].append({'path': local, 'format': 'iso-lines'})
                detail.update(truncated=cut, bytes=len(normalized))
                remaining -= max(len(normalized), min(len(result['data']), cap))
        # Metadata is allowlisted in the final report; never persist raw inputs.
        safe_components = diag.clean(components)
        (root / 'capture.json').write_text(json.dumps({
            'schema': 1, 'captured_at': began.isoformat(),
            'components': safe_components}), encoding='utf-8')
        report, payloads = diag.collect(root, app, minutes, end, file_bytes, total_bytes,
                                       include_recorded=True)
    report.update(evidence='live-ssh', vehicle_contacted=transport.contacted,
                  context=context, collection_failures=failures, captures=diag.clean(captures),
                  collection_started_at=began.isoformat(),
                  collection_finished_at=dt.datetime.now(diag.UTC).isoformat(),
                  deployment_inventory=inventory,
                  component_observations=diag.clean({
                      name: {k: components[name][k] for k in
                             ('registered', 'deployment_record', 'recorded_requires')
                             if k in components[name]} for name in ids}),
                  service_observations=diag.clean({
                      name: components[name].get('service_observations', []) for name in ids}))
    report['notes'][0] = 'Existing vehicle evidence collected over verified SSH; no repair or service activation performed.'
    report['notes'] += [
        'Journal streams are limited to the newest 200 records in the requested absolute time window; file logs are bounded tails.',
        'The log window uses the computer clock. Compare vehicle_time and the symptom time before interpreting an empty window.',
        'Deployment inventory and recorded requirements are retained records, not proof of active registration or current manifest contents.',
        'Known default paths are inspected; custom log locations, DLT-only logs and unexported firmware logs may be unavailable.']
    if len(diag.selection(app, components, include_recorded=True)) > 32:
        failures.append({'probe': 'dependencies', 'status': 'component-limit'})
    if failures or any(c['status'] != 'ok' or c.get('truncated') for c in captures):
        report['status'] = 'partial'
    if not transport.contacted:
        report['status'] = 'partial'
    diag.write_bundle(output, report, payloads)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', required=True, help='verified HU IP address from the ENET session')
    p.add_argument('--identity', help='existing private key; omitted = existing SSH agent')
    p.add_argument('--known-hosts', required=True, help='existing verified OpenSSH host-key record')
    p.add_argument('--port', type=int, default=22)
    p.add_argument('--user', default='root')
    p.add_argument('--output', required=True, help='new private local ZIP; never overwritten')
    p.add_argument('--app', help='app ID, waze/maps or ambient; omitted = basic')
    p.add_argument('--minutes', type=diag.bounded_int(1, 1440), default=30)
    p.add_argument('--until', type=diag.timestamp, help='incident window end, ISO 8601 with timezone')
    p.add_argument('--file-kib', type=diag.bounded_int(1, 1024), default=256)
    p.add_argument('--total-kib', type=diag.bounded_int(1, 16384), default=4096)
    p.add_argument('--seconds', type=diag.bounded_int(15, 600), default=120)
    args = p.parse_args(argv)
    try:
        diag.selection(args.app, {})  # Reject invalid scope before any connection.
        output = Path(args.output).expanduser()
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError('output must be a new ZIP in an existing local directory')
        transport = SSH(args.host, args.identity, args.known_hosts, args.port, args.user, args.seconds)
        report = collect_live(transport, output, args.app, args.minutes, args.until,
                              args.file_kib * 1024, args.total_kib * 1024)
    except (ValueError, OSError, RecursionError):
        print('Cannot create live diagnostic bundle; check local arguments, SSH files and output.', file=sys.stderr)
        return 1
    print('Diagnostic bundle created; coverage={}; vehicle_contacted={}'.format(
        report['status'], str(report['vehicle_contacted']).lower()))
    return 0 if report['vehicle_contacted'] else 1


if __name__ == '__main__':
    sys.exit(main())
