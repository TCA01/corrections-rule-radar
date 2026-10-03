import React, { useState, useEffect, useRef, useMemo } from 'react';
import { RuleSummary } from '../types';
import { Search, X, CornerDownLeft, ArrowDown, ArrowUp } from 'lucide-react';

interface GlobalSearchProps {
  rules: RuleSummary[];
  onSelectRule: (rule: RuleSummary) => void;
}

interface SearchResultItem {
  rule: RuleSummary;
  matchedAlias?: string;
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ rules, onSelectRule }) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Global keyboard shortcut '/' to focus search
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        // If not typing in another input
        const tag = (document.activeElement?.tagName || '').toLowerCase();
        if (tag !== 'input' && tag !== 'textarea') {
          e.preventDefault();
          inputRef.current?.focus();
        }
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Filter rules based on query
  const results: SearchResultItem[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const matches: SearchResultItem[] = [];

    for (const rule of rules) {
      const name = rule.current_name.toLowerCase();
      if (name.includes(q)) {
        matches.push({ rule });
        continue;
      }

      // Check historical/seed aliases
      const allAliases = [...(rule.historical_names || []), ...(rule.seed_names || [])];
      const matchedAlias = allAliases.find((a) => a.toLowerCase().includes(q));
      if (matchedAlias) {
        matches.push({ rule, matchedAlias });
      }
    }

    return matches.slice(0, 10);
  }, [rules, query]);

  // Reset selected index when query changes
  useEffect(() => {
    setSelectedIndex(0);
    setIsOpen(query.trim().length > 0);
  }, [query]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) {
      if (e.key === 'Escape') {
        setQuery('');
        setIsOpen(false);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % results.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) {
        handleSelect(results[selectedIndex].rule);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    }
  };

  const handleSelect = (rule: RuleSummary) => {
    onSelectRule(rule);
    setIsOpen(false);
    setQuery('');
  };

  // Scroll active item into view
  useEffect(() => {
    if (listRef.current && isOpen && results.length > 0) {
      const activeEl = listRef.current.children[selectedIndex] as HTMLElement;
      if (activeEl && typeof activeEl.scrollIntoView === 'function') {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex, isOpen, results.length]);

  return (
    <section className="global-search-section" aria-label="통합 규정 검색">
      <div className="global-search-container" ref={containerRef}>
        <div className="search-input-wrapper">
          <Search className="search-icon" size={20} aria-hidden="true" />
          <input
            ref={inputRef}
            type="search"
            className="search-input"
            placeholder="법령·예규·훈령 또는 이전 명칭 검색 (예: 영치금품, 치료감호)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              if (query.trim()) setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            aria-autocomplete="list"
            aria-expanded={isOpen}
            aria-controls="search-results-list"
            aria-activedescendant={
              isOpen && results[selectedIndex]
                ? `search-item-${results[selectedIndex].rule.canonical_id}`
                : undefined
            }
          />
          {query && (
            <button
              type="button"
              className="search-clear-btn"
              onClick={() => {
                setQuery('');
                setIsOpen(false);
                inputRef.current?.focus();
              }}
              aria-label="검색어 지우기"
            >
              <X size={16} />
            </button>
          )}
          <div className="search-shortcut-hint" aria-hidden="true">
            <kbd>/</kbd>
          </div>
        </div>

        {/* Live Search Results Dropdown */}
        {isOpen && (
          <div className="search-results-dropdown" role="region" aria-label="검색 결과">
            {results.length > 0 ? (
              <>
                <div className="search-results-header">
                  <span>검색 결과 {results.length}건</span>
                  <span className="search-keyboard-hint">
                    <ArrowUp size={12} />
                    <ArrowDown size={12} /> 이동 <CornerDownLeft size={12} /> 선택 Esc 닫기
                  </span>
                </div>
                <ul
                  ref={listRef}
                  id="search-results-list"
                  className="search-results-list"
                  role="listbox"
                >
                  {results.map((item, idx) => {
                    const { rule, matchedAlias } = item;
                    const isSelected = idx === selectedIndex;
                    const primaryDomain = rule.business_domains[0];

                    return (
                      <li
                        key={rule.canonical_id}
                        id={`search-item-${rule.canonical_id}`}
                        role="option"
                        aria-selected={isSelected}
                        className={`search-result-row ${isSelected ? 'selected' : ''}`}
                        onClick={() => handleSelect(rule)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                      >
                        <div className="search-result-main">
                          <div className="search-result-title-line">
                            <span className="search-result-category">{rule.corrections_category}</span>
                            <span className="search-result-title">{rule.current_name}</span>
                            {rule.status === 'REPEALED' && (
                              <span className="status-indicator repealed">폐지</span>
                            )}
                          </div>

                          {matchedAlias && (
                            <div className="search-result-alias">
                              <span className="alias-label">이전 명칭:</span> {matchedAlias}
                            </div>
                          )}
                        </div>

                        <div className="search-result-meta">
                          {rule.classification_status === 'REVIEW' || rule.business_domains.length === 0 ? (
                            <span className="domain-label review">분야 검토중</span>
                          ) : (
                            <span className="domain-label">{primaryDomain}</span>
                          )}
                          <span className="effective-label">
                            {rule.metadata.effective_date || '-'}
                          </span>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </>
            ) : (
              <div className="search-no-results">
                <p>"{query}"에 일치하는 규정 또는 이전 명칭이 없습니다.</p>
                <span className="search-help-text">
                  띄어쓰기 없이 검색하거나 핵심 단어로 다시 검색해 보세요.
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
