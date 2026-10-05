import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import { api } from '../services/api';
import { resolveVisualComparison, structuredArticles } from '../services/comparison';
import { decodeDisplayText } from '../utils/text';
import { computeWordDiff } from '../utils/diff';
import { RuleDetailModal } from '../components/RuleDetailModal';
import { PersistentChangeEvent, RuleDetailResponse } from '../types';

const root = path.resolve(__dirname, '../../..');
const read = (file: string) => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const fixture = read('tests/fixtures/phase1i_education14.json');
const detail: RuleDetailResponse = read('public/api/v1/rules/admrul-37584.json');
const event: PersistentChangeEvent = read('public/api/v1/changes/history.json').events.find((e: PersistentChangeEvent) => e.event_id === fixture.event_id);
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('Phase 1I official comparison source', () => {
  it('uses the exact historical bodies for article 14, keeping both substantive changes and literal deletion', () => {
    const value = resolveVisualComparison(event, fixture.before_snapshot, fixture.after_snapshot);
    const article = value.articles.find(a => a.article_number === '14')!;
    expect(article.before_text).toBe(fixture.before_article.text);
    expect(article.after_text).toBe(fixture.after_article.text);
    const chunks = computeWordDiff(article.before_text, article.after_text);
    expect(chunks.filter(c => c.type === 'deleted').map(c => c.text).join('')).toContain('형기주기별');
    expect(chunks.filter(c => c.type === 'deleted').map(c => c.text).join('')).toContain('심리치료프로그램');
    expect(article.after_text).toContain('4. 삭제5. 삭제');
    expect(chunks.some(c => /생\s*략|현행과 같음/.test(c.text))).toBe(false);
  });
  it('suppresses unchanged structured articles and never strips literal 생략', () => {
    const before = structuredClone(fixture.before_snapshot);
    const after = structuredClone(fixture.after_snapshot);
    before.body.articles = ['제14조(교육면제) 생략 절차. 5. 삭제'];
    after.body.articles = ['제14조(교육면제) 생략 절차. 5. 삭제'];
    const only = { ...event, changed_articles: [fixture.official_article] };
    expect(resolveVisualComparison(only, before, after).articles).toEqual([]);
    after.body.articles = ['제14조(교육면제) 생략 신청 절차. 5. 삭제'];
    const value = resolveVisualComparison(only, before, after).articles[0];
    expect(value.before_text).toContain('생략'); expect(value.after_text).toContain('5. 삭제');
  });
  it('rejects a wrong effective state even if the promulgated version ID is equal', () => {
    const wrong = structuredClone(fixture.after_snapshot); wrong.metadata.effective_date = '2027-02-05';
    expect(() => resolveVisualComparison(event, fixture.before_snapshot, wrong)).toThrow('PAIR_MISMATCH');
  });
  it('groups nested singleton law paragraphs and admin continuation text deterministically', () => {
    expect(structuredArticles({ articles: { 조문단위: { 조문내용: '제1조(범위)', 항: { 항내용: '① 생략', 호: { 호내용: '1. 삭제' } } } } }).get('1')?.text).toBe('제1조(범위)\n① 생략\n1. 삭제');
    expect(structuredArticles({ articles: ['제1조(범위)', '본문', '제2장 제목', '편제 설명'] }).get('1')?.text).toBe('제1조(범위)\n본문');
  });
  it('fails closed when either snapshot cannot be loaded', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')));
    expect(await api.getVisualComparison(event)).toEqual({ articles: [], textSource: 'UNAVAILABLE' });
  });
  it('loads only the two explicit snapshot references and retains original event text', async () => {
    const original = JSON.stringify(event);
    const fetcher = vi.fn().mockImplementation(async (url: string) => ({ ok: true, json: async () => ({ version: url === fixture.before_reference.snapshot_url ? fixture.before_snapshot : fixture.after_snapshot }) }));
    vi.stubGlobal('fetch', fetcher);
    expect((await api.getVisualComparison(event)).textSource).toBe('STRUCTURED_SNAPSHOT');
    expect(fetcher.mock.calls.map(c => c[0])).toEqual([fixture.before_reference.snapshot_url, fixture.after_reference.snapshot_url]);
    expect(JSON.stringify(event)).toBe(original);
  });
  it('renders the real article 14 changes with no red/green comparison placeholders', async () => {
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(detail);
    vi.spyOn(api, 'getVisualComparison').mockResolvedValue(resolveVisualComparison(event, fixture.before_snapshot, fixture.after_snapshot));
    render(<RuleDetailModal rule={detail.rule} initialEvent={event} onClose={vi.fn()} />);
    await screen.findByText(/문구 비교: 해당 개정/);
    const card = Array.from(screen.getByRole('dialog').querySelectorAll('.diff-article-card')).find(el => el.textContent?.includes('제14조(교육면제)'))!;
    expect(card.querySelectorAll('del').length).toBeGreaterThan(0);
    expect(card.textContent).toContain('5. 삭제');
    expect(card.textContent).not.toMatch(/생\s*략|현행과 같음/);
  });
});

describe('Phase 1I appendix display', () => {
  it.each([['&lt;', '<'], ['&gt;', '>'], ['&amp;', '&'], ['&quot;', '"'], ['&amp;lt;', '&lt;']])('decodes %s once as plain text', (input, output) => {
    expect(decodeDisplayText(input)).toBe(output);
  });
  it('renders the official deleted title safely with no download or preview', async () => {
    const value = structuredClone(detail);
    value.current.appendices = [{ sequence: '1', branch: '', type: '서식', title: '삭제 &lt;2016.1.22.&gt;', status: 'REMOVED', url: 'https://www.law.go.kr/flDownload.do', pdf_url: null }];
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(value);
    render(<RuleDetailModal rule={value.rule} onClose={vi.fn()} />);
    await screen.findByText('삭제 <2016.1.22.>');
    const item = screen.getByText('해당 개정에서 삭제된 서식').closest('.appendix-item')!;
    expect(item.querySelector('a')).toBeNull();
    expect(value.current.appendices[0].title).toBe('삭제 &lt;2016.1.22.&gt;');
  });
  it('renders decoded markup as literal text, never as an HTML element', async () => {
    const value = structuredClone(detail);
    value.current.appendices = [{ sequence: '1', branch: '', type: '서식', title: '&lt;img src=x onerror=alert(1)&gt;', status: 'REMOVED', url: null, pdf_url: null }];
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(value);
    render(<RuleDetailModal rule={value.rule} onClose={vi.fn()} />);
    const text = await screen.findByText('<img src=x onerror=alert(1)>');
    expect(text.querySelector('img')).toBeNull();
  });
  it('shows snapshot unavailability instead of a false no-change claim or excerpt word diff', async () => {
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(detail);
    vi.spyOn(api, 'getVisualComparison').mockResolvedValue({ articles: [], textSource: 'UNAVAILABLE' });
    render(<RuleDetailModal rule={detail.rule} initialEvent={event} onClose={vi.fn()} />);
    await screen.findByText(/공식 전체 본문을 불러오지 못해/);
    await waitFor(() => expect(screen.getByRole('dialog').querySelector('del')).toBeNull());
  });
});
