import React from 'react';
import { BusinessDomain, CONTROLLED_DOMAINS } from '../types';
import { Check } from 'lucide-react';

interface DomainSelectorProps {
  selectedDomains: BusinessDomain[];
  onToggleDomain: (domain: BusinessDomain) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  domainCounts: Record<string, number>;
}

export const DomainSelector: React.FC<DomainSelectorProps> = ({
  selectedDomains,
  onToggleDomain,
  onSelectAll,
  onClearAll,
  domainCounts,
}) => {
  const isAllSelected = selectedDomains.length === CONTROLLED_DOMAINS.length;

  return (
    <section className="domain-section" aria-labelledby="domain-selector-heading">
      <div className="domain-header">
        <div className="domain-title-group">
          <div className="domain-title-row">
            <span className="editorial-eyebrow">필터링</span>
            <h2 id="domain-selector-heading" className="domain-title">
              내 업무 분야
            </h2>
            {selectedDomains.length > 0 && (
              <span className="active-filter-badge">{selectedDomains.length}개 분야 선택됨</span>
            )}
          </div>
          <p className="domain-subtitle">
            관련 업무 분야를 선택하면 해당 규정과 변경 사항만 선별하여 표시합니다.
          </p>
        </div>

        <div className="domain-actions">
          <button
            type="button"
            className="domain-action-btn"
            onClick={onSelectAll}
            aria-pressed={isAllSelected}
          >
            전체 선택
          </button>
          <span className="action-divider">|</span>
          <button
            type="button"
            className="domain-action-btn"
            onClick={onClearAll}
            disabled={selectedDomains.length === 0}
          >
            선택 해제
          </button>
        </div>
      </div>

      <div className="domain-chips-grid" role="group" aria-label="업무 분야 선택 필터">
        {CONTROLLED_DOMAINS.map((domain) => {
          const isSelected = selectedDomains.includes(domain);
          const count = domainCounts[domain] || 0;

          return (
            <button
              key={domain}
              type="button"
              className={`domain-chip ${isSelected ? 'active' : ''}`}
              onClick={() => onToggleDomain(domain)}
              aria-pressed={isSelected}
            >
              <span className="chip-indicator" aria-hidden="true">
                {isSelected && <Check size={12} strokeWidth={3} />}
              </span>
              <span className="chip-name">{domain}</span>
              <span className="chip-count">{count}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
};
