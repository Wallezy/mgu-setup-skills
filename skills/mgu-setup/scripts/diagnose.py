#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build a bounded, redacted diagnostic bundle from existing local evidence.

No network, subprocesses, vehicle commands, archive extraction or repair actions.
See references/diagnostics.md for the capture.json contract and live-use boundary.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

BASE = ('robertn_store', 'mgu-updater', 'mgu-deploy', 'mgu-uplink',
        'mgu-render', 'mgu-python', 'app-privacy', 'app-manager')
MAP = ('robertn_waze_cluster', 'waze-on-cluster', 'cluster-render')
ALIASES = {'waze': MAP[0], 'maps': MAP[0], 'ambient': 'ambient_config'}
ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$')
SENSITIVE = re.compile(r'password|passwd|passphrase|token|secret|credential|authorization|cookie|vin|private.?key|certificate|latitude|longitude|location|profile.?id|driver.?id|account|email|车架号|车身号码|密码|令牌', re.I)
UTC = dt.timezone.utc
MANIFEST_MAX = 1024 * 1024


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be an ISO 8601 string with timezone')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp needs timezone')
    return result.astimezone(UTC)


def redact(text):
    """Conservative text filter; no raw evidence is written to the bundle."""
    text = re.sub(r'-----BEGIN [^-\r\n]+-----.*?(?:-----END [^-\r\n]+-----|\Z)',
                  '[REDACTED PEM]', text, flags=re.S)
    text = re.sub(r'(?i)\b(?:ssh-(?:rsa|ed25519)|ecdsa-sha2-\S+)\s+\S+(?:[^\r\n]*)', '[REDACTED SSH KEY]', text)
    text = re.sub(r'(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_.=~:-]+', '[REDACTED AUTH]', text)
    # Remove userinfo and all query/fragment values, including signed URLs.
    def url(match):
        value = re.sub(r'(?<=://)[^/\s]+@', '[REDACTED]@', match[0])
        return re.split(r'[?#]', value, maxsplit=1)[0] + ('?[REDACTED]' if re.search(r'[?#]', value) else '')
    text = re.sub(r'https?://[^\s<>"\']+', url, text)
    text = re.sub(r'''(?ix)(["']?(?:[\w.-]*(?:password|passwd|passphrase|token|secret|credential|authorization|cookie|vin|private.?key|latitude|longitude|location|profile.?id|driver.?id|account|email|车架号|车身号码|密码|令牌)[\w.-]*)["']?\s*[:=：＝]\s*)("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\r\n,;}]+)''', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)\b[A-HJ-NPR-Z0-9]{17}\b', '[REDACTED VIN]', text)
    text = re.sub(r'\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b', '[REDACTED EMAIL]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED IP]', text)
    text = re.sub(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b', '[REDACTED MAC]', text)
    text = re.sub(r'(?<![\w.])-?\d{1,3}\.\d{4,}\s*[,/]\s*-?\d{1,3}\.\d{4,}(?![\w.])', '[REDACTED COORDINATES]', text)
    # Long opaque credentials and key-body lines, including partial PEM exports.
    text = re.sub(r'(?<![\w])[A-Za-z0-9+/=_-]{48,}(?![\w])', '[REDACTED OPAQUE]', text)
    return ''.join(c for c in text if c in '\n\t' or ord(c) >= 32).replace('\x7f', '')


def clean(value):
    if isinstance(value, dict):
        return {redact(str(k)): '[REDACTED]' if SENSITIVE.search(str(k)) else clean(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return redact(value) if isinstance(value, str) else value


def read_file(root, relative, limit, tail=False):
    """Reject links and special files; read at most limit bytes plus one sentinel."""
    if not isinstance(relative, str):
        raise ValueError('invalid evidence path')
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in ('.', '..') for p in path.parts):
        raise ValueError('evidence path must stay inside input directory')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink evidence is not accepted')
    if not current.resolve().is_relative_to(root):
        raise ValueError('evidence path escapes input directory')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(str(current), flags)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('evidence must be a regular file')
        truncated = info.st_size > limit
        if truncated and tail:
            stream.seek(info.st_size - limit)
        data = stream.read(limit + 1)
        truncated = truncated or len(data) > limit
        data = data[:limit]
    if truncated and tail:
        # Never include a fragment that lost its timestamp or credential label.
        data = data.partition(b'\n')[2]
    return data, truncated


def capture(root):
    try:
        data, cut = read_file(root, 'capture.json', MANIFEST_MAX)
        if cut:
            raise ValueError('capture.json exceeds 1 MiB')
        value = json.loads(data)
        if not isinstance(value, dict) or value.get('schema') != 1:
            raise ValueError('unsupported capture schema')
        components = value.get('components')
        if not isinstance(components, dict) or len(components) > 128:
            raise ValueError('components must be an object with at most 128 entries')
        if any(not ID.fullmatch(k) for k in components):
            raise ValueError('invalid component identifier')
        return value, None
    except (OSError, ValueError, RecursionError) as exc:
        # Do not copy filesystem error messages, filenames or invalid JSON contents.
        return {'components': {}}, type(exc).__name__ + ': capture unavailable or invalid'


def selection(app, components):
    chosen = []
    if app:
        app = ALIASES.get(app.lower(), app)
        if not ID.fullmatch(app):
            raise ValueError('invalid app identifier')
        chosen.extend(MAP if app in MAP else (app,))
    chosen = list(dict.fromkeys(chosen + list(BASE)))
    for name in chosen:
        entry = components.get(name, {})
        deps = entry.get('requires', {}) if isinstance(entry, dict) else {}
        if isinstance(deps, dict):
            for dep in deps:
                if isinstance(dep, str) and ID.fullmatch(dep) and dep not in chosen and len(chosen) < 128:
                    chosen.append(dep)
    return chosen


def log_window(data, start, end, fmt):
    text = data.decode('utf-8', errors='replace')
    # Redact multiline private material before splitting into time-filtered records.
    text = re.sub(r'-----BEGIN [^-\r\n]+-----.*?(?:-----END [^-\r\n]+-----|\Z)',
                  '[REDACTED PEM]', text, flags=re.S)
    lines, unknown, outside = [], 0, 0
    for line in text.splitlines():
        try:
            if fmt == 'jsonl':
                entry = json.loads(line)
                when = timestamp(entry['timestamp'])
                body = json.dumps(clean(entry), ensure_ascii=False)
            else:
                when = timestamp(line.split(' ', 1)[0])
                body = redact(line)
        except (ValueError, TypeError, KeyError, IndexError, RecursionError):
            unknown += 1
            continue
        if start <= when <= end:
            lines.append(body)
        else:
            outside += 1
    return ('\n'.join(lines) + ('\n' if lines else '')).encode('utf-8'), unknown, outside


def metadata(entry):
    result = {}
    for key in ('version', 'requires', 'source', 'service'):
        value = entry.get(key)
        valid = isinstance(value, str) if key == 'version' else isinstance(value, dict)
        if not valid:
            result[key] = {'status': 'unavailable'}
            continue
        if key == 'source':
            value = {k: value[k] for k in ('edition', 'id', 'url', 'version', 'sha256', 'observed_at') if k in value}
        if key == 'service':
            value = {k: value[k] for k in ('unit', 'load', 'active', 'sub', 'result', 'restarts', 'observed_at') if k in value}
        if key == 'service' and not all(isinstance(value.get(k), str) and value[k] for k in ('unit', 'active')):
            result[key] = {'status': 'unavailable'}
            continue
        if key == 'source' and not any(isinstance(value.get(k), str) and value[k] for k in ('id', 'url')):
            result[key] = {'status': 'unavailable'}
            continue
        sanitized = clean(value)
        if key == 'source' and isinstance(value.get('sha256'), str) and re.fullmatch(r'[0-9a-fA-F]{64}', value['sha256']):
            sanitized['sha256'] = value['sha256']
        result[key] = {'status': 'observed', 'value': sanitized}
    return result


def collect(root, app=None, minutes=30, end=None, file_bytes=256*1024, total_bytes=4*1024*1024):
    root = Path(root).expanduser().resolve()
    observed, error = capture(root)
    end = end or dt.datetime.now(UTC)
    start = end - dt.timedelta(minutes=minutes)
    report = {'schema': 1, 'mode': 'app' if app else 'basic', 'app': redact(app) if app else None,
              'evidence': 'local-export', 'vehicle_contacted': False, 'repairs_performed': False,
              'window': {'start': start.isoformat(), 'end': end.isoformat()},
              'limits': {'per_file_bytes': file_bytes, 'log_total_bytes': total_bytes,
                         'manifest_bytes': MANIFEST_MAX, 'logs_per_component': 8},
              'capture_error': error, 'components': [], 'notes': [
                  'Evidence is an exported observation, not a live health check or proof of a fix.',
                  'Missing observations do not prove a component is absent.',
                  'Untimed log lines are excluded; inspect coverage counts before drawing conclusions.',
                  'Redaction is best effort. Review privately before sharing; no upload is performed.']}
    try:
        report['captured_at'] = timestamp(observed.get('captured_at')).isoformat()
        report['capture_time_in_window'] = start <= timestamp(observed['captured_at']) <= end
    except (ValueError, TypeError):
        report['captured_at'] = None
        report['capture_time_in_window'] = False
    payloads, remaining = {}, total_bytes
    for name in selection(app, observed['components']):
        report_id = redact(name)
        archive_id = name if report_id == name else 'redacted-component-{}'.format(len(report['components']))
        entry = observed['components'].get(name)
        if not isinstance(entry, dict):
            report['components'].append({'id': report_id, 'status': 'unavailable', 'reason': 'no component observation'})
            continue
        item = {'id': report_id, 'metadata': metadata(entry), 'logs': []}
        logs = entry.get('logs', [])
        if not isinstance(logs, list):
            logs = []
        item['logs_omitted_by_count'] = max(0, len(logs) - 8)
        for index, spec in enumerate(logs[:8]):
            record = {'index': index}
            item['logs'].append(record)
            if not isinstance(spec, dict):
                record.update(status='unavailable', reason='invalid log descriptor')
                continue
            if spec.get('status', 'ok') != 'ok':
                # Preserve failure class without arbitrary unredacted error strings.
                status = spec.get('status')
                record.update(status='unavailable', reason=status if status in ('missing', 'failed', 'timeout', 'denied') else 'capture failed')
                continue
            if remaining <= 0:
                record.update(status='omitted', reason='total log budget reached')
                continue
            fmt = spec.get('format', 'iso-lines')
            if fmt not in ('iso-lines', 'jsonl'):
                record.update(status='unavailable', reason='unsupported timestamp format')
                continue
            try:
                data, cut = read_file(root, spec.get('path'), file_bytes, tail=True)
                content, unknown, outside = log_window(data, start, end, fmt)
                # Avoid cutting through a redaction token or UTF-8 sequence.
                clipped = len(content) > min(remaining, file_bytes)
                if clipped:
                    content = content[:min(remaining, file_bytes)].rpartition(b'\n')[0]
                    if content:
                        content += b'\n'
                record.update(status='partial' if cut or clipped or unknown else ('ok' if content else 'empty'),
                              input_truncated=cut, output_truncated=clipped,
                              untimed_lines_excluded=unknown, outside_window_lines=outside,
                              bytes=len(content))
                archive_path = 'logs/{}/{}.log'.format(archive_id, index)
                payloads[archive_path] = content
                record.update(file=archive_path, sha256=hashlib.sha256(content).hexdigest())
                remaining -= len(content)
            except (OSError, ValueError, RecursionError) as exc:
                record.update(status='unavailable', reason=type(exc).__name__)
        meta = item['metadata']
        item['status'] = 'ok' if (all(v['status'] == 'observed' for v in meta.values())
                                  and item['logs'] and all(v['status'] == 'ok' for v in item['logs'])
                                  and not item['logs_omitted_by_count']) else 'partial'
        report['components'].append(item)
    if 'ambient_config' in [x['id'] for x in report['components']]:
        report['notes'].append('氛围灯“车身模块未响应，暂时无法自定义颜色”是采集覆盖案例，未证明已修复或车身模块损坏。关注已有 TASU 初始化、诊断通道错误/忙、拒绝、超时、DA5F/E3D1、空/短记录及扫描重叠日志；缺少细分日志时原因未知。不触发重新查找或 UDS 请求。')
    if any(x['id'] in MAP for x in report['components']):
        report['notes'].append('地图关联 Waze 应用、waze-on-cluster、cluster-render；手机导航、显示目标/Off、驾驶员配置与实际画面仍需已有证据，不能由服务 active 推定显示正常。')
    report['status'] = 'complete' if (not error and report['capture_time_in_window'] and all(x['status'] == 'ok' for x in report['components'])) else 'partial'
    return report, payloads


def markdown(report):
    lines = ['# MGU 诊断 / Diagnostics', '', '采集状态 / Coverage: **{}**'.format(report['status']),
             '', '来源：已有本地导出；未连接车辆，未执行修复、重启或写入车机。',
             '', '窗口：{} → {}'.format(report['window']['start'], report['window']['end']),
             '采集时间：{}；位于窗口内：{}'.format(report['captured_at'], report['capture_time_in_window']), '',
             '| 组件 | 覆盖 | 版本 | 服务 | 依赖 | 来源 | 日志 |', '|---|---|---|---|---|---|---|']
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')
    for item in report['components']:
        meta = item.get('metadata', {})
        values = [item['id'], item['status']]
        for field in ('version', 'service', 'requires', 'source'):
            value = meta.get(field, {}).get('value', 'unavailable')
            values.append(json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value)
        values.append(', '.join(str(x['index']) + ':' + x['status'] + (' (' + x['reason'] + ')' if x.get('reason') else '') for x in item.get('logs', [])) or 'unavailable')
        lines.append('| ' + ' | '.join(cell(x) for x in values) + ' |')
    lines.extend(['', '逐文件错误、截断、时间过滤计数与哈希见 report.json。', ''])
    if report['capture_error']:
        lines.append('- ' + report['capture_error'])
    lines.extend('- ' + note for note in report['notes'])
    return '\n'.join(lines) + '\n'


def write_bundle(output, report, payloads):
    output = Path(output).expanduser()
    # Exclusive creation avoids overwriting an earlier case or a symlink target.
    fd = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as target:
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, data in payloads.items():
                archive.writestr(name, data)
            archive.writestr('report.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            archive.writestr('report.md', markdown(report))


def bounded_int(low, high):
    def parse(value):
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError('must be between {} and {}'.format(low, high))
        return number
    return parse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='existing local evidence directory containing capture.json')
    parser.add_argument('--output', required=True, help='new private ZIP file; never overwritten')
    parser.add_argument('--app', help='app ID, waze/maps or ambient; omitted = basic diagnostics')
    parser.add_argument('--minutes', type=bounded_int(1, 1440), default=30)
    parser.add_argument('--until', type=timestamp, help='ISO time with timezone; default now, set to capture time for historical evidence')
    parser.add_argument('--file-kib', type=bounded_int(1, 1024), default=256)
    parser.add_argument('--total-kib', type=bounded_int(1, 16384), default=4096)
    args = parser.parse_args(argv)
    try:
        report, payloads = collect(args.input, args.app, args.minutes, args.until,
                                   args.file_kib * 1024, args.total_kib * 1024)
        write_bundle(args.output, report, payloads)
    except (ValueError, OSError) as exc:
        print('Cannot create diagnostic bundle: ' + type(exc).__name__, file=sys.stderr)
        return 1
    print('Diagnostic bundle created; coverage=' + report['status'] + '; vehicle_contacted=false')
    return 0


if __name__ == '__main__':
    sys.exit(main())
