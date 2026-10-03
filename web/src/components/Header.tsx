import React from 'react';
import { HealthResponse } from '../types';
import { formatDateTime } from '../utils/date';
import { ShieldCheck, AlertTriangle, ArrowRight, BookOpen } from 'lucide-react';

interface HeaderProps {
  health: HealthResponse | null;
  onOpenDemo: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onOpenDemo }) => {
  const isDegraded = health ? health.status !== 'OK' || health.publication_status !== 'PUBLISHED' : false;
  const lastSyncStr = health ? formatDateTime(health.last_successful_sync) : '-';

  return (
    <header className="site-header" role="banner">
      {isDegraded && (
        <div className="degraded-banner" role="alert">
          <AlertTriangle size={16} />
          <span>일부 데이터 확인이 지연되고 있습니다. 마지막 정상 데이터가 표시됩니다.</span>
        </div>
      )}

      <div className="container">
        <div className="header-top">
          <a href="#" className="brand" aria-label="교정업무 변경 레이더 홈">
            <div className="brand-icon" aria-hidden="true">
              <BookOpen size={20} />
            </div>
            <div>
              <span className="brand-title">교정업무 변경 레이더</span>
            </div>
          </a>

          <div className="header-actions">
            <div
              className="sync-status"
              title={`마지막 정상 동기화: ${lastSyncStr}`}
              aria-label={`동기화 상태: 마지막 정상 동기화 ${lastSyncStr}`}
            >
              <span
                className={`status-dot ${isDegraded ? 'degraded' : ''}`}
                aria-hidden="true"
              />
              <span>
                마지막 정상 동기화: <strong>{lastSyncStr}</strong>
              </span>
              <ShieldCheck size={14} style={{ color: isDegraded ? '#d97706' : '#16a34a' }} aria-hidden="true" />
            </div>

            <button
              type="button"
              className="demo-trigger-btn"
              onClick={onOpenDemo}
              title="30초 데모: 최근 변경 사례(형집행법 2026.12.24 시행예정 등)를 바로 확인합니다."
            >
              <span>최근 변경 사례 보기</span>
              <ArrowRight size={14} aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
