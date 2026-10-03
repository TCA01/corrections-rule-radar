import React, { useState } from 'react';
import { DisplayChangeEvent } from '../types';
import { formatDotDate } from '../utils/date';
import { Clock, ExternalLink, Eye, ChevronRight } from 'lucide-react';

interface UpcomingTimelineProps {
  events: DisplayChangeEvent[];
  onSelectEvent: (event: DisplayChangeEvent) => void;
}

type RangeFilter = '7' | '30' | '90' | 'all';

export const UpcomingTimeline: React.FC<UpcomingTimelineProps> = ({ events, onSelectEvent }) => {
  const [rangeFilter, setRangeFilter] = useState<RangeFilter>('all');

  // Filter events by selected D-day range
  const filteredEvents = events.filter((evt) => {
    if (evt.d_day === null) return rangeFilter === 'all';
    if (evt.d_day < 0) return false; // Future only

    switch (rangeFilter) {
      case '7':
        return evt.d_day <= 7;
      case '30':
        return evt.d_day <= 30;
      case '90':
        return evt.d_day <= 90;
      case 'all':
      default:
        return true;
    }
  });

  return (
    <section className="section-block" aria-labelledby="upcoming-timeline-heading">
      <div className="section-header">
        <div className="section-title-wrap">
          <Clock size={20} color="var(--color-accent-amber)" aria-hidden="true" />
          <h2 id="upcoming-timeline-heading" className="section-title">
            시행 예정 규정 타임라인
          </h2>
          <span className="section-badge">{filteredEvents.length}건</span>
        </div>

        <div className="section-filters" role="group" aria-label="시행 예정 기간 필터">
          <button
            type="button"
            className={`filter-btn ${rangeFilter === '7' ? 'active' : ''}`}
            onClick={() => setRangeFilter('7')}
            aria-pressed={rangeFilter === '7'}
          >
            7일 이내
          </button>
          <button
            type="button"
            className={`filter-btn ${rangeFilter === '30' ? 'active' : ''}`}
            onClick={() => setRangeFilter('30')}
            aria-pressed={rangeFilter === '30'}
          >
            30일 이내
          </button>
          <button
            type="button"
            className={`filter-btn ${rangeFilter === '90' ? 'active' : ''}`}
            onClick={() => setRangeFilter('90')}
            aria-pressed={rangeFilter === '90'}
          >
            90일 이내
          </button>
          <button
            type="button"
            className={`filter-btn ${rangeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setRangeFilter('all')}
            aria-pressed={rangeFilter === 'all'}
          >
            전체
          </button>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="empty-state">
          <p>
            {rangeFilter === 'all'
              ? '현재 등록된 시행 예정 규정이 없습니다.'
              : `선택하신 기간(${
                  rangeFilter === '7' ? '7일' : rangeFilter === '30' ? '30일' : '90일'
                } 이내)에 예정된 규정 시행 일정이 없습니다.`}
          </p>
        </div>
      ) : (
        <div className="card-stack">
          {filteredEvents.map((evt) => {
            const rule = evt.rule_summary;
            return (
              <article key={evt.id} className="event-card upcoming-featured">
                <div className="event-card-top">
                  <div className="card-badges">
                    <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                      {rule.corrections_category}
                    </span>

                    <span className="badge badge-change-type">시행 예정</span>

                    {rule.classification_status === 'REVIEW' || evt.business_domains.length === 0 ? (
                      <span className="badge badge-domain-review">업무 분야 검토 중</span>
                    ) : (
                      evt.business_domains.map((dom) => (
                        <span key={dom} className="badge badge-domain-reviewed">
                          {dom}
                        </span>
                      ))
                    )}
                  </div>

                  <div className="card-meta-right">
                    {evt.d_day !== null && (
                      <span className={`d-day-badge ${evt.d_day === 0 ? 'today' : ''}`}>
                        {evt.d_day === 0 ? 'D-DAY' : `D-${evt.d_day}`}
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
                </div>

                <p className="factual-desc">{evt.factual_description}</p>

                <div className="card-footer">
                  <div className="footer-info">
                    {evt.effective_date && (
                      <span>
                        시행 예정일: <strong>{formatDotDate(evt.effective_date)}</strong>
                      </span>
                    )}
                    {evt.department && (
                      <span>
                        소관부서: <strong>{evt.department}</strong>
                      </span>
                    )}
                  </div>

                  <div className="footer-actions">
                    <button
                      type="button"
                      className="btn-detail"
                      onClick={() => onSelectEvent(evt)}
                    >
                      <Eye size={14} aria-hidden="true" />
                      <span>개정 조문 대비표 보기</span>
                      <ChevronRight size={14} aria-hidden="true" />
                    </button>

                    {evt.official_source_url && (
                      <a
                        href={evt.official_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-source"
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
