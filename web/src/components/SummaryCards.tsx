import React from 'react';
import { CalendarCheck, Clock, History, FileText } from 'lucide-react';

interface SummaryCardsProps {
  todayCount: number;
  upcoming30Count: number;
  recent30Count: number;
  totalTrackedCount: number;
  onSelectCard?: (type: 'today' | 'upcoming' | 'recent' | 'total') => void;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({
  todayCount,
  upcoming30Count,
  recent30Count,
  totalTrackedCount,
  onSelectCard,
}) => {
  return (
    <section className="summary-section" aria-label="주요 통계 요약">
      <div className="hero-section">
        <div className="hero-title-group">
          <h1>교정업무 변경 레이더</h1>
          <p className="hero-subtitle">
            법령·예규·훈령의 변경과 시행예정을 업무분야별로 확인하세요.
          </p>
        </div>
      </div>

      <div className="summary-grid">
        <div
          className="summary-card today"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('today')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('today')}
          aria-label={`오늘 시행: ${todayCount}건`}
        >
          <div className="summary-card-header">
            <span className="summary-card-title">오늘 시행</span>
            <div className="summary-card-icon" style={{ backgroundColor: 'var(--color-accent-green-bg)', color: 'var(--color-accent-green)' }}>
              <CalendarCheck size={16} aria-hidden="true" />
            </div>
          </div>
          <div className="summary-card-count">
            {todayCount}
            <span className="summary-card-unit">건</span>
          </div>
          <div className="summary-card-desc">오늘 날짜 기준으로 효력이 발생하는 규정</div>
        </div>

        <div
          className="summary-card upcoming"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('upcoming')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('upcoming')}
          aria-label={`30일 내 시행 예정: ${upcoming30Count}건`}
        >
          <div className="summary-card-header">
            <span className="summary-card-title">30일 내 시행 예정</span>
            <div className="summary-card-icon" style={{ backgroundColor: 'var(--color-accent-amber-bg)', color: 'var(--color-accent-amber)' }}>
              <Clock size={16} aria-hidden="true" />
            </div>
          </div>
          <div className="summary-card-count">
            {upcoming30Count}
            <span className="summary-card-unit">건</span>
          </div>
          <div className="summary-card-desc">향후 30일 이내 시행일이 도래하는 개정 조항</div>
        </div>

        <div
          className="summary-card recent"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('recent')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('recent')}
          aria-label={`최근 30일 변경: ${recent30Count}건`}
        >
          <div className="summary-card-header">
            <span className="summary-card-title">최근 30일 변경</span>
            <div className="summary-card-icon" style={{ backgroundColor: 'var(--color-primary-subtle)', color: 'var(--color-primary-light)' }}>
              <History size={16} aria-hidden="true" />
            </div>
          </div>
          <div className="summary-card-count">
            {recent30Count}
            <span className="summary-card-unit">건</span>
          </div>
          <div className="summary-card-desc">최근 30일 동안 개정·시행된 규정 내역</div>
        </div>

        <div
          className="summary-card total"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('total')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('total')}
          aria-label={`추적 규정: 총 ${totalTrackedCount}개`}
        >
          <div className="summary-card-header">
            <span className="summary-card-title">추적 규정</span>
            <div className="summary-card-icon" style={{ backgroundColor: 'var(--color-surface-hover)', color: 'var(--color-text-main)' }}>
              <FileText size={16} aria-hidden="true" />
            </div>
          </div>
          <div className="summary-card-count">
            {totalTrackedCount}
            <span className="summary-card-unit">개</span>
          </div>
          <div className="summary-card-desc">국가법령정보센터 연계 교정 핵심 법령·훈령·예규</div>
        </div>
      </div>
    </section>
  );
};
