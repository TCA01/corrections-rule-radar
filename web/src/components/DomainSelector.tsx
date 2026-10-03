import React from 'react';
import { BusinessDomain, CONTROLLED_DOMAINS } from '../types';
import { Briefcase, Check } from 'lucide-react';

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Briefcase size={20} color="var(--color-primary-light)" aria-hidden="true" />
            <h2 id="domain-selector-heading" className="domain-title">
              내 업무 분야
            </h2>
          </div>
          <span className="domain-subtitle">
            선택한 분야의 변경사항과 규정이 우선 필터링됩니다 (다중 선택 가능, 자동 저장)
          </span>
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

      <div className="domain-pills" role="group" aria-label="업무 분야 선택 필터">
        {CONTROLLED_DOMAINS.map((domain) => {
          const isSelected = selectedDomains.includes(domain);
          const count = domainCounts[domain] || 0;

          return (
            <button
              key={domain}
              type="button"
              className={`domain-pill ${isSelected ? 'active' : ''}`}
              onClick={() => onToggleDomain(domain)}
              aria-pressed={isSelected}
            >
              {isSelected && <Check size={14} aria-hidden="true" />}
              <span>{domain}</span>
              <span className="domain-pill-count">{count}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
};
