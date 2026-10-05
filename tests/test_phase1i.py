import json
import unittest
from pathlib import Path
from pipeline.diff.history import article_groups, article_diff

ROOT = Path(__file__).resolve().parents[1]


class Phase1IAuditTests(unittest.TestCase):
    def test_exact_official_snapshot_evidence_and_substantive_change(self):
        fixture = json.loads((ROOT / 'tests/fixtures/phase1i_education14.json').read_text(encoding='utf-8'))
        groups = []
        for side in ('before', 'after'):
            snapshot = fixture[side + '_snapshot']
            stored = json.loads((ROOT / ('public' + fixture[side + '_reference']['snapshot_url'])).read_text(encoding='utf-8'))['version']
            self.assertEqual(snapshot, stored)
            group = article_groups(snapshot['body'])
            self.assertEqual(group['14'], fixture[side + '_article'])
            self.assertNotIn('현행과 같음', group['14']['text'])
            self.assertNotIn('생  략', group['14']['text'])
            groups.append(group)
        change = next(a for a in article_diff(*groups, '2026-10-02') if a['article_number'] == '14')
        self.assertIn('4. 심리치료프로그램', change['before_text'])
        self.assertIn('4. 삭제5. 삭제', change['after_text'])
        self.assertIn('형기주기별 재교육', change['before_text'])
        self.assertNotIn('형기주기별', change['after_text'])

    def test_literal_legal_words_are_not_placeholder_normalized(self):
        before = article_groups({'articles': ['제14조(교육면제) 생략 절차. 5. 삭제']})
        after = article_groups({'articles': ['제14조(교육면제) 생략 신청 절차. 5. 삭제']})
        diff = article_diff(before, after, '2026-10-02')[0]
        self.assertIn('생략', diff['before_text'])
        self.assertIn('5. 삭제', diff['after_text'])
