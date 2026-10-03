import React from 'react';
import { HealthResponse } from '../types';
import { formatDateTime } from '../utils/date';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface HeaderProps {
  health: HealthResponse | null;
  onOpenDemo?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health }) => {
  const isDegraded = health ? health.status !== 'OK' || health.publication_status !== 'PUBLISHED' : false;
  const lastSyncStr = health ? formatDateTime(health.last_successful_sync) : '-';

  return (
    <header className="site-header" role="banner">
      {isDegraded && (
        <div className="degraded-banner" role="alert">
          <AlertTriangle size={15} />
          <span>일부 데이터 확인이 지연되고 있습니다. 마지막 정상 데이터가 표시됩니다.</span>
        </div>
      )}

      <div className="container">
        <div className="header-inner">
          <div className="header-brand-block">
            <a href="#" className="brand" aria-label="교정관련 규정 추적기 홈">
              <span className="brand-badge">법령·행정규칙 추적</span>
              <h1 className="brand-title">교정관련 규정 추적기</h1>
            </a>
            <p className="brand-subtitle">
              교정업무에 관련된 법령·예규·훈령의 변경과 시행예정을 추적합니다.
            </p>
          </div>

          <div className="header-meta-block">
            <div
              className="sync-status"
              title={`마지막 정상 동기화: ${lastSyncStr}`}
              aria-label={`동기화 상태: 마지막 정상 동기화 ${lastSyncStr}`}
            >
              <span
                className={`status-dot ${isDegraded ? 'degraded' : 'ok'}`}
                aria-hidden="true"
              />
              <span className="sync-label">
                마지막 정상 동기화: <strong>{lastSyncStr}</strong>
              </span>
              <CheckCircle2
                size={14}
                className="sync-icon"
                style={{ color: isDegraded ? '#d97706' : '#15803d' }}
                aria-hidden="true"
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
