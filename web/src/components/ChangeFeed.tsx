import React from 'react';
import { DisplayChangeEvent } from '../types';
import { formatDotDate } from '../utils/date';
import { ExternalLink, Eye, ChevronRight } from 'lucide-react';

interface ChangeFeedProps {
  title: string;
  badgeText?: string;
  events: DisplayChangeEvent[];
  emptyMessage?: string;
  onSelectEvent: (event: DisplayChangeEvent) => void;
  featuredStyle?: 'today' | 'upcoming' | 'recent';
}

export const ChangeFeed: React.FC<ChangeFeedProps> = ({
  title,
  badgeText,
  events,
  emptyMessage = '해당 조건의 변경 사항이 없습니다.',
  onSelectEvent,
  featuredStyle,
}) => {
  return (
    <section className="section-block" aria-label={title}>
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">{title}</h2>
          {badgeText && <span className="section-badge">{badgeText}</span>}
        </div>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <p>{emptyMessage}</p>
        </div>
      ) : (
        <div className="card-stack">
          {events.map((evt) => {
            const rule = evt.rule_summary;
            const aliasNames = Array.from(
              new Set([...(rule.historical_names || []), ...(rule.seed_names || [])])
            ).filter((name) => name !== rule.current_name);

            return (
              <article
                key={evt.id}
                className={`event-card ${
                  featuredStyle === 'today'
                    ? 'today-featured'
                    : featuredStyle === 'upcoming'
                    ? 'upcoming-featured'
                    : ''
                }`}
              >
                <div className="event-card-top">
                  <div className="card-badges">
                    <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                      {rule.corrections_category}
                    </span>

                    <span className="badge badge-change-type">
                      {evt.change_type_label}
                    </span>

                    {evt.business_domains.map((dom) => (
                      <span key={dom} className="badge badge-domain-reviewed">
                        {dom}
                      </span>
                    ))}
                  </div>

                  <div className="card-meta-right">
                    {evt.d_day !== null && (
                      <span className={`d-day-badge ${evt.d_day === 0 ? 'today' : ''}`}>
                        {evt.d_day === 0
                          ? 'D-DAY'
                          : evt.d_day > 0
                          ? `D-${evt.d_day}`
                          : `D+${Math.abs(evt.d_day)}`}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <h3
                    className="event-card-title"
                    onClick={() => onSelectEvent(evt)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectEvent(evt)}
                  >
                    {evt.rule_name}
                  </h3>

                  {aliasNames.length > 0 && (
                    <div className="stale-name-box" style={{ marginTop: '0.375rem' }}>
                      <span className="stale-name-label">이전 명칭:</span>
                      <span>{aliasNames.join(', ')}</span>
                    </div>
                  )}
                </div>

                <p className="factual-desc">{evt.factual_description}</p>

                <div className="card-footer">
                  <div className="footer-info">
                    {evt.effective_date && (
                      <span>
                        시행일: <strong>{formatDotDate(evt.effective_date)}</strong>
                      </span>
                    )}
                    {evt.department && (
                      <span>
                        소관: <strong>{evt.department}</strong>
                      </span>
                    )}
                    {evt.detected_at && (
                      <span>
                        감지: {formatDotDate(evt.detected_at)}
                      </span>
                    )}
                  </div>

                  <div className="footer-actions">
                    <button
                      type="button"
                      className="btn-detail"
                      onClick={() => onSelectEvent(evt)}
                      aria-label={`${evt.rule_name} 상세 및 조문 보기`}
                    >
                      <Eye size={14} aria-hidden="true" />
                      <span>상세 정보</span>
                      <ChevronRight size={14} aria-hidden="true" />
                    </button>

                    {evt.official_source_url && (
                      <a
                        href={evt.official_source_url}
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
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
};
