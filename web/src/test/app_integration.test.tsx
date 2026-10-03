import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../App';
import { api } from '../services/api';
import fs from 'fs';
import path from 'path';
import {
  ManifestResponse,
  HealthResponse,
  RulesResponse,
  ChangesResponse,
  RuleDetailResponse,
} from '../types';

describe('App End-to-End Integration Test with Production Fixtures', () => {
  const publicDir = path.resolve(__dirname, '../../../tests/fixtures/web_baseline');

  const prodPublicDir = path.resolve(__dirname, '../../../public/api/v1');

  const manifestData: ManifestResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'manifest.json'), 'utf-8')
  );
  const healthData: HealthResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'health.json'), 'utf-8')
  );
  const rulesData: RulesResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8')
  );
  const upcomingData: ChangesResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'changes/upcoming.json'), 'utf-8')
  );
  const latestData: ChangesResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'changes/latest.json'), 'utf-8')
  );
  const recentDataRaw: any = fs.existsSync(path.join(publicDir, 'changes/recent.json'))
    ? JSON.parse(fs.readFileSync(path.join(publicDir, 'changes/recent.json'), 'utf-8'))
    : JSON.parse(fs.readFileSync(path.join(prodPublicDir, 'changes/recent.json'), 'utf-8'));
  const recentData: any = { ...recentDataRaw, dataset_version: manifestData.dataset_version };
  const lawDetailData: RuleDetailResponse = JSON.parse(
    fs.readFileSync(path.join(publicDir, 'rules/law-001668.json'), 'utf-8')
  );

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-10-03T03:00:00Z'));
    vi.spyOn(api, 'getManifest').mockResolvedValue(manifestData);
    vi.spyOn(api, 'getHealth').mockResolvedValue(healthData);
    vi.spyOn(api, 'getRules').mockResolvedValue(rulesData);
    vi.spyOn(api, 'getUpcomingChanges').mockResolvedValue(upcomingData);
    vi.spyOn(api, 'getLatestChanges').mockResolvedValue(latestData);
    vi.spyOn(api, 'getRecentChanges').mockResolvedValue(recentData);
    vi.spyOn(api, 'getRuleDetail').mockImplementation((id: string) => {
      if (id === 'law-001668') return Promise.resolve(lawDetailData);
      const file = path.join(publicDir, `rules/${id}.json`);
      if (fs.existsSync(file)) {
        return Promise.resolve(JSON.parse(fs.readFileSync(file, 'utf-8')));
      }
      return Promise.reject(new Error('Rule not found'));
    });
  });

  afterEach(() => { vi.useRealTimers(); });

  it('rejects mixed dataset versions during a hosting update', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({ ...healthData, dataset_version: 'ds-mixed' });
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/데이터 버전이 갱신 중입니다/)).toBeInTheDocument();
    });
  });

  it('loads entire dataset, displays last successful sync, and dynamic counts without hardcoding', async () => {
    render(<App />);

    // Wait for data load
    await waitFor(() => {
      expect(screen.getByText('추적 규정')).toBeInTheDocument();
    });

    // Check new branding "교정관련 규정 추적기" is present and old branding is completely eradicated
    expect(screen.getAllByText('교정관련 규정 추적기').length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('교정업무 변경 레이더')).not.toBeInTheDocument();

    // Check last successful sync is displayed
    expect(screen.getByText(/마지막 정상 동기화:/)).toBeInTheDocument();

    // Check total tracked regulations count matches actual rules.length (68)
    expect(screen.getByText('추적 규정')).toBeInTheDocument();
    expect(screen.getByText(String(rulesData.rules.length))).toBeInTheDocument();

    // Check recent 90-day changes section is rendered
    expect(screen.getByText('최근 규정 변경')).toBeInTheDocument();

    // Check upcoming regulations section contains law-001668
    expect(screen.getByText('시행 예정 규정 타임라인')).toBeInTheDocument();
    const lawTitles = screen.getAllByText('형의 집행 및 수용자의 처우에 관한 법률');
    expect(lawTitles.length).toBeGreaterThanOrEqual(1);

    // D-Day badge for 2026-12-24
    expect(screen.getAllByText(/D-8[123]/).length).toBeGreaterThanOrEqual(1);
  });

  it('filters by business domains and persists in localStorage', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('추적 규정')).toBeInTheDocument();
    });

    // Select domain '보관금품' in domain selector
    const domainGroup = screen.getByRole('group', { name: '업무 분야 선택 필터' });
    const bokwanBtn = within(domainGroup).getByRole('button', { name: /보관금품/ });
    fireEvent.click(bokwanBtn);

    // Verify localStorage has '보관금품'
    const saved = localStorage.getItem('corrections_rule_radar_domains');
    expect(saved).toContain('보관금품');

    // Deselect
    fireEvent.click(bokwanBtn);
    const savedAfter = localStorage.getItem('corrections_rule_radar_domains');
    expect(savedAfter).toBe('[]');
  });

  it('searches by alias (영치금품 -> 보관금품 관리지침) and toggles repealed rules', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('추적 규정')).toBeInTheDocument();
    });

    // Alias search
    const searchInput = screen.getByLabelText('규정명 및 이전 명칭 검색');
    fireEvent.change(searchInput, { target: { value: '영치금품' } });

    // Finds 보관금품 관리지침
    expect(screen.getAllByText('보관금품 관리지침').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('이전 명칭:').length).toBeGreaterThanOrEqual(1);

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });

    // By default repealed rules are not shown
    expect(screen.queryByText('교정기관 간판게시 및 교정직제 영문표기에 관한 지침')).not.toBeInTheDocument();

    // Toggle repealed filter
    const repealedToggle = screen.getByLabelText('폐지 규정 포함');
    fireEvent.click(repealedToggle);

    expect(screen.getByText('교정기관 간판게시 및 교정직제 영문표기에 관한 지침')).toBeInTheDocument();
  });

  it('opens RuleDetailModal for law-001668, showing changed articles diff and official disclaimer', async () => {
    render(<App />);

    // Wait until full dataset is loaded
    await waitFor(() => {
      expect(screen.getByText('추적 규정')).toBeInTheDocument();
    });

    // Verify judge/competition demo wording is absent
    expect(screen.queryByText('최근 변경 사례 보기')).not.toBeInTheDocument();
    expect(screen.queryByText(/심사위원 30초/)).not.toBeInTheDocument();
    expect(screen.queryByText(/30초 데모/)).not.toBeInTheDocument();

    // Open law-001668 naturally via upcoming/directory card
    const ruleItem = screen.getAllByText('형의 집행 및 수용자의 처우에 관한 법률')[0];
    fireEvent.click(ruleItem);

    // Modal should open
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Verify changed articles in modal
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /개정 조문 대비표/ })).toBeInTheDocument();
    });

    // Check default unified mode and switch to split mode
    expect(screen.getByText('변경된 부분')).toBeInTheDocument();
    expect(screen.getByText('전·후 전체 비교')).toBeInTheDocument();

    fireEvent.click(screen.getByText('전·후 전체 비교'));
    expect(screen.getAllByText('변경 전 (현행)').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('변경 후 (개정안)').length).toBeGreaterThanOrEqual(1);

    // Verify official disclaimer
    expect(screen.getAllByText('출처: 법제처 국가법령정보센터').length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/본 서비스는 법령·행정규칙 변경사항을 업무 편의를 위해 정리한 참고 서비스입니다/).length
    ).toBeGreaterThanOrEqual(1);

    // Close modal
    fireEvent.click(screen.getByLabelText('닫기'));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('handles degraded health gracefully with warning banner without crashing', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({
      ...healthData,
      status: 'DEGRADED',
      publication_status: 'DEGRADED',
    });

    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByText('일부 데이터 확인이 지연되고 있습니다. 마지막 정상 데이터가 표시됩니다.')
      ).toBeInTheDocument();
    });

    // Site still renders completely with new branding
    expect(screen.getAllByText('교정관련 규정 추적기').length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('교정업무 변경 레이더')).not.toBeInTheDocument();
    expect(screen.getByText('추적 규정')).toBeInTheDocument();
  });
});
