import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import { NoticeFooter } from '../components/NoticeFooter';
import { RegulationDirectory } from '../components/RegulationDirectory';
import { GlobalSearch } from '../components/GlobalSearch';
import { RuleDetailModal } from '../components/RuleDetailModal';
import { RecentChangesSection } from '../components/RecentChangesSection';
import { api } from '../services/api';
import { RuleDetailResponse, RulesResponse, PersistentChangeEvent } from '../types';

const root = path.resolve(__dirname, '../../../public/api/v1');
const rules: RulesResponse = JSON.parse(fs.readFileSync(path.join(root, 'rules.json'), 'utf8'));
const law = rules.rules.find((r) => r.current_name === '형사소송법')!;
const detail: RuleDetailResponse = JSON.parse(fs.readFileSync(path.join(root, law.detail_url.replace('/api/v1/', '')), 'utf8'));
const history: PersistentChangeEvent[] = JSON.parse(fs.readFileSync(path.join(root, 'changes/history.json'), 'utf8')).events.filter((e: PersistentChangeEvent) => e.canonical_id === law.canonical_id);
afterEach(() => vi.restoreAllMocks());

describe('Phase 1G production integration', () => {
  it('distinguishes zero article differences from unavailable comparison data', () => {
    const zero = history.find((e) => e.effective_date === law.metadata.effective_date && e.changed_article_count === 0)!;
    expect(zero.comparison_status).toBe('AVAILABLE');
    const unavailable = { ...zero, event_id: 'test-unavailable', comparison_status: 'COMPARISON_UNAVAILABLE' };
    render(<RecentChangesSection events={[zero, unavailable]} rules={[law]} selectedDomains={[]} onSelectEvent={vi.fn()} />);
    expect(screen.getByText('조문 변경 없음')).toBeInTheDocument();
    expect(screen.getByText('비교 자료 없음')).toBeInTheDocument();
  });
  it('renders only the approved creator identity and subordinate disclaimer in the footer', () => {
    render(<NoticeFooter />);
    const footer = screen.getByRole('contentinfo');
    expect(within(footer).getByText('Created by Kim In-jun · Wonju Correctional Institution')).toBeInTheDocument();
    expect(within(footer).getByText('Personal project · Not an official service of Wonju Correctional Institution or the Ministry of Justice.')).toHaveClass('creator-disclaimer');
    expect(footer.textContent).not.toContain('Created by:');
    expect(footer.textContent).not.toContain('교정직 공무원 및 관련 업무 담당자를 위한');
    expect(within(footer).getByText('출처: 법제처 국가법령정보센터')).toBeInTheDocument();
    expect(footer.textContent).toContain('실제 업무 적용 시');
  });
  it('searches the single new law and returns it through the existing domain filter', () => {
    const select = vi.fn();
    render(<RegulationDirectory rules={rules.rules} onSelectRule={select} />);
    fireEvent.change(screen.getByLabelText('규정명 및 이전 명칭 검색'), { target: { value: '형사소송법' } });
    fireEvent.change(screen.getByLabelText('업무 분야 필터'), { target: { value: '수용·보안' } });
    expect(screen.getAllByText('형사소송법')).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: '형사소송법 조문 상세 보기' }));
    expect(select).toHaveBeenCalledWith(law);
  });
  it('finds the law in global search without displaying creator identity outside the footer', () => {
    const select = vi.fn(); render(<GlobalSearch rules={rules.rules} onSelectRule={select} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: '형사소송법' } });
    fireEvent.keyDown(screen.getByRole('searchbox'), { key: 'Enter' });
    expect(select).toHaveBeenCalledWith(law);
    expect(screen.queryByText(/Kim In-jun/)).not.toBeInTheDocument();
  });
  it('opens actual current metadata, selection basis, related targets and recent comparison', async () => {
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(detail);
    const recent = history.find((e) => e.after_version?.identifier === law.version_id && e.changed_article_count > 0)!;
    render(<RuleDetailModal rule={law} initialEvent={recent} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText(/불러오는 중입니다/)).not.toBeInTheDocument());
    const modal = screen.getByRole('dialog');
    expect(within(modal).getByText('선정 근거')).toBeInTheDocument();
    const provenance = law.provenance;
    if (!provenance || typeof provenance === 'string') throw new Error('Expected schema 1.4 structured provenance');
    expect(modal.textContent).toContain(provenance.selection_basis);
    expect(modal.textContent).toContain('수용기록 업무');
    expect(within(modal).getByRole('link', { name: '공식 원문' })).toHaveAttribute('href', 'https://www.law.go.kr/LSW/lsInfoP.do?efYd=20261002&lsiSeq=290189');
    fireEvent.click(within(modal).getByRole('tab', { name: '전·후 전체 비교' }));
    expect(modal.textContent).toContain('종전 버전');
    expect(modal.textContent).toContain('개정 버전');
  });
  it('selects distinct future effective dates sharing the same MST', async () => {
    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(detail);
    render(<RuleDetailModal rule={law} onClose={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText(/불러오는 중입니다/)).not.toBeInTheDocument());
    const group = screen.getByRole('tablist', { name: '개정 버전 선택' });
    const tabs = within(group).getAllByRole('tab');
    for (const tab of tabs) {
      fireEvent.click(tab);
      expect(tabs.filter((t) => t.getAttribute('aria-selected') === 'true')).toHaveLength(1);
    }
  });
});
