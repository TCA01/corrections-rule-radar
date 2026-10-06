"""Bounded, isolated production attempts. No live mutation before full success."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.operations import now
from pipeline.snapshot import write_json
from scripts.validate_public import validate
from pipeline.operations.public_status import publish_status

ROOT = Path(__file__).resolve().parents[1]
DEADLINE_SECONDS = 720
RETRY_DELAY_SECONDS = 5
TRANSIENT = {'TIMEOUT', 'NETWORK_ERROR'}


def read(root, rel, default=None):
    path = root / rel
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def clone_inputs(root, candidate):
    # Explicit trees: never copy secrets, Git, node_modules, or staging itself.
    for rel in ('pipeline', 'scripts', 'schemas', 'data/seed', 'data/registry',
                'data/snapshots', 'data/ops', 'public/api/v1'):
        source = root / rel
        if source.exists(): shutil.copytree(source, candidate / rel, ignore=shutil.ignore_patterns('__pycache__'))
    queue = root / 'data/reports/discovery_candidates_api.json'
    if queue.exists():
        (candidate / 'data/reports').mkdir(parents=True, exist_ok=True)
        shutil.copy2(queue, candidate / 'data/reports' / queue.name)


def execute_candidate(candidate, options, timeout):
    args = [sys.executable, '-u', 'scripts/production_sync.py', '--worker']
    args += ['--' + key.replace('_', '-') for key, enabled in options.items() if enabled]
    log = candidate / 'worker_stdout.log'
    with log.open('wb') as output:
        process = subprocess.Popen(args, cwd=candidate, stdout=output, stdin=subprocess.DEVNULL)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
            return {'result': 'BLOCKED', 'error_summary': {'code': 'SYNC_DEADLINE_EXCEEDED'}}
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=10)
    report = read(candidate, 'data/reports/production_sync.json', {})
    if code or report.get('result') not in ('PUBLISHED', 'NO_CHANGE'):
        report['result'] = 'BLOCKED'
        if not report.get('error_summary'): report['error_summary'] = {'code': 'SYNC_WORKER_FAILED'}
    return report


def retryable(report, candidate):
    code = report.get('error_summary', {}).get('code')
    if code in TRANSIENT: return True
    if code == 'HTTP_ERROR':
        status = report.get('error_summary', {}).get('http_status') or 0
        return status == 429 or 500 <= status <= 599
    # Collection catches API errors per rule. Only an all-transient unresolved
    # set qualifies; malformed bodies, authentication and identity review don't.
    resolution = read(candidate, 'data/reports/core_resolution.json', {})
    rows = resolution if isinstance(resolution, list) else resolution.get('entries', [])
    failures = [row for row in rows if row.get('status') != 'RESOLVED']
    return bool(failures) and all(row.get('review_reason') in TRANSIENT or
        row.get('review_reason') == 'HTTP_ERROR' and (row.get('http_status') == 429 or 500 <= (row.get('http_status') or 0) <= 599) for row in failures)


def promote(root, candidate, report, deadline):
    """Validate first, then local reversible transaction; never promote a failure."""
    if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
    validate(candidate / 'public/api/v1')
    if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
    if report['result'] == 'NO_CHANGE':
        old = root / 'public/api/v1'; new = candidate / 'public/api/v1'
        old_files = {p.relative_to(old): p.read_bytes() for p in old.rglob('*.json')}
        if old_files != {p.relative_to(new): p.read_bytes() for p in new.rglob('*.json')}:
            raise ValueError('NO_CHANGE_CONTENT_DRIFT')
    replacements = []
    # State files are staged and backed up before any live directory switch.
    backup = candidate / 'promotion_backup'
    for rel in ('data/registry/state.json', 'data/registry/rules.json',
                'data/registry/events.json', 'data/registry/change_history.json'):
        source = candidate / rel; target = root / rel
        if source.exists() and (not target.exists() or source.read_bytes() != target.read_bytes()):
            if report['result'] == 'NO_CHANGE': raise ValueError('NO_CHANGE_STATE_DRIFT')
            prior = backup / rel
            if target.exists(): prior.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(target, prior)
            replacements.append((source, target, prior))
    new_snapshots = []
    # A NO_CHANGE candidate can contain a different download token in an
    # attachment URL. It must not grow the retained legal snapshot set merely
    # because a poll happened. Raw cache evidence is private and content keyed.
    sources = (list((candidate / 'data/snapshots').rglob('*.json')) if report['result'] == 'PUBLISHED' else []) + list((candidate / 'data/raw_cache').glob('*'))
    for source in sources:
        if not source.is_file(): continue
        target = root / source.relative_to(candidate)
        if target.exists() and source.read_bytes() != target.read_bytes(): raise ValueError('IMMUTABLE_SNAPSHOT_DRIFT')
        if not target.exists(): new_snapshots.append((source, target))
    switched = False; applied = []; added = []
    output = root / 'public/api/v1'; prior_public = candidate / 'promotion_public_backup'
    try:
        for source, target in new_snapshots:
            if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target); added.append(target)
        for source, target, prior in replacements:
            if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix('.promotion.tmp'); shutil.copy2(source, temp); os.replace(temp, target)
            applied.append((target, prior))
        if report['result'] == 'PUBLISHED':
            if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
            os.replace(output, prior_public)
            try: os.replace(candidate / 'public/api/v1', output)
            except Exception:
                os.replace(prior_public, output); raise
            switched = True
        if time.monotonic() >= deadline: raise TimeoutError('SYNC_DEADLINE_EXCEEDED')
    except Exception:
        if switched:
            os.replace(output, candidate / 'rejected_public'); os.replace(prior_public, output)
        for target, prior in reversed(applied):
            if prior.exists(): shutil.copy2(prior, target)
            else: target.unlink(missing_ok=True)
        for target in added: target.unlink(missing_ok=True)
        raise


def retain_operations(root, candidate, report):
    # These operational outputs are separate from the published legal dataset.
    for rel in ('data/ops/health.json', 'data/ops/discovery_pages.json'):
        value = read(candidate, rel)
        if value is not None: write_json(root / rel, value)
    for source in (candidate / 'data/reports').glob('*.json'):
        write_json(root / 'data/reports' / source.name, read(candidate, 'data/reports/' + source.name))


def run(*, root=None, deadline_seconds=DEADLINE_SECONDS, executor=None, **options):
    root = Path(root or ROOT).resolve(); started = now(); start = time.monotonic()
    deadline = start + deadline_seconds; reserve = min(60, deadline_seconds / 10)
    previous = read(root, 'data/ops/health.json', {})
    manifest = read(root, 'public/api/v1/manifest.json', {})
    attempts = []; last = {}; candidate = None; executor = executor or execute_candidate
    staging = root / 'data/staging'; staging.mkdir(parents=True, exist_ok=True)
    write_json(root / 'data/reports/production_sync.json', {'result': 'RUNNING', 'started_at': started, 'last_good_dataset_version': manifest.get('dataset_version')})
    try:
        with tempfile.TemporaryDirectory(prefix='unattended-', dir=staging) as folder:
            for attempt in range(1, 3):
                candidate = Path(folder) / str(attempt)
                if time.monotonic() >= deadline - reserve: raise TimeoutError()
                clone_inputs(root, candidate)
                remaining = deadline - reserve - time.monotonic()
                if remaining <= 0: raise TimeoutError()
                print(f'[unattended_sync] attempt {attempt}/2; maximum remaining worker time {remaining:.0f}s', file=sys.stderr, flush=True)
                last = executor(candidate, options, remaining)
                attempts.append({'attempt': attempt, 'result': last.get('result'), 'error_summary': last.get('error_summary', {}),
                                 'metrics': {key: last[key] for key in ('api_request_count', 'public_page_request_count', 'retry_count', 'api_response_seconds', 'public_page_response_seconds', 'transport_error_summary') if key in last}})
                # Keep failure diagnostics outside legal/public state. These are
                # sanitized reports, never raw HTTP URLs or credentialed bodies.
                attempt_dir = root / 'data/reports/production_attempts' / started[:19].replace(':', '').replace('-', '') / str(attempt)
                write_json(attempt_dir / 'production_sync.json', last)
                for name in ('core_resolution.json', 'discovery_scan.json'):
                    value = read(candidate, 'data/reports/' + name)
                    if value is not None: write_json(attempt_dir / name, value)
                if last.get('result') in ('PUBLISHED', 'NO_CHANGE'):
                    promote(root, candidate, last, deadline)
                    try: retain_operations(root, candidate, last)
                    except Exception: last['operations_retention_error'] = 'OPS_REPORT_RETENTION_FAILED'
                    break
                if attempt == 2 or not retryable(last, candidate): break
                if deadline - reserve - time.monotonic() <= RETRY_DELAY_SECONDS: raise TimeoutError()
                time.sleep(RETRY_DELAY_SECONDS)
            else: raise ValueError('SYNC_WORKER_FAILED')
    except TimeoutError:
        last = {'result': 'BLOCKED', 'error_summary': {'code': 'SYNC_DEADLINE_EXCEEDED'}}
    except Exception:
        last = {'result': 'BLOCKED', 'error_summary': {'code': 'SYNC_SUPERVISOR_FAILED'}}
    if last.get('result') not in ('PUBLISHED', 'NO_CHANGE'):
        # Preserve verified health/data identity and mark only private ops failed.
        last.update({'result': 'BLOCKED', 'dataset_version': manifest.get('dataset_version'), 'last_good_dataset_version': manifest.get('dataset_version'), 'new_events': 0, 'persistent_new_events': 0, 'public_rewritten': False})
        ops = {**previous, 'last_attempt': started, 'publication_status': 'BLOCKED', 'api_status': last.get('error_summary', {}).get('code', 'SYNC_FAILED')}
        write_json(root / 'data/ops/health.json', ops)
    report = {**last, 'started_at': started, 'finished_at': now(), 'duration_seconds': round(time.monotonic() - start, 6),
              'whole_sync_deadline_seconds': deadline_seconds, 'whole_sync_attempts': attempts, 'whole_sync_retry_count': max(0, len(attempts) - 1)}
    # Never conceal the cost/errors of a failed first attempt. A killed worker
    # may have incomplete telemetry, which must be explicit instead of zero.
    known = all('api_request_count' in a['metrics'] for a in attempts) and bool(attempts)
    report['request_metrics_complete'] = known
    if known:
        for key in ('api_request_count', 'public_page_request_count', 'retry_count', 'api_response_seconds', 'public_page_response_seconds'):
            report[key] = round(sum(a['metrics'].get(key, 0) for a in attempts), 6)
        report['total_http_request_count'] = report['api_request_count'] + report['public_page_request_count']
        report['average_api_response_seconds'] = round(report['api_response_seconds'] / report['api_request_count'], 6) if report['api_request_count'] else None
        errors = Counter()
        for attempt in attempts: errors.update(attempt['metrics'].get('transport_error_summary', {}))
        report['transport_error_summary'] = dict(errors)
    try: report['ops_status_updated'] = publish_status(root, report)
    except Exception:
        report['ops_status_updated'] = False
        report['result'] = 'BLOCKED'
        report['error_summary'] = {'code':'OPS_STATUS_PUBLICATION_FAILED'}
    write_json(root / 'data/reports/production_sync.json', report)
    return report
