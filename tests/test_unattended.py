"""Bounded transport and isolated fail-closed production recovery."""
import json
import os
import shutil
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from pipeline.law_api.client import ApiError, LawClient, bounded_request
from pipeline.snapshot import write_json
from scripts import unattended_sync as supervisor
from tests.test_pipeline import Opener, Response, SECRET

ROOT = Path(__file__).resolve().parents[1]
GOOD = b'{"LawSearch":{"totalCnt":0}}'


class RequestBounds(unittest.TestCase):
    def request(self, responses):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'LAW_API_OC': SECRET}), patch('time.sleep') as sleep:
            opener = Opener(responses)
            client = LawClient(opener=opener, interval=0, retries=2, cache=tmp)
            try:
                client.fetch(target='law')
            except ApiError as error:
                return opener.count, sleep.call_args_list, error.code, list(Path(tmp).iterdir())
            return opener.count, sleep.call_args_list, None, list(Path(tmp).iterdir())

    def test_timeout_then_success(self):
        count, waits, error, cache = self.request([socket.timeout(), GOOD])
        self.assertEqual((count, error, len(cache)), (2, None, 1))
        self.assertEqual([c.args for c in waits], [(1,)])

    def test_repeated_timeout_is_three_attempts_no_cache(self):
        count, waits, error, cache = self.request([socket.timeout()] * 3)
        self.assertEqual((count, error, cache), (3, 'TIMEOUT', []))
        self.assertEqual([c.args for c in waits], [(1,), (2,)])

    def test_http500_and_429_then_success(self):
        for status in (500, 429):
            with self.subTest(status=status):
                failure = urllib.error.HTTPError('https://example', status, 'fail', {}, None)
                self.assertEqual(self.request([failure, GOOD])[:3:2], (2, None))

    def test_http400_is_not_retried(self):
        failure = urllib.error.HTTPError('https://example', 400, 'fail', {}, None)
        self.assertEqual(self.request([failure])[:3], (1, [], 'HTTP_ERROR'))

    def test_connection_reset_then_success(self):
        self.assertEqual(self.request([ConnectionResetError(), GOOD])[:3:2], (2, None))

    def test_entire_open_and_body_read_bound_not_just_socket(self):
        # A transport that ignores its socket timeout must still return promptly.
        for hang_in_read in (False, True):
            release = threading.Event()
            class HangingResponse(Response):
                def read(self, limit=None):
                    release.wait(3)
                    return GOOD
            class HangingOpener:
                def open(self, *args, **kwargs):
                    if not hang_in_read: release.wait(3)
                    return HangingResponse(GOOD)
            started = time.monotonic()
            try:
                with self.assertRaisesRegex(ApiError, 'TIMEOUT'):
                    bounded_request(HangingOpener(), object(), .04)
                self.assertLess(time.monotonic() - started, .5)
            finally:
                release.set()


class IsolatedRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / 'public/api/v1', self.root / 'public/api/v1')
        shutil.copytree(ROOT / 'data/registry', self.root / 'data/registry')
        write_json(self.root / 'data/ops/health.json', {'last_successful_sync': 'LAST_GOOD', 'last_dataset_version': 'GOOD'})
        self.before = self.fingerprint()

    def tearDown(self):
        self.tmp.cleanup()

    def fingerprint(self):
        return {str(p.relative_to(self.root)): (p.read_bytes(), p.stat().st_mtime_ns)
                for rel in ('public/api/v1', 'data/registry', 'data/snapshots')
                for p in (self.root / rel).rglob('*.json')}

    def partial_failure(self, candidate, code='TIMEOUT', status=None):
        write_json(candidate / 'public/api/v1/health.json', {'INVALID_PARTIAL': True})
        write_json(candidate / 'data/registry/events.json', ['FAKE_EVENT'])
        write_json(candidate / 'data/snapshots/fake.json', {'partial': True})
        return {'result': 'BLOCKED', 'error_summary': {'code': code, 'http_status': status}}

    def no_change(self, candidate):
        write_json(candidate / 'data/ops/health.json', {'last_successful_sync': 'RESTORED', 'last_dataset_version': 'GOOD'})
        return {'result': 'NO_CHANGE', 'success_count': 107, 'error_summary': {}}

    def run_sync(self, executor):
        with patch.object(supervisor, 'RETRY_DELAY_SECONDS', 0):
            return supervisor.run(root=self.root, deadline_seconds=30, executor=executor)

    def test_success_failure_success_preserves_last_good_and_restores(self):
        self.assertEqual(self.run_sync(lambda c, o, t: self.no_change(c))['result'], 'NO_CHANGE')
        good = self.fingerprint()
        failed = self.run_sync(lambda c, o, t: self.partial_failure(c))
        self.assertEqual(failed['result'], 'BLOCKED')
        self.assertEqual(failed['whole_sync_retry_count'], 1)
        self.assertEqual(self.fingerprint(), good)
        self.assertEqual(supervisor.read(self.root, 'data/ops/health.json')['last_successful_sync'], 'RESTORED')
        self.assertEqual(self.run_sync(lambda c, o, t: self.no_change(c))['result'], 'NO_CHANGE')
        self.assertEqual(self.fingerprint(), good)

    def test_timeout_then_success_uses_fresh_candidate(self):
        def executor(candidate, options, timeout):
            return self.partial_failure(candidate) if candidate.name == '1' else self.no_change(candidate)
        report = self.run_sync(executor)
        self.assertEqual(report['result'], 'NO_CHANGE')
        self.assertEqual(report['whole_sync_retry_count'], 1)
        self.assertEqual(self.fingerprint(), self.before)

    def test_transient_http500_whole_retry(self):
        def executor(candidate, options, timeout):
            return self.partial_failure(candidate, 'HTTP_ERROR', 500) if candidate.name == '1' else self.no_change(candidate)
        report = self.run_sync(executor)
        self.assertEqual((report['result'], report['whole_sync_retry_count']), ('NO_CHANGE', 1))
        self.assertEqual(self.fingerprint(), self.before)

    def test_http400_no_whole_retry(self):
        report = self.run_sync(lambda c, o, t: self.partial_failure(c, 'HTTP_ERROR', 400))
        self.assertEqual((report['result'], report['whole_sync_retry_count']), ('BLOCKED', 0))
        self.assertEqual(self.fingerprint(), self.before)

    def test_no_change_content_drift_is_rejected(self):
        def executor(candidate, options, timeout):
            write_json(candidate / 'public/api/v1/health.json', {'BAD': True})
            return self.no_change(candidate)
        self.assertEqual(self.run_sync(executor)['result'], 'BLOCKED')
        self.assertEqual(self.fingerprint(), self.before)

    def test_no_change_does_not_promote_unpublished_snapshot_variation(self):
        def executor(candidate, options, timeout):
            write_json(candidate / 'data/snapshots/volatile-attachment.json', {'attachment_url': 'https://example/download?token=2'})
            return self.no_change(candidate)
        self.assertEqual(self.run_sync(executor)['result'], 'NO_CHANGE')
        self.assertEqual(self.fingerprint(), self.before)

    def test_hung_worker_is_killed_and_cannot_publish_partial_state(self):
        def executor(candidate, options, timeout):
            script = candidate / 'scripts/production_sync.py'
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("from pathlib import Path\nimport time\nPath('public/api/v1/health.json').write_text('{}')\nPath('data/registry/events.json').write_text('[1]')\nwhile True: time.sleep(1)\n", encoding='utf-8')
            return supervisor.execute_candidate(candidate, {}, .15)
        start = time.monotonic()
        report = self.run_sync(executor)
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(report['error_summary']['code'], 'SYNC_DEADLINE_EXCEEDED')
        self.assertEqual(report['whole_sync_retry_count'], 0)
        self.assertEqual(self.fingerprint(), self.before)

    def test_deadline_before_worker_does_not_change_live_data(self):
        report = supervisor.run(root=self.root, deadline_seconds=0, executor=lambda *args: self.fail('worker started'))
        self.assertEqual(report['error_summary']['code'], 'SYNC_DEADLINE_EXCEEDED')
        self.assertEqual(self.fingerprint(), self.before)

    def test_hanging_api_double_failure_exits_without_partial_publication(self):
        def executor(candidate, options, timeout):
            shutil.copytree(ROOT / 'pipeline', candidate / 'pipeline', ignore=shutil.ignore_patterns('__pycache__'))
            script = candidate / 'scripts/production_sync.py'
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text('''import sys, threading
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from pipeline.law_api.client import LawClient, ApiError
from pipeline.operations.metrics import Metrics
from pipeline.snapshot import write_json
from unittest.mock import patch
class Hang:
    def open(self, *args, **kwargs): threading.Event().wait()
Path('data/registry/events.json').write_text('["PARTIAL"]')
Path('public/api/v1/health.json').write_text('{}')
metrics = Metrics()
try:
    with patch('time.sleep'):
        LawClient(timeout=.03, retries=2, interval=0, opener=Hang(), metrics=metrics).fetch(target='law')
except ApiError as exc:
    write_json('data/reports/production_sync.json', {'result':'BLOCKED', 'error_summary':{'code':exc.code}, **metrics.report()})
    sys.exit(1)
sys.exit(0)
''', encoding='utf8')
            with patch.dict(os.environ, {'LAW_API_OC': SECRET}):
                return supervisor.execute_candidate(candidate, {}, timeout)
        report = self.run_sync(executor)
        self.assertEqual((report['result'], report['whole_sync_retry_count']), ('BLOCKED', 1))
        self.assertEqual(report['api_request_count'], 6)
        self.assertEqual(report['retry_count'], 4)
        self.assertEqual(report['transport_error_summary'], {'TIMEOUT': 6})
        self.assertTrue(report['request_metrics_complete'])
        self.assertEqual(self.fingerprint(), self.before)

    def test_promotion_deadline_rolls_back_state_and_public(self):
        candidate = self.root / 'candidate'
        supervisor.clone_inputs(self.root, candidate)
        write_json(candidate / 'data/registry/events.json', ['NEW'])
        write_json(candidate / 'data/snapshots/new.json', {'new': True})
        # Deadline expires just after public directory replacement.
        with patch.object(supervisor.time, 'monotonic', side_effect=[0, 0, 0, 0, 0, 11]):
            with self.assertRaises(TimeoutError):
                supervisor.promote(self.root, candidate, {'result': 'PUBLISHED'}, 10)
        # Rollback restores contents, preserving the public directory's mtimes.
        after = self.fingerprint()
        self.assertEqual({p: b[0] for p, b in after.items()}, {p: b[0] for p, b in self.before.items()})
        self.assertEqual(after, self.before)


if __name__ == '__main__':
    unittest.main()
