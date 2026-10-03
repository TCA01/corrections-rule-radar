import { describe, it, expect } from 'vitest';
import {
  calculateDDay,
  formatDotDate,
  formatDateTime,
  isSameDay,
  isWithinNextDays,
  isWithinPastDays,
  isFutureDate,
} from '../utils/date';
import { displayArticleDiffs, computeWordDiff, tokenizeLegalText } from '../utils/diff';
import {
  getChangeTypeLabel,
  getFactualDescription,
  getStatusBadge,
  getClassificationBadge,
  getScopeClassLabel,
  isRemovedAppendix,
} from '../utils/format';


describe('Date & D-Day Utilities', () => {
  const refDate = new Date('2026-10-03T00:00:00+09:00'); // 2026-10-03

  it('calculates D-Day correctly for today', () => {
    const res = calculateDDay('2026-10-03', refDate);
    expect(res.dDay).toBe(0);
    expect(res.label).toBe('D-DAY');
  });

  it('calculates D-Day correctly for future dates', () => {
    const d3 = calculateDDay('2026-10-06', refDate);
    expect(d3.dDay).toBe(3);
    expect(d3.label).toBe('D-3');

    const d82 = calculateDDay('2026-12-24', refDate);
    expect(d82.dDay).toBe(82);
    expect(d82.label).toBe('D-82');
  });

  it('calculates D-Day correctly for past dates', () => {
    const past = calculateDDay('2026-10-01', refDate);
    expect(past.dDay).toBe(-2);
    expect(past.label).toBe('D+2');
  });

  it('formats dates into dot format YYYY.MM.DD', () => {
    expect(formatDotDate('2026-10-03')).toBe('2026.10.03');
    expect(formatDotDate(null)).toBe('-');
  });

  it('formats ISO timestamps into YYYY.MM.DD HH:mm', () => {
    const formatted = formatDateTime('2026-10-03T02:55:26.652223+00:00');
    expect(formatted).toMatch(/^2026\.10\.03 \d{2}:\d{2}$/);
    expect(formatDateTime(null)).toBe('-');
  });

  it('checks day equality and future/past ranges', () => {
    expect(isSameDay('2026-10-03', refDate)).toBe(true);
    expect(isSameDay('2026-10-04', refDate)).toBe(false);

    expect(isFutureDate('2026-10-04', refDate)).toBe(true);
    expect(isFutureDate('2026-10-02', refDate)).toBe(false);

    expect(isWithinPastDays('2026-10-01', 30, refDate)).toBe(true);
    expect(isWithinPastDays('2026-08-01', 30, refDate)).toBe(false);

    expect(isWithinNextDays('2026-10-20', 30, refDate)).toBe(true);
    expect(isWithinNextDays('2026-12-24', 30, refDate)).toBe(false);
    expect(isWithinNextDays('2026-12-24', 90, refDate)).toBe(true);
  });
});

describe('Backend diff presentation', () => {
  it('preserves canonical backend text and order even without raw bodies', () => {
    const result = displayArticleDiffs([
      { article_key: 'backend-key', article_number: '5의2', article_title: '제5조의2(기본계획)',
        change_type: 'MODIFIED', before_text: '종전', after_text: '개정', effective_date: '2026-12-24' },
      { article_key: 'added', article_number: '3', article_title: '제3조',
        change_type: 'ADDED', before_text: null, after_text: '신설', effective_date: '2026-12-24' },
    ]);
    expect(result.map(a => a.article_key)).toEqual(['backend-key', 'added']);
    expect(result[0].title).toBe('제5조의2(기본계획)');
    expect(result[0].before_text).toBe('종전');
    expect(result[1].is_new).toBe(true);
    expect(displayArticleDiffs()).toEqual([]);
  });
});

