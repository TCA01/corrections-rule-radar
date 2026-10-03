import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SummaryCards } from '../components/SummaryCards';
import { DomainSelector } from '../components/DomainSelector';
import { UpcomingTimeline } from '../components/UpcomingTimeline';
import { RegulationDirectory } from '../components/RegulationDirectory';
import { Header } from '../components/Header';
import { RuleDetailModal } from '../components/RuleDetailModal';
import { RuleSummary, DisplayChangeEvent, RuleDetailResponse } from '../types';
import { api } from '../services/api';

const mockRule: RuleSummary = {
  canonical_id: 'law-001668',
  source_kind: 'law',
  current_name: '형의 집행 및 수용자의 처우에 관한 법률',
  seed_names: ['형의 집행 및 수용자의 처우에 관한 법률'],
  historical_names: ['행형법'],
  corrections_category: '법률',
  business_domains: ['수용·보안', '분류·가석방'],
  classification_status: 'REVIEWED',
  primary_domain: '수용·보안',
  secondary_domains: ['분류·가석방'],
  status: 'CURRENT',
  version_id: '280443',
  metadata: {
    name: '형의 집행 및 수용자의 처우에 관한 법률',
    rule_type: '법률',
    issue_date: '2025-12-23',
    issue_number: '21233',
    effective_date: '2026-12-24',
    ministry: '법무부',
    department: '보안과',
    amendment_type: '일부개정',
    official_state: 'Y',
  },
  official_source_url: 'https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=280443',
  detail_url: '/api/v1/rules/law-001668.json',
};

const mockRepealedRule: RuleSummary = {
  canonical_id: 'admrul-26424',
  source_kind: 'admrul',
  current_name: '교정기관 간판게시 및 교정직제 영문표기에 관한 지침',
  seed_names: ['교정기관 간판게시 및 교정직제 영문표기에 관한 지침'],
  historical_names: [],
  corrections_category: '예규',
  business_domains: ['인사·조직'],
  classification_status: 'REVIEWED',
  primary_domain: '인사·조직',
  secondary_domains: [],
  status: 'REPEALED',
  version_id: '2100000189927',
  metadata: {
    name: '교정기관 간판게시 및 교정직제 영문표기에 관한 지침',
    rule_type: '예규',
    issue_date: '2020-06-08',
    issue_number: '1256',
    effective_date: '2020-06-08',
    ministry: '법무부',
    department: '교정기획과',
    amendment_type: '폐지',
    official_state: 'N',
  },
  official_source_url: 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000189927',
  detail_url: '/api/v1/rules/admrul-26424.json',
};

const mockAliasRule: RuleSummary = {
  canonical_id: 'admrul-28558',
  source_kind: 'admrul',
  current_name: '보관금품 관리지침',
  seed_names: ['영치금품 관리지침'],
  historical_names: ['영치금품 관리지침'],
  corrections_category: '예규',
  business_domains: ['보관금품'],
  classification_status: 'REVIEWED',
  primary_domain: '보관금품',
  secondary_domains: [],
  status: 'CURRENT',
  version_id: '2100000240000',
  metadata: {
    name: '보관금품 관리지침',
    rule_type: '예규',
    issue_date: '2024-05-01',
    issue_number: '1350',
    effective_date: '2024-05-01',
    ministry: '법무부',
    department: '보안과',
    amendment_type: '일부개정',
    official_state: 'Y',
  },
  official_source_url: 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000240000',
  detail_url: '/api/v1/rules/admrul-28558.json',
};

const mockReviewDomainRule: RuleSummary = {
  canonical_id: 'admrul-32484',
  source_kind: 'admrul',
  current_name: '현황작성 및 보고요령 지침',
  seed_names: ['현황작성 및 보고요령 지침'],
  historical_names: [],
  corrections_category: '훈령',
  business_domains: [],
  classification_status: 'REVIEW',
  primary_domain: null,
  secondary_domains: [],
  status: 'CURRENT',
  version_id: '2100000100000',
  metadata: {
    name: '현황작성 및 보고요령 지침',
    rule_type: '훈령',
    issue_date: '2023-01-01',
    issue_number: '1200',
    effective_date: '2023-01-01',
    ministry: '법무부',
    department: '교정기획과',
    amendment_type: '일부개정',
    official_state: 'Y',
  },
  official_source_url: 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000100000',
  detail_url: '/api/v1/rules/admrul-32484.json',
};

const mockEvent: DisplayChangeEvent = {
  id: 'evt-1',
  canonical_id: 'law-001668',
  rule_name: '형의 집행 및 수용자의 처우에 관한 법률',
  corrections_category: '법률',
  business_domains: ['수용·보안'],
  classification_status: 'REVIEWED',
  change_type: 'FUTURE_EFFECTIVE_VERSION',
  change_type_label: '시행 예정',
  detected_at: '2026-10-03T02:20:42Z',
  effective_date: '2026-12-24',
  d_day: 82,
  department: '보안과',
  factual_description: '2026.12.24 시행 예정인 조문이 공식 공포되었습니다.',
  official_source_url: 'https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=280443',
  is_upcoming: true,
  is_today: false,
  status: 'CURRENT',
  rule_summary: mockRule,
};

