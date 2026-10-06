import React from 'react';

interface SummaryCardsProps {
  todayCount: number;
  upcoming30Count: number;
  recent90Count?: number;
  recent30Count?: number;
  totalTrackedCount: number;
  currentCount?: number;
  historicalCount?: number;
  onSelectCard?: (type: 'today' | 'upcoming' | 'recent' | 'total') => void;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({
  todayCount,
  upcoming30Count,
  recent90Count,
  recent30Count,
  totalTrackedCount,
  currentCount,
  historicalCount,
  onSelectCard,
}) => {
  const displayRecentCount = recent90Count !== undefined ? recent90Count : (recent30Count ?? 0);

  return (
    <section className="editorial-summary-band" aria-label="주요 규정 동향 통계">
      <div className="summary-band-inner">
        {/* Item 1: 오늘 시행 */}
        <div
          className="summary-stat-cell"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('today')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('today')}
          aria-label={`오늘 시행: ${todayCount}건`}
        >
          <span className="summary-stat-label">오늘 시행</span>
          <div className="summary-stat-val">
            <span className="stat-number">{todayCount}</span>
            <span className="stat-unit">건</span>
          </div>
          <span className="summary-stat-sub">당일 효력 발생 규정</span>
        </div>

        <div className="summary-divider" aria-hidden="true" />

        {/* Item 2: 30일 내 시행 예정 */}
        <div
          className="summary-stat-cell"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('upcoming')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('upcoming')}
          aria-label={`30일 내 시행 예정: ${upcoming30Count}건`}
        >
          <span className="summary-stat-label">30일 내 시행예정</span>
          <div className="summary-stat-val">
            <span className="stat-number">{upcoming30Count}</span>
            <span className="stat-unit">건</span>
          </div>
          <span className="summary-stat-sub">향후 도래 예정 조항</span>
        </div>

        <div className="summary-divider" aria-hidden="true" />

        {/* Item 3: 최근 90일 변경 */}
        <div
          className="summary-stat-cell"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('recent')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('recent')}
          aria-label={`최근 90일 변경: ${displayRecentCount}건`}
        >
          <span className="summary-stat-label">최근 90일 변경</span>
          <div className="summary-stat-val">
            <span className="stat-number">{displayRecentCount}</span>
            <span className="stat-unit">건</span>
          </div>
          <span className="summary-stat-sub">최근 개정·적용 내역</span>
        </div>

        <div className="summary-divider" aria-hidden="true" />

        {/* Item 4: 추적 규정 */}
        <div
          className="summary-stat-cell total-cell"
          tabIndex={0}
          role="button"
          onClick={() => onSelectCard?.('total')}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelectCard?.('total')}
          aria-label={`추적 규정: 총 ${totalTrackedCount}개`}
        >
          <span className="summary-stat-label">추적 규정</span>
          <div className="summary-stat-val">
            <span className="stat-number">{totalTrackedCount}</span>
            <span className="stat-unit">개</span>
          </div>
          <span className="summary-stat-sub">{currentCount !== undefined ? `현행 ${currentCount} · 폐지/역사 ${historicalCount ?? 0}` : '교정 핵심 법령·훈령·예규'}</span>
        </div>
      </div>
    </section>
  );
};