describe('Seoul timezone contract', () => {
  it.each([
    ['2026-10-02T23:59:00+09:00', 1],
    ['2026-10-03T00:00:00+09:00', 0],
    ['2026-10-02T14:59:00Z', 1],
    ['2026-10-02T15:00:00Z', 0],
    ['2026-10-03T00:00:00Z', 0],
    ['2026-10-03T15:00:00Z', -1],
  ])('uses Seoul civil day at %s', (instant, expected) => {
    expect(calculateDDay('2026-10-03', new Date(instant)).dDay).toBe(expected);
  });
  it('rejects impossible dates and timestamp effective dates', () => {
    expect(calculateDDay('2026-02-30').dDay).toBeNull();
    expect(calculateDDay('2026-10-03T00:00:00Z').dDay).toBeNull();
  });
  it('formats a timestamp consistently in Seoul', () => {
    expect(formatDateTime('2026-10-02T15:00:00Z')).toBe('2026.10.03 00:00');
    expect(formatDotDate('2026-10-03')).toBe('2026.10.03');
  });
});

describe('Format & Badge Utilities', () => {
  it('formats change type labels factually without legal advice', () => {
    expect(getChangeTypeLabel('FUTURE_EFFECTIVE_VERSION')).toBe('시행 예정');
    expect(getChangeTypeLabel('RULE_AMENDED')).toBe('규정 개정');
    expect(getChangeTypeLabel('ARTICLE_CHANGED')).toBe('조문 변경');
    expect(getChangeTypeLabel('RULE_REPEALED')).toBe('규정 폐지');

    const desc = getFactualDescription('FUTURE_EFFECTIVE_VERSION', '2026-12-24');
    expect(desc).toContain('2026-12-24 시행 예정');
    expect(desc).not.toContain('해야 합니다');
  });

  it('returns appropriate status badges', () => {
    expect(getStatusBadge('CURRENT').text).toBe('현행');
    expect(getStatusBadge('REPEALED').text).toBe('폐지');

    expect(getClassificationBadge('REVIEWED', ['의료']).text).toBe('의료');
    expect(getClassificationBadge('REVIEWED', ['의료', '보고']).text).toBe('의료, 보고');
    expect(getClassificationBadge('REVIEWED', []).text).toBe('기타');
  });

  it('returns human-friendly Korean labels for scope classes', () => {
    expect(getScopeClassLabel('OFFICIAL_CORRECTIONS_LIST')).toBe('교정본부 공식 목록');
    expect(getScopeClassLabel('DIRECT_CORRECTIONS')).toBe('교정 직접 관련');
    expect(getScopeClassLabel('CROSS_DOMAIN_CORRECTIONS')).toBe('공통 적용 규정');
    expect(getScopeClassLabel('HISTORICAL_REPEALED')).toBe('폐지·연혁 규정');
    expect(getScopeClassLabel(undefined)).toBeNull();
  });
});

describe('Korean Legal Word Diff & Tokenization', () => {
  it('tokenizes Korean legal phrases preserving article numbers and atomic words', () => {
    const tokens = tokenizeLegalText('제53조의2(태아의 보호 등) 수용자가 임신한 경우');
    expect(tokens).toEqual([
      '제53조의2',
      '(',
      '태아의',
      ' ',
      '보호',
      ' ',
      '등',
      ')',
      ' ',
      '수용자가',
      ' ',
      '임신한',
      ' ',
      '경우',
    ]);
  });

  it('computes word/phrase diff without single-character fragmentation', () => {
    const before = '수용자에게 1일 3회 식사를 지급한다.';
    const after = '수용자에게 1일 3회 균형잡힌 식사를 지급한다.';

    const chunks = computeWordDiff(before, after);
    expect(chunks).toEqual([
      { type: 'unchanged', text: '수용자에게 1일 3회' },
      { type: 'added', text: ' 균형잡힌' },
      { type: 'unchanged', text: ' 식사를 지급한다.' },
    ]);
  });

  it('correctly detects pure deletion, pure addition, and unchanged text', () => {
    // Pure addition (e.g., new article)
    expect(computeWordDiff(null, '신설 조문 내용')).toEqual([
      { type: 'added', text: '신설 조문 내용' },
    ]);

    // Pure deletion (e.g., deleted article)
    expect(computeWordDiff('삭제된 조문 내용', null)).toEqual([
      { type: 'deleted', text: '삭제된 조문 내용' },
    ]);

    // Unchanged
    expect(computeWordDiff('동일한 규정 본문', '동일한 규정 본문')).toEqual([
      { type: 'unchanged', text: '동일한 규정 본문' },
    ]);

    // Empty
    expect(computeWordDiff(null, null)).toEqual([]);
  });

  it('handles word replacement cleanly', () => {
    const before = '소장은 매월 1회 점검하여야 한다.';
    const after = '소장은 분기별 1회 점검하여야 한다.';

    const chunks = computeWordDiff(before, after);
    expect(chunks).toEqual([
      { type: 'unchanged', text: '소장은 ' },
      { type: 'deleted', text: '매월' },
      { type: 'added', text: '분기별' },
      { type: 'unchanged', text: ' 1회 점검하여야 한다.' },
    ]);
  });
});

