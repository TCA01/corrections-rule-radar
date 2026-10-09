"""Check live statuses against structured official evidence, not release counts."""
from pipeline.operations.calendar import seoul_date

def assert_status_evidence(test, collection):
    for row in collection['registry']:
        sn = collection['snapshots'][row['canonical_id']]
        meta = sn['metadata']
        test.assertEqual(sn['canonical_id'], row['canonical_id'])
        test.assertEqual(sn['version_id'], row['version_id'])
        test.assertLessEqual(meta['effective_date'], seoul_date().isoformat())
        repealed = meta['amendment_type'] in ('폐지', '타법폐지')
        test.assertEqual(row['status'], 'REPEALED' if repealed else 'CURRENT')
        if repealed:
            evidence = sn['repeal_evidence']
            test.assertEqual(evidence['source'], 'OFFICIAL_HISTORY')
            test.assertEqual(evidence['canonical_id'], sn['canonical_id'])
            test.assertEqual(evidence['version_id'], sn['version_id'])
            test.assertEqual(evidence['amendment_type'], meta['amendment_type'])
            test.assertTrue(evidence['history_evidence'])
            test.assertEqual(row['provenance']['scope_class'], 'HISTORICAL_REPEALED')
        elif sn['source_kind'] == 'admrul' and meta['official_state'] != 'Y':
            # A LID can expose a future Y state; today's exact-ID predecessor
            # is confirmed separately by the collector's structured history.
            future = collection['future'].get(sn['canonical_id'], [])
            test.assertTrue(any(s['metadata']['official_state']=='Y' and s['metadata']['effective_date']>seoul_date().isoformat() for s in future))
