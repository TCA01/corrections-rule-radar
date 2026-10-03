import React, { useState, useMemo } from 'react';
import { RuleSummary, BusinessDomain, CONTROLLED_DOMAINS } from '../types';
import { formatDotDate } from '../utils/date';
import { Search, Filter, BookOpen, ExternalLink, Eye, ChevronRight } from 'lucide-react';

interface RegulationDirectoryProps {
  rules: RuleSummary[];
  onSelectRule: (rule: RuleSummary) => void;
}

export const RegulationDirectory: React.FC<RegulationDirectoryProps> = ({ rules, onSelectRule }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [includeRepealed, setIncludeRepealed] = useState<boolean>(false);

  // Filtered and searched rules
  const filteredRules = useMemo(() => {
    return rules.filter((rule) => {
      // 1. Repealed filter: Default false (exclude repealed unless includeRepealed is checked)
      if (!includeRepealed && rule.status === 'REPEALED') {
        return false;
      }

      // 2. Category filter
      if (selectedCategory !== 'all' && rule.corrections_category !== selectedCategory) {
        return false;
      }

      // 3. Domain filter
      if (selectedDomain !== 'all') {
        if (selectedDomain === 'REVIEW') {
          if (rule.classification_status !== 'REVIEW') return false;
        } else {
          const dom = selectedDomain as BusinessDomain;
          if (!rule.business_domains.includes(dom)) return false;
        }
      }

      // 4. Search query matching: title, aliases (seed_names, historical_names), department
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        const titleMatch = rule.current_name.toLowerCase().includes(query);
        const seedMatch = rule.seed_names.some((s) => s.toLowerCase().includes(query));
        const histMatch = rule.historical_names.some((h) => h.toLowerCase().includes(query));
        const deptMatch = rule.metadata.department?.toLowerCase().includes(query) ?? false;
        const idMatch = rule.canonical_id.toLowerCase().includes(query);

        if (!titleMatch && !seedMatch && !histMatch && !deptMatch && !idMatch) {
          return false;
        }
      }

      return true;
    });
  }, [rules, includeRepealed, selectedCategory, selectedDomain, searchQuery]);

  return (
    <section className="section-block" aria-labelledby="directory-heading">
      <div className="section-header">
        <div className="section-title-wrap">
          <BookOpen size={20} color="var(--color-primary-light)" aria-hidden="true" />
          <h2 id="directory-heading" className="section-title">
            전체 규정 디렉터리
          </h2>
          <span className="section-badge">총 {filteredRules.length}개</span>
        </div>
      </div>

      <div className="directory-controls">
        <div className="search-input-wrap">
          <Search size={16} className="search-icon" aria-hidden="true" />
          <input
            type="text"
            className="search-input"
            placeholder="규정명 또는 이전 명칭 검색 (예: 영치금품, 분류처우)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="규정명 및 이전 명칭 검색"
          />
        </div>

        <select
          className="control-select"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          aria-label="규정 유형 필터"
        >
          <option value="all">전체 유형</option>
          <option value="법률">법률</option>
          <option value="대통령령">대통령령</option>
          <option value="법무부령">법무부령</option>
          <option value="훈령">훈령</option>
          <option value="예규">예규</option>
        </select>

        <select
          className="control-select"
          value={selectedDomain}
          onChange={(e) => setSelectedDomain(e.target.value)}
          aria-label="업무 분야 필터"
        >
          <option value="all">전체 업무 분야</option>
          {CONTROLLED_DOMAINS.map((dom) => (
            <option key={dom} value={dom}>
              {dom}
            </option>
          ))}
          <option value="REVIEW">업무 분야 검토 중</option>
        </select>

        <label className="repealed-toggle">
          <input
            type="checkbox"
            checked={includeRepealed}
            onChange={(e) => setIncludeRepealed(e.target.checked)}
          />
          <span>폐지 규정 포함</span>
        </label>
      </div>

      {filteredRules.length === 0 ? (
        <div className="empty-state">
          <Filter size={24} style={{ margin: '0 auto', opacity: 0.5 }} />
          <p>검색 및 필터 조건에 부합하는 규정이 없습니다.</p>
        </div>
      ) : (
        <div className="directory-list">
          {filteredRules.map((rule) => {
            const isRepealed = rule.status === 'REPEALED';
            const aliasNames = Array.from(
              new Set([...(rule.historical_names || []), ...(rule.seed_names || [])])
            ).filter((name) => name !== rule.current_name);

            return (
              <div
                key={rule.canonical_id}
                className={`directory-row ${isRepealed ? 'repealed-row' : ''}`}
              >
                <div className="directory-row-main">
                  <div className="directory-row-title-wrap">
                    <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                      {rule.corrections_category}
                    </span>

                    {isRepealed && <span className="badge badge-repealed">폐지</span>}

                    {rule.classification_status === 'REVIEW' || rule.business_domains.length === 0 ? (
                      <span className="badge badge-domain-review">업무 분야 검토 중</span>
                    ) : (
                      rule.business_domains.map((dom) => (
                        <span key={dom} className="badge badge-domain-reviewed">
                          {dom}
                        </span>
                      ))
                    )}

                    <span
                      className="directory-row-title"
                      onClick={() => onSelectRule(rule)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectRule(rule)}
                    >
                      {rule.current_name}
                    </span>
                  </div>

                  {aliasNames.length > 0 && (
                    <div className="stale-name-box">
                      <span className="stale-name-label">이전 명칭:</span>
                      <span>{aliasNames.join(', ')}</span>
                      <span style={{ margin: '0 0.5rem', color: '#cbd5e1' }}>|</span>
                      <span className="stale-name-label">현재:</span>
                      <strong>{rule.current_name}</strong>
                    </div>
                  )}

                  <div className="directory-row-meta">
                    {rule.metadata.department && <span>소관: {rule.metadata.department}</span>}
                    {rule.metadata.effective_date && (
                      <span>
                        시행일: {formatDotDate(rule.metadata.effective_date)}{' '}
                        {rule.metadata.amendment_type && `(${rule.metadata.amendment_type})`}
                      </span>
                    )}
                    {rule.metadata.issue_number && <span>제{rule.metadata.issue_number}호</span>}
                  </div>
                </div>

                <div className="footer-actions" style={{ flexShrink: 0 }}>
                  <button
                    type="button"
                    className="btn-detail"
                    onClick={() => onSelectRule(rule)}
                    aria-label={`${rule.current_name} 규정 상세 보기`}
                  >
                    <Eye size={14} aria-hidden="true" />
                    <span>상세 보기</span>
                    <ChevronRight size={14} aria-hidden="true" />
                  </button>

                  {rule.official_source_url && (
                    <a
                      href={rule.official_source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-source"
                      title="국가법령정보센터 공식 원문 열기"
                    >
                      <ExternalLink size={14} aria-hidden="true" />
                      <span>원문</span>
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
