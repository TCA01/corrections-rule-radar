import React, { useMemo } from 'react';
import { PersistentChangeEvent, RuleSummary, BusinessDomain } from '../types';
import { formatDotDate } from '../utils/date';
import { ExternalLink, Eye, History } from 'lucide-react';

interface RecentChangesSectionProps {
  events: PersistentChangeEvent[];
  ruleMap?: Map<string, RuleSummary>;
  rules?: RuleSummary[];
  selectedDomains: BusinessDomain[] | string[];
  onSelectEvent: (event: PersistentChangeEvent, rule?: RuleSummary) => void;
  onSelectRule?: (rule: RuleSummary) => void;
}

export const RecentChangesSection: React.FC<RecentChangesSectionProps> = ({
  events,
  ruleMap,
  rules,
  selectedDomains,
  onSelectEvent,
}) => {
  const effectiveRuleMap = useMemo(() => {
    if (ruleMap) return ruleMap;
    const map = new Map<string, RuleSummary>();
    if (rules) {
      for (const r of rules) {
        map.set(r.canonical_id, r);
      }
    }
    return map;
  }, [ruleMap, rules]);

  // Filter by selected business domains if any
  const filteredEvents = events.filter((evt) => {
    if (selectedDomains.length === 0) return true;
    const rule = effectiveRuleMap.get(evt.canonical_id);
    if (!rule) return true;
    return rule.business_domains.some((d) => selectedDomains.includes(d));
  });

  return (
    <section className="section-block recent-changes-section" aria-labelledby="recent-changes-heading">
      <div className="section-header">
        <div className="section-title-wrap">
          <History size={20} className="section-icon" aria-hidden="true" />
          <h2 id="recent-changes-heading" className="section-title">
            최근 규정 변경
          </h2>
          <span className="section-badge">최근 90일 ({filteredEvents.length}건)</span>
        </div>
        <p className="section-subtitle">
          최근 90일 이내에 개정·시행된 법령·예규·훈령의 변경 이력과 개정 조문 대비표를 확인합니다.
        </p>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="empty-state">
          <p>
            {selectedDomains.length > 0
              ? '선택하신 업무 분야에 해당하는 최근 90일 변경 내역이 없습니다.'
              : '최근 90일 이내 등록된 변경 내역이 없습니다.'}
          </p>
        </div>
      ) : (
        <div className="recent-changes-table-wrapper">
          <table className="recent-changes-table" aria-label="최근 90일 규정 변경 목록">
            <thead>
              <tr>
                <th scope="col" style={{ width: '100px' }}>시행일자</th>
                <th scope="col" style={{ width: '80px' }}>구분</th>
                <th scope="col">규정명</th>
                <th scope="col" style={{ width: '110px' }}>개정 조문</th>
                <th scope="col" style={{ width: '140px' }}>업무 분야</th>
                <th scope="col" style={{ width: '80px' }}>상태</th>
                <th scope="col" style={{ width: '220px', textAlign: 'right' }}>조치</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((evt) => {
                const rule = effectiveRuleMap.get(evt.canonical_id) || {
                  canonical_id: evt.canonical_id,
                  source_kind: (evt.regulation_type === '법률' || evt.regulation_type === '대통령령' || evt.regulation_type === '법무부령' ? 'law' : 'admrul') as 'law' | 'admrul',
                  current_name: evt.regulation_name,
                  seed_names: [evt.regulation_name],
                  historical_names: [],
                  corrections_category: (evt.regulation_type as any) || '법률',
                  business_domains: [],
                  classification_status: 'REVIEWED' as const,
                  primary_domain: null,
                  secondary_domains: [],
                  status: 'CURRENT' as const,
                  version_id: evt.after_version?.version_id || '',
                  metadata: {
                    name: evt.regulation_name,
                    rule_type: evt.regulation_type,
                    issue_date: evt.promulgation_or_issue_date || null,
                    issue_number: null,
                    effective_date: evt.effective_date,
                    ministry: '법무부',
                    department: null,
                    amendment_type: (evt.change_type === 'RULE_AMENDED' ? '일부개정' : evt.change_type) as string,
                    official_state: 'Y',
                  },
                  official_source_url: evt.official_source_url,
                  detail_url: `/api/v1/rules/${evt.canonical_id}.json`,
                };

                const isLaw = rule.source_kind === 'law';
                const statusBadge = rule.status === 'REPEALED' ? '폐지' : '현행';
                const domains = rule.business_domains.length > 0 ? rule.business_domains.join(', ') : '-';

                const regName = evt.regulation_name || (evt as any).rule_name || rule.current_name;
                const regType = evt.regulation_type || (evt as any).corrections_category || rule.corrections_category;
                const artCount = evt.changed_article_count ?? (evt as any).changed_articles_count ?? (evt.changed_articles?.length || 0);

                return (
                  <tr key={evt.event_id} className="recent-change-row">
                    <td className="recent-date-cell">
                      <span className="tabular-date">{formatDotDate(evt.effective_date)}</span>
                    </td>
                    <td>
                      <span className={`badge ${isLaw ? 'badge-law' : 'badge-admin'}`}>
                        {regType}
                      </span>
                    </td>
                    <td className="recent-name-cell">
                      <button
                        type="button"
                        className="recent-rule-name-btn"
                        onClick={() => onSelectEvent(evt, rule)}
                        title={`${regName} 상세 및 대비표 보기`}
                      >
                        {regName}
                      </button>
                    </td>
                    <td className="recent-articles-cell">
                      <span className="articles-count-tag">
                        {artCount > 0 ? `${artCount}개 조문` : '조문 변경'}
                      </span>
                    </td>
                    <td className="recent-domain-cell">
                      <span className="domain-text-muted">{domains}</span>
                    </td>
                    <td>
                      <span className={`badge ${rule.status === 'REPEALED' ? 'badge-repealed' : 'badge-current'}`}>
                        {statusBadge}
                      </span>
                    </td>
                    <td className="recent-actions-cell">
                      <div className="recent-btn-group">
                        <button
                          type="button"
                          className="btn-action-primary"
                          onClick={() => onSelectEvent(evt, rule)}
                          aria-label={`${regName} 변경 내용 보기`}
                        >
                          <Eye size={13} aria-hidden="true" />
                          <span>변경 내용 보기</span>
                        </button>
                        <a
                          href={evt.official_source_url || rule.official_source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-action-secondary"
                          title="국가법령정보센터 공식 원문 새 창 열기"
                        >
                          <span>공식 원문</span>
                          <ExternalLink size={12} aria-hidden="true" />
                        </a>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
};
