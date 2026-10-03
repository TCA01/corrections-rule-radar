import React, { useState, useMemo } from 'react';
import { RuleSummary, BusinessDomain, CONTROLLED_DOMAINS } from '../types';
import { formatDotDate } from '../utils/date';
import { Search, Filter, ExternalLink, ChevronRight } from 'lucide-react';

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
        const dom = selectedDomain as BusinessDomain;
        if (!rule.business_domains.includes(dom)) return false;
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
    <section className="directory-section" aria-labelledby="directory-heading">
      <div className="directory-header">
        <div className="section-title-wrap">
          <span className="editorial-eyebrow">법령 색인</span>
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

        <div className="filter-selects-group">
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
      </div>

      {filteredRules.length === 0 ? (
        <div className="empty-state">
          <Filter size={24} style={{ margin: '0 auto', opacity: 0.5 }} />
          <p>검색 및 필터 조건에 부합하는 규정이 없습니다.</p>
        </div>
      ) : (
        <div className="directory-table" role="table" aria-label="규정 목록">
          <div className="directory-table-header" role="row">
            <span className="col-cat" role="columnheader">구분</span>
            <span className="col-name" role="columnheader">규정명</span>
            <span className="col-domain" role="columnheader">관련 분야</span>
            <span className="col-date" role="columnheader">시행일자</span>
            <span className="col-action" role="columnheader">상세</span>
          </div>

          <div className="directory-table-body" role="rowgroup">
            {filteredRules.map((rule) => {
              const isRepealed = rule.status === 'REPEALED';
              const aliasNames = Array.from(
                new Set([...(rule.historical_names || []), ...(rule.seed_names || [])])
              ).filter((name) => name !== rule.current_name);

              return (
                <div
                  key={rule.canonical_id}
                  className={`directory-table-row ${isRepealed ? 'repealed' : ''}`}
                  role="row"
                  tabIndex={0}
                  onClick={() => onSelectRule(rule)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectRule(rule)}
                >
                  <div className="col-cat" role="cell">
                    <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                      {rule.corrections_category}
                    </span>
                    {isRepealed && <span className="badge badge-repealed">폐지</span>}
                  </div>

                  <div className="col-name" role="cell">
                    <div className="directory-row-title-wrap">
                      <span className="directory-row-title">
                        {rule.current_name}
                      </span>
                    </div>

                    {aliasNames.length > 0 && (
                      <div className="directory-alias-note">
                        <span className="alias-label">이전 명칭:</span> {aliasNames.join(', ')}
                      </div>
                    )}

                    <div className="directory-row-meta-sub">
                      <span>{rule.metadata.ministry || '법무부'}</span>
                      {rule.metadata.department && <span>· {rule.metadata.department}</span>}
                    </div>
                  </div>

                  <div className="col-domain" role="cell">
                    <div className="domain-labels-wrap">
                      {rule.business_domains.map((dom) => (
                        <span key={dom} className="domain-label">
                          {dom}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="col-date" role="cell">
                    <span className="date-text">{formatDotDate(rule.metadata.effective_date)}</span>
                    {rule.metadata.amendment_type && (
                      <span className="amend-type-text">{rule.metadata.amendment_type}</span>
                    )}
                  </div>

                  <div className="col-action" role="cell">
                    <button
                      type="button"
                      className="row-open-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRule(rule);
                      }}
                      aria-label={`${rule.current_name} 조문 상세 보기`}
                    >
                      <span>조문</span>
                      <ChevronRight size={14} />
                    </button>
                    <a
                      href={rule.official_source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="row-external-link"
                      onClick={(e) => e.stopPropagation()}
                      title="국가법령정보센터 공식 원문 보기"
                      aria-label={`${rule.current_name} 국가법령정보센터 공식 원문 (새 창)`}
                    >
                      <ExternalLink size={14} />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
};
