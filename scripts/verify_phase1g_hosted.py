"""Bounded, unauthenticated verification of the approved Phase 1G release."""
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://corrections-rule-radar.web.app'


def run():
    checked = []

    def public(path):
        local = ROOT / ('public' + path)
        request = urllib.request.Request(BASE + path, headers={'Cache-Control': 'no-cache', 'Accept': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
        assert raw == local.read_bytes(), 'HOSTED_BYTES_MISMATCH: ' + path
        checked.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest()})
        return json.loads(raw)

    manifest = public('/api/v1/manifest.json')
    health = public('/api/v1/health.json')
    rules = public('/api/v1/rules.json')['rules']
    detail = public('/api/v1/rules/law-001671.json')
    history = public('/api/v1/changes/history.json')['events']
    recent = public('/api/v1/changes/recent.json')['events']
    public('/api/v1/changes/upcoming.json')
    assert manifest['schema_version'] == '1.4' and manifest['rule_count'] == 107
    assert health['rule_count'] == 107 and health['dataset_version'] == manifest['dataset_version']
    assert len(rules) == 107 and sum(r['status'] == 'CURRENT' for r in rules) == 105
    assert sum(r['status'] == 'REPEALED' for r in rules) == 2
    matches = [r for r in rules if r['canonical_id'] == 'law-001671']
    assert len(matches) == 1
    rule = matches[0]
    assert rule['current_name'] == '형사소송법' and rule['version_id'] == '290189'
    assert rule['metadata']['effective_date'] == '2026-10-02'
    assert rule['primary_domain'] == '수용·보안'
    assert rule['provenance']['scope_class'] == 'CROSS_DOMAIN_CORRECTIONS'
    assert detail['current']['body'] and len(detail['upcoming']) == 3
    events = [e for e in history if e['canonical_id'] == 'law-001671']
    recent_events = [e for e in recent if e['canonical_id'] == 'law-001671']
    assert len(events) == 32 and len(recent_events) == 2
    assert sorted(e['changed_article_count'] for e in recent_events) == [0, 93]
    for event in recent_events:
        public('/api/v1/changes/' + event['event_id'] + '.json')
        for ref in ('before_version', 'after_version'):
            public(event[ref]['snapshot_url'])
    with urllib.request.urlopen(rule['official_source_url'], timeout=30) as response:
        assert response.status == 200
        official_status = response.status
    report_path = ROOT / 'data/reports/phase1g_hosted.json'
    previous = json.loads(report_path.read_text(encoding='utf8')) if report_path.exists() else {}
    report = {'status': 'PASS', 'checked_at': datetime.now(timezone.utc).isoformat(),
              'url': BASE, 'dataset_version': manifest['dataset_version'], 'live_schema': '1.4',
              'live_rule_count': 107, 'current': 105, 'historical': 2,
              'live_law': 'PASS', 'live_history': 'PASS', 'history_events': 32,
              'recent_events': 2, 'recent_article_counts': [0, 93],
              'official_source_http_status': official_status, 'checked_public_files': checked,
              'ui_status': previous.get('ui_status', 'PENDING'),
              'ui_checks': previous.get('ui_checks', [])}
    write_json(report_path, report)
    print(json.dumps({k: v for k, v in report.items() if k != 'checked_public_files'}))


if __name__ == '__main__':
    run()
