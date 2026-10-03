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
import { displayArticleDiffs } from '../utils/diff';
import {
  getChangeTypeLabel,
  getFactualDescription,
  getStatusBadge,
  getClassificationBadge,
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
    expect(getStatusBadge('REVIEW').text).toBe('검토 중');

    expect(getClassificationBadge('REVIEW', []).text).toBe('업무 분야 검토 중');
    expect(getClassificationBadge('REVIEWED', ['의료']).text).toBe('의료');
  });
});