describe('SummaryCards Component', () => {
  it('renders dynamic counts without hardcoded values', () => {
    render(
      <SummaryCards
        todayCount={1}
        upcoming30Count={0}
        recent30Count={5}
        totalTrackedCount={68}
      />
    );

    expect(screen.getByText('오늘 시행')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('30일 내 시행 예정')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('최근 30일 변경')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('추적 규정')).toBeInTheDocument();
    expect(screen.getByText('68')).toBeInTheDocument();
  });
});

describe('DomainSelector Component', () => {
  it('handles multi-selection, select all, and clear all', () => {
    const toggleMock = vi.fn();
    const selectAllMock = vi.fn();
    const clearAllMock = vi.fn();

    render(
      <DomainSelector
        selectedDomains={['의료', '수용·보안']}
        onToggleDomain={toggleMock}
        onSelectAll={selectAllMock}
        onClearAll={clearAllMock}
        domainCounts={{ 의료: 3, '수용·보안': 12 }}
      />
    );

    expect(screen.getByText('내 업무 분야')).toBeInTheDocument();
    const medicalBtn = screen.getByRole('button', { name: /의료/ });
    expect(medicalBtn).toHaveClass('active');

    fireEvent.click(medicalBtn);
    expect(toggleMock).toHaveBeenCalledWith('의료');

    fireEvent.click(screen.getByRole('button', { name: '전체 선택' }));
    expect(selectAllMock).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: '선택 해제' }));
    expect(clearAllMock).toHaveBeenCalled();
  });
});

describe('UpcomingTimeline Component', () => {
  it('filters by D-day ranges and displays D-day badge', () => {
    const onSelectMock = vi.fn();
    render(<UpcomingTimeline events={[mockEvent]} onSelectEvent={onSelectMock} />);

    expect(screen.getByText('D-82')).toBeInTheDocument();
    expect(screen.getByText('형의 집행 및 수용자의 처우에 관한 법률')).toBeInTheDocument();

    // 7 days filter should show empty state
    fireEvent.click(screen.getByRole('button', { name: '7일 이내' }));
    expect(screen.getByText(/선택하신 기간\(7일 이내\)에 예정된 규정 시행 일정이 없습니다/)).toBeInTheDocument();

    // 90 days filter should show the event
    fireEvent.click(screen.getByRole('button', { name: '90일 이내' }));
    expect(screen.getByText('D-82')).toBeInTheDocument();
  });
});

describe('RegulationDirectory Component', () => {
  const rulesList = [mockRule, mockRepealedRule, mockAliasRule, mockReviewDomainRule];

  it('excludes repealed rules by default and includes them when toggle is checked', () => {
    render(<RegulationDirectory rules={rulesList} onSelectRule={vi.fn()} />);

    // By default, repealed rule is hidden
    expect(screen.queryByText('교정기관 간판게시 및 교정직제 영문표기에 관한 지침')).not.toBeInTheDocument();

    // Toggle repealed filter
    const toggle = screen.getByLabelText('폐지 규정 포함');
    fireEvent.click(toggle);

    // Now repealed rule appears with '폐지' badge
    expect(screen.getByText('교정기관 간판게시 및 교정직제 영문표기에 관한 지침')).toBeInTheDocument();
    expect(screen.getByText('폐지')).toBeInTheDocument();
  });

  it('searches by alias (e.g. 영치금품 finding 보관금품 관리지침)', () => {
    render(<RegulationDirectory rules={rulesList} onSelectRule={vi.fn()} />);

    const searchInput = screen.getByLabelText('규정명 및 이전 명칭 검색');
    fireEvent.change(searchInput, { target: { value: '영치금품' } });

    // Finds 보관금품 관리지침
    expect(screen.getAllByText('보관금품 관리지침').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('이전 명칭:')).toBeInTheDocument();
  });

  it('displays REVIEW domain rules with "업무 분야 검토 중" and remains searchable', () => {
    render(<RegulationDirectory rules={rulesList} onSelectRule={vi.fn()} />);

    const searchInput = screen.getByLabelText('규정명 및 이전 명칭 검색');
    fireEvent.change(searchInput, { target: { value: '현황작성' } });

    expect(screen.getByText('현황작성 및 보고요령 지침')).toBeInTheDocument();
    expect(screen.getAllByText('업무 분야 검토 중').length).toBeGreaterThanOrEqual(1);
  });
});

