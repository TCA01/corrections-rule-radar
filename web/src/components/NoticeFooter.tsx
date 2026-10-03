import React from 'react';
import { ExternalLink, Shield } from 'lucide-react';

export const NoticeFooter: React.FC = () => {
  return (
    <footer className="site-footer" role="contentinfo">
      <div className="container">
        <div className="footer-content">
          <div className="footer-brand">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Shield size={18} color="var(--color-primary-light)" />
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>교정업무 변경 레이더</h3>
            </div>
            <p style={{ maxWidth: '400px', lineHeight: 1.5, color: 'var(--color-text-muted)' }}>
              교정직 공무원 및 관련 업무 담당자를 위한 법령·예규·훈령 개정 및 시행 예정 모니터링 시스템입니다.
            </p>
          </div>

          <div className="footer-source">
            <div className="notice-box" style={{ background: '#ffffff' }}>
              <p>
                <strong>출처: 법제처 국가법령정보센터</strong>
              </p>
              <p style={{ marginTop: '0.375rem', fontSize: '0.8125rem' }}>
                본 서비스는 법령·행정규칙 변경사항을 업무 편의를 위해 정리한 참고 서비스입니다.
                실제 업무 적용 시 국가법령정보센터의 공식 원문을 확인하세요.
              </p>
              <p style={{ marginTop: '0.5rem' }}>
                <a
                  href="https://www.law.go.kr"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.8125rem' }}
                >
                  <span>국가법령정보센터 바로가기</span>
                  <ExternalLink size={13} aria-hidden="true" />
                </a>
              </p>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0', textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8' }}>
          교정업무 변경 레이더 — Static Web Client (Firebase Hosting Compatible)
        </div>
      </div>
    </footer>
  );
};