describe('isRemovedAppendix Predicate', () => {
  it('returns false for null or undefined input', () => {
    expect(isRemovedAppendix(null)).toBe(false);
    expect(isRemovedAppendix(undefined)).toBe(false);
  });

  it('detects is_deleted === true flag', () => {
    expect(isRemovedAppendix({ is_deleted: true, title: '어떤 서식' })).toBe(true);
  });

  it('detects removed/deleted statuses regardless of casing', () => {
    expect(isRemovedAppendix({ status: 'REMOVED', title: '양식' })).toBe(true);
    expect(isRemovedAppendix({ status: 'removed', title: '양식' })).toBe(true);
    expect(isRemovedAppendix({ status: 'DELETED', title: '양식' })).toBe(true);
    expect(isRemovedAppendix({ status: '삭제', title: '양식' })).toBe(true);
    expect(isRemovedAppendix({ status: 'APPENDIX_REMOVED', title: '양식' })).toBe(true);
  });

  it('detects change_type of appendix removal', () => {
    expect(isRemovedAppendix({ change_type: 'APPENDIX_REMOVED', title: '양식' })).toBe(true);
    expect(isRemovedAppendix({ change_type: 'DELETED', title: '양식' })).toBe(true);
  });

  it('detects Law.go.kr deleted titles with various delimiters', () => {
    expect(isRemovedAppendix({ title: '삭제' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제 <2016.1.22.>' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제 &lt;2016.1.22.&gt;' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제<2016.1.22.>' })).toBe(true);
    expect(isRemovedAppendix({ title: '[삭제]' })).toBe(true);
    expect(isRemovedAppendix({ title: '(삭제)' })).toBe(true);
    expect(isRemovedAppendix({ title: '[삭제 2016.1.22.]' })).toBe(true);
    expect(isRemovedAppendix({ title: '(삭제 2016.1.22.)' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제(2016.1.22.)' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제[2016.1.22.]' })).toBe(true);
    expect(isRemovedAppendix({ title: '삭제&lt;2016.1.22.&gt;' })).toBe(true);
  });

  it('returns false for active non-deleted items even with similar words', () => {
    expect(
      isRemovedAppendix({
        title: '수형자 분류처우심사표',
        status: 'AVAILABLE',
        url: 'https://www.law.go.kr/LSW/flDownload.do?flSeq=149617249',
      })
    ).toBe(false);
    expect(
      isRemovedAppendix({
        title: '작업폐지 보고서',
        url: 'https://www.law.go.kr/LSW/flDownload.do?flSeq=123',
      })
    ).toBe(false);
    expect(
      isRemovedAppendix({
        title: '분류심사 제외 및 유예사유 소멸된 자의 분류심사',
        url: 'https://www.law.go.kr/LSW/flDownload.do?flSeq=124',
      })
    ).toBe(false);
  });
});

