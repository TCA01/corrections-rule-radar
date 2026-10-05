"""Two real supervised runs; assert public/history/snapshot idempotency."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.snapshot import write_json
from scripts.observe import public_fingerprint, semantic_hashes


def baseline():
    def read(rel): return json.loads((ROOT / rel).read_text(encoding='utf8'))
    return {
        'public': public_fingerprint(ROOT),
        'snapshots': semantic_hashes(read('data/registry/state.json')),
        'event_ids': [e['event_id'] for e in read('data/registry/events.json')],
        'persistent_history': hashlib.sha256((ROOT / 'data/registry/change_history.json').read_bytes()).hexdigest(),
        'immutable_files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'data/snapshots').rglob('*.json')},
    }


def main():
    before = baseline(); results = []
    for number in (1, 2):
        completed = subprocess.run([sys.executable, 'scripts/production_sync.py'], cwd=ROOT, timeout=750, stdout=subprocess.DEVNULL)
        report = json.loads((ROOT / 'data/reports/production_sync.json').read_text(encoding='utf8'))
        stable = baseline() == before
        results.append({'run': number, 'exit_code': completed.returncode, 'all_public_mtimes_hashes_history_and_snapshots_identical': stable, 'report': report})
        write_json(ROOT / 'data/reports/phase1j_live_runs.json', {'runs': results, 'passed': all(r['exit_code'] == 0 and r['all_public_mtimes_hashes_history_and_snapshots_identical'] and r['report']['result'] == 'NO_CHANGE' for r in results)})
        print(f"run {number}: {report['result']}, {report['duration_seconds']}s; unchanged={stable}", flush=True)
        if completed.returncode or not stable or report['result'] != 'NO_CHANGE': return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
