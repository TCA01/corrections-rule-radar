import React from 'react';
import { RuleSummary, DisplayChangeEvent } from '../types';
import { Sparkles, ArrowRight } from 'lucide-react';
import { formatDotDate } from '../utils/date';

interface DemoHighlightProps {
  upcomingEvent?: DisplayChangeEvent | null;
  latestRule?: RuleSummary | null;
  onOpenDetail: (rule: RuleSummary) => void;
}

export const DemoHighlight: React.FC<DemoHighlightProps> = ({
  upcomingEvent,
  latestRule,
  onOpenDetail,
}) => {
  const targetRule = upcomingEvent?.rule_summary || latestRule;
  if (!targetRule) return null;

  return (
    <div
      style={{
        backgroundColor: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem',
        marginBottom: '2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap',
      }}
      role="region"
      aria-label="30초 데모 추천 사례"
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.875rem' }}>
        <div
          style={{
            backgroundColor: '#dcfce7',
            color: '#15803d',
            padding: '0.5rem',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          aria-hidden="true"
        >
          <Sparkles size={20} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: '#166534',
                backgroundColor: '#bbf7d0',
                padding: '0.125rem 0.5rem',
                borderRadius: 'var(--radius-full)',
              }}
            >
              심사위원 30초 둘러보기 추천 사례
            </span>

            {upcomingEvent?.d_day !== null && upcomingEvent?.d_day !== undefined && (
              <span className="d-day-badge">
                {upcomingEvent.d_day === 0 ? 'D-DAY' : `D-${upcomingEvent.d_day}`}
              </span>
            )}
          </div>

          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#14532d', marginTop: '0.25rem' }}>
            {targetRule.current_name}
          </h3>

          <p style={{ fontSize: '0.875rem', color: '#166534', marginTop: '0.25rem' }}>
            {upcomingEvent
              ? `${formatDotDate(upcomingEvent.effective_date)} 시행 예정: 개정 조문(제5조의2, 제53조의2 등) 대비표와 별표·서식이 준비되어 있습니다.`
              : `${formatDotDate(targetRule.metadata.effective_date)} 최신 시행: 변경 조문 및 관련 업무 분야가 분류되어 있습니다.`}
          </p>
        </div>
      </div>

      <button
        type="button"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.375rem',
          backgroundColor: '#15803d',
          color: 'white',
          padding: '0.5625rem 1rem',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.875rem',
          fontWeight: 600,
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        }}
        onClick={() => onOpenDetail(targetRule)}
      >
        <span>변경 전/후 조문 대비표 보기</span>
        <ArrowRight size={16} aria-hidden="true" />
      </button>
    </div>
  );
};