describe('Header Component', () => {
  it('displays sync time and degraded warning when health status is not OK', () => {
    render(
      <Header
        health={{
          schema_version: '1.2',
          dataset_version: 'ds-1',
          health_scope: 'PUBLISHED_DATASET',
          publication_status: 'DEGRADED',
          status: 'DEGRADED',
          rule_count: 68,
          review_count: 0,
          classification_review_count: 2,
          last_successful_sync: '2026-10-03T02:55:26Z',
        }}
        onOpenDemo={vi.fn()}
      />
    );

    expect(screen.getByRole('alert')).toHaveTextContent(
      '일부 데이터 확인이 지연되고 있습니다. 마지막 정상 데이터가 표시됩니다.'
    );
    expect(screen.getByText(/마지막 정상 동기화:/)).toBeInTheDocument();
  });
});

describe('RuleDetailModal Component', () => {
  it('renders rule detail, changed articles diff side-by-side, and appendices', async () => {
    const mockDetailResponse: RuleDetailResponse = {
      schema_version: '1.2',
      dataset_version: 'ds-1',
      rule: mockRule,
      current: {
        canonical_id: 'law-001668',
        source_kind: 'law',
        stable_identifier: '001668',
        version_id: '1',
        version_status: 'CURRENT',
        version_reference: {
          version_id: '1',
          effective_date: '2026-10-02',
          snapshot_url: '/api/v1/snapshot1.json',
          official_source_url: 'https://www.law.go.kr',
        },
        metadata: mockRule.metadata,
        official_source_url: 'https://www.law.go.kr',
        appendices: [
          {
            branch: '00',
            pdf_url: 'https://www.law.go.kr/pdf',
            sequence: '0001',
            title: '수용기록 서식',
            type: '별표',
            url: 'https://www.law.go.kr/form',
          },
        ],
        attachments: [],
        body: {
          articles: {
            조문단위: [
              { 조문키: '0053021', 조문번호: '53', 조문제목: '태아의 보호 등', 조문내용: '제53조의2 종전' },
            ],
          },
          addenda: {},
        },
        hashes: {
          appendix_hash: 'h1',
          attachment_link_hash: 'h2',
          body_hash: 'h3',
          metadata_hash: 'h4',
        },
      },
      upcoming: [
        {
          canonical_id: 'law-001668',
          source_kind: 'law',
          stable_identifier: '001668',
          version_id: '2',
          version_status: 'FUTURE',
          changed_articles: [{ article_key: '0053021', article_number: '53의2', article_title: '제53조의2(태아의 보호 등)', change_type: 'MODIFIED', before_text: '제53조의2 종전', after_text: '제53조의2 개정안', effective_date: '2026-12-24' }],
          version_reference: {
            version_id: '2',
            effective_date: '2026-12-24',
            snapshot_url: '/api/v1/snapshot2.json',
            official_source_url: 'https://www.law.go.kr',
          },
          metadata: {
            ...mockRule.metadata,
            effective_date: '2026-12-24',
          },
          official_source_url: 'https://www.law.go.kr',
          appendices: [],
          attachments: [],
          body: {
            articles: {
              조문단위: [
                {
                  조문키: '0053021',
                  조문번호: '53',
                  조문제목: '태아의 보호 등',
                  조문내용: '제53조의2 개정안',
                  조문변경여부: 'Y',
                },
              ],
            },
            addenda: {},
          },
          hashes: {
            appendix_hash: 'h1',
            attachment_link_hash: 'h2',
            body_hash: 'h3',
            metadata_hash: 'h4',
          },
        },
      ],
    };

    vi.spyOn(api, 'getRuleDetail').mockResolvedValue(mockDetailResponse);

    render(<RuleDetailModal rule={mockRule} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('개정 조문 대비표 (2026-12-24 시행 예정)')).toBeInTheDocument();
    });

    // Check changed article nav pill
    expect(screen.getByText('변경 조문 1개:')).toBeInTheDocument();
    expect(screen.getAllByText('제53조의2(태아의 보호 등)').length).toBeGreaterThanOrEqual(1);

    // Check side-by-side comparison panels
    expect(screen.getByText('변경 전 (현행)')).toBeInTheDocument();
    expect(screen.getByText('제53조의2 종전')).toBeInTheDocument();
    expect(screen.getByText('변경 후 (개정안)')).toBeInTheDocument();
    expect(screen.getByText('제53조의2 개정안')).toBeInTheDocument();

    // Check appendices
    expect(screen.getByText('관련 별표·서식 (1건)')).toBeInTheDocument();
    expect(screen.getByText('수용기록 서식')).toBeInTheDocument();

    // Check official source notice
    expect(screen.getByText('출처: 법제처 국가법령정보센터')).toBeInTheDocument();
    expect(
      screen.getByText(/본 서비스는 법령·행정규칙 변경사항을 업무 편의를 위해 정리한 참고 서비스입니다/)
    ).toBeInTheDocument();
  });
});
