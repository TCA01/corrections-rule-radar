import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import { RuleDetailModal } from '../components/RuleDetailModal';
import { api } from '../services/api';
import { RuleDetailResponse, PersistentChangeEvent } from '../types';
const root = path.resolve(__dirname, '../../../public/api/v1');
const detail: RuleDetailResponse = JSON.parse(fs.readFileSync(path.join(root, 'rules/law-001671.json'), 'utf8'));
const history: PersistentChangeEvent[] = JSON.parse(fs.readFileSync(path.join(root, 'changes/history.json'), 'utf8')).events;
afterEach(() => vi.restoreAllMocks());

describe('Phase 1H upcoming comparisons', () => {
  it.each([
    ['2027.02.05', '2026.10.02', 3, 3],
    ['2027.08.05', '2027.02.05', 2, 5],
    ['2027.12.31', '2027.08.05', 1, 6],
  ])('uses explicit backend baselines for %s and toggles cumulative mode', async (day, before, inc, cum) => {
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(detail);
    render(<RuleDetailModal rule={detail.rule} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText(/불러오는 중입니다/)).not.toBeInTheDocument());
    const modal = screen.getByRole('dialog');
    fireEvent.click(within(modal).getByRole('tab', { name: `시행 예정 ${day} 시행 예정` }));
    expect(within(modal).getByRole('button', { name: '직전 시행상태 대비' })).toHaveAttribute('aria-pressed', 'true');
    const strip = modal.querySelector('.diff-meta-strip')!;
    expect(strip.textContent).toContain(before); expect(strip.textContent).toContain(day); expect(strip.textContent).toContain(`${inc}개`);
    if (day === '2027.08.05') {
      expect(modal.querySelectorAll('.diff-article-card')).toHaveLength(2);
      expect(within(modal).getByRole('navigation', { name: '변경 조문 바로가기' }).textContent).toContain('제220조의2');
      expect(within(modal).getByRole('navigation', { name: '변경 조문 바로가기' }).textContent).toContain('제244조의6');
    }
    fireEvent.click(within(modal).getByRole('button', { name: '현재 기준 누적 비교' }));
    expect(within(modal).getByRole('button', { name: '현재 기준 누적 비교' })).toHaveAttribute('aria-pressed', 'true');
    expect(strip.textContent).toContain('2026.10.02'); expect(strip.textContent).toContain(`${cum}개`);
    expect(modal.querySelectorAll('.diff-article-card')).toHaveLength(cum as number);
    fireEvent.click(within(modal).getByRole('button', { name: '직전 시행상태 대비' }));
    expect(strip.textContent).toContain(before); expect(modal.querySelectorAll('.diff-article-card')).toHaveLength(inc as number);
  });
  it('uses the same article set as persistent history for every effective state', () => {
    for (const future of detail.upcoming) {
      const event = history.find((e) => e.canonical_id === detail.rule.canonical_id && e.after_version?.effective_date === future.metadata.effective_date)!;
      expect(event.before_version?.snapshot_url).toBe(future.articles_compared_to?.snapshot_url);
      expect(event.changed_articles.map((a) => a.article_number)).toEqual(future.changed_articles?.map((a) => a.article_number));
    }
  });
  it('keeps the date and baseline selector accessible when incremental changes are empty', async () => {
    const empty = structuredClone(detail); empty.upcoming[0].changed_articles = [];
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(empty);
    render(<RuleDetailModal rule={empty.rule} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText(/불러오는 중입니다/)).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole('tab', { name: '시행 예정 2027.02.05 시행 예정' }));
    expect(screen.getByText('이 비교 기준에서는 조문 변경이 없습니다.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '현재 기준 누적 비교' }));
    expect(screen.getByRole('dialog').querySelectorAll('.diff-article-card')).toHaveLength(3);
  });
});
