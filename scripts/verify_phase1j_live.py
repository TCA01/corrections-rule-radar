"""Read-only last-good hosting probe; never sends an API credential."""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.law_api.client import bounded_request
from pipeline.snapshot import write_json


def main():
    matches = {}
    for rel in ('manifest.json', 'health.json', 'rules.json', 'changes/history.json', 'changes/recent.json', 'rules/law-001671.json'):
        req = urllib.request.Request('https://corrections-rule-radar.web.app/api/v1/' + rel, headers={'Cache-Control': 'no-cache'})
        raw = bounded_request(urllib.request.build_opener(), req, 30)
        local = (ROOT / 'public/api/v1' / rel).read_bytes()
        matches[rel] = {'identical_bytes': raw == local, 'sha256': hashlib.sha256(raw).hexdigest()}
    health = json.loads((ROOT / 'public/api/v1/health.json').read_text(encoding='utf8'))
    manifest = json.loads((ROOT / 'public/api/v1/manifest.json').read_text(encoding='utf8'))
    report = {'status': 'PASS' if all(v['identical_bytes'] for v in matches.values()) else 'FAIL',
              'dataset_version': manifest['dataset_version'], 'health': health, 'matches': matches}
    write_json(ROOT / 'data/reports/phase1j_live_last_good.json', report)
    print(json.dumps({'status': report['status'], 'dataset_version': report['dataset_version'], 'files': len(matches)}))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    sys.exit(main())
