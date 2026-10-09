"""Cross-check the final report against retained run and legal-state evidence."""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.snapshot import write_json

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'data/reports'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    report = read(REPORTS / 'phase1m_final.json')
    history = read(REPORTS / 'phase1m_run_history.json')
    live = read(REPORTS / 'phase1m_live.json')
    preservation = read(REPORTS / 'phase1m_preservation.json')
    markdown = (REPORTS / 'phase1m_final.md').read_text(encoding='utf8')
    by_id = {r['id']: r for r in report['runs']}
    manuals = [by_id[i] for i in report['manual_rehearsals_completed']]
    repeated = [by_id[i] for i in report['no_change_verified_run_ids']]
    checks = {
        'all_actions_runs_included': history['all_runs_captured'] and set(by_id) == {r['id'] for r in history['runs']},
        'five_requested_slots_included': len(report['slots']) == 5,
        'slot_matches_actual_schedule_event': all(not slot['run_existed'] or (
            by_id[slot['run_id']]['event'] == 'schedule'
            and by_id[slot['run_id']]['expected_slot_kst'].startswith(slot['slot_kst'])
        ) for slot in report['slots']),
        'morning_and_evening_rehearsals_are_manual': {r['sync']['schedule_test_mode'] for r in manuals} == {'morning', 'evening'}
            and all(r['event'] == 'workflow_dispatch' and r['sync']['trigger'] == 'MANUAL' for r in manuals),
        'both_rehearsals_passed_all_release_gates': all(r['deployment_completed'] and r['verification']['passed']
            and r['verification']['tests'] >= 172 and r['verification']['secret_scan']['file_count'] == 0 for r in manuals),
        'no_change_kept_events_hashes_bytes_and_mtimes': bool(repeated) and all(
            r['sync']['event_ids_identical'] and r['sync']['snapshot_hashes_identical']
            and r['sync']['public_bytes_and_mtimes_identical'] and not r['sync']['public_rewritten'] for r in repeated),
        'repository_and_live_dataset_agree': live['dataset_version'] == read(ROOT / 'public/api/v1/manifest.json')['dataset_version'],
        'official_107_scope_and_repeal_verified': live['tracked'] == 107 and live['counts'] == {'CURRENT': 104, 'REPEALED': 3}
            and live['official_repeal_body_matches'],
        'scheduled_freshness_kept_independently': live['ops']['trigger'] == 'MANUAL'
            and live['ops']['last_scheduled_scan']['github_run_id'] == '37503211648'
            and live['last_scheduled_run_event_verified'] == 'schedule',
        'immutable_and_future_data_preserved': preservation['status'] == 'PASS'
            and preservation['changed_current_rule_ids'] == ['admrul-35611'],
        'markdown_matches_ready_decision': ('READY FOR UNATTENDED TWICE-DAILY OPERATION: ' +
            ('YES' if report['ready_for_unattended_twice_daily_operation'] else 'NO')) in markdown,
        'manual_tests_cannot_substitute_for_real_schedule_acceptance': not report['ready_for_unattended_twice_daily_operation']
            or report['next_real_scheduled_success_verified'],
        'utc_to_kst_origin_correct': datetime.fromisoformat(report['ui_origin']['completed_utc'])
            .replace(tzinfo=None) + timedelta(hours=9) == datetime.fromisoformat(report['ui_origin']['completed_kst'])
            + timedelta(microseconds=209233),
    }
    value = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
             'audit_cutoff_utc': report['as_of'], 'run_count': len(by_id)}
    write_json(REPORTS / 'phase1m_report_consistency.json', value)
    print(json.dumps(value))
    assert value['status'] == 'PASS'


if __name__ == '__main__':
    main()
