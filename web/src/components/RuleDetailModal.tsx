import React, { useEffect, useState, useRef } from 'react';
import { RuleSummary, RuleDetailResponse, ChangedArticleDiff } from '../types';
import { api, ApiError } from '../services/api';
import { formatDotDate } from '../utils/date';
import { displayArticleDiffs } from '../utils/diff';
import {
  X,
  ExternalLink,
  FileSpreadsheet,
  AlertCircle,
  Loader2,
  Calendar,
  Building2,
  Hash,
  ArrowRight,
  FileText,
} from 'lucide-react';

interface RuleDetailModalProps {
  rule: RuleSummary | null;
  onClose: () => void;
}

export const RuleDetailModal: React.FC<RuleDetailModalProps> = ({ rule, onClose }) => {
  const [detail, setDetail] = useState<RuleDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiffKey, setActiveDiffKey] = useState<string | null>(null);

  const diffRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!rule) {
      setDetail(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    api
      .getRuleDetail(rule.canonical_id)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const msg =
            err instanceof ApiError
              ? `규정 상세 데이터를 불러오지 못했습니다 (${err.message})`
              : '규정 상세 정보를 불러오는 중 오류가 발생했습니다.';
          setError(msg);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [rule]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!rule) return null;

  // Display the canonical backend comparison.
  const upcomingVersion = detail?.upcoming && detail.upcoming.length > 0 ? detail.upcoming[0] : null;
  const articleDiffs: ChangedArticleDiff[] =
    detail && upcomingVersion
      ? displayArticleDiffs(upcomingVersion.changed_articles)
      : [];

  const scrollToDiff = (key: string) => {
    setActiveDiffKey(key);
    const target = diffRefs.current[key];
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const aliasNames = Array.from(
    new Set([...(rule.historical_names || []), ...(rule.seed_names || [])])
  ).filter((name) => name !== rule.current_name);

  const appendices = detail?.current.appendices || [];
  const attachments = detail?.current.attachments || [];

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="rule-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-content">
        <div className="modal-header">
          <div className="modal-title-group">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                {rule.corrections_category}
              </span>
              <span className={`badge ${rule.status === 'REPEALED' ? 'badge-repealed' : 'badge-current'}`}>
                {rule.status === 'REPEALED' ? '폐지' : '현행'}
              </span>
              {rule.classification_status === 'REVIEW' || rule.business_domains.length === 0 ? (
                <span className="badge badge-domain-review">업무 분야 검토 중</span>
              ) : (
                rule.business_domains.map((dom) => (
                  <span key={dom} className="badge badge-domain-reviewed">
                    {dom}
                  </span>
                ))
              )}
            </div>

            <h2 id="rule-modal-title">{rule.current_name}</h2>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="닫기"
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Metadata Section */}
          <div className="detail-section">
            <h3 className="detail-section-title">기본 규정 정보</h3>

            {aliasNames.length > 0 && (
              <div className="stale-name-box">
                <span className="stale-name-label">이전 명칭:</span>
                <span>{aliasNames.join(', ')}</span>
                <span style={{ margin: '0 0.5rem', color: '#cbd5e1' }}>|</span>
                <span className="stale-name-label">현재 명칭:</span>
                <strong>{rule.current_name}</strong>
              </div>
            )}

            <div className="meta-grid">
              <div className="meta-item">
                <span className="meta-label">
                  <Building2 size={12} style={{ display: 'inline', marginRight: 4 }} />
                  소관 부처 / 부서
                </span>
                <span className="meta-val">
                  {rule.metadata.ministry || '법무부'}
                  {rule.metadata.department ? ` (${rule.metadata.department})` : ''}
                </span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Calendar size={12} style={{ display: 'inline', marginRight: 4 }} />
                  시행일자
                </span>
                <span className="meta-val">
                  {formatDotDate(rule.metadata.effective_date)}
                  {rule.metadata.amendment_type ? ` [${rule.metadata.amendment_type}]` : ''}
                </span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Calendar size={12} style={{ display: 'inline', marginRight: 4 }} />
                  공포 / 발령일자
                </span>
                <span className="meta-val">{formatDotDate(rule.metadata.issue_date)}</span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Hash size={12} style={{ display: 'inline', marginRight: 4 }} />
                  발령번호
                </span>
                <span className="meta-val">
                  {rule.metadata.issue_number ? `제${rule.metadata.issue_number}호` : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Loading state */}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
              <Loader2 className="animate-spin" size={24} style={{ marginRight: '0.5rem' }} />
              <span>상세 조문 및 별표 데이터를 불러오는 중입니다...</span>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="empty-state" style={{ borderColor: '#fca5a5', backgroundColor: '#fff1f2' }}>
              <AlertCircle size={24} color="#e11d48" style={{ margin: '0 auto' }} />
              <p style={{ color: '#be123c' }}>{error}</p>
            </div>
          )}

          {/* Old/New Comparison Section */}
          {!loading && !error && upcomingVersion && articleDiffs.length > 0 && (
            <div className="detail-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <h3 className="detail-section-title">
                  {`개정 조문 대비표 (${upcomingVersion.metadata.effective_date} 시행 예정)`}
                </h3>
              </div>

              {/* Changed Articles Navigation */}
              <div className="diff-nav-bar" role="navigation" aria-label="변경 조문 바로가기">
                <span className="diff-nav-title">{`변경 조문 ${articleDiffs.length}개:`}</span>
                <div className="diff-nav-pills">
                  {articleDiffs.map((diff) => (
                    <button
                      key={diff.article_key}
                      type="button"
                      className={`diff-nav-pill ${activeDiffKey === diff.article_key ? 'active' : ''}`}
                      onClick={() => scrollToDiff(diff.article_key)}
                    >
                      {diff.title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Side-by-side (desktop) / Stacked (mobile) Comparison */}
              <div className="diff-comparison-list">
                {articleDiffs.map((diff) => (
                  <div
                    key={diff.article_key}
                    ref={(el) => (diffRefs.current[diff.article_key] = el)}
                    className="diff-card"
                    style={{
                      borderColor: activeDiffKey === diff.article_key ? 'var(--color-primary-light)' : undefined,
                    }}
                  >
                    <div className="diff-card-header">
                      <span className="diff-card-title">{diff.title}</span>
                      <span className="badge badge-change-type">{diff.change_type}</span>
                    </div>

                    <div className="diff-panels">
                      <div className="diff-panel before">
                        <span className="diff-panel-label">변경 전 (현행)</span>
                        <div>{diff.before_text || '〔신설된 조문으로 종전 규정 없음〕'}</div>
                      </div>

                      <div className="diff-panel after">
                        <span className="diff-panel-label">변경 후 (개정안)</span>
                        <div>{diff.after_text || '〔삭제됨〕'}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && !error && (!upcomingVersion || articleDiffs.length === 0) && (
            <div className="detail-section">
              <h3 className="detail-section-title">조문 변경 대비표</h3>
              <div className="empty-state">
                <FileText size={24} style={{ margin: '0 auto', opacity: 0.5 }} />
                <p>
                  별도의 개정 예정 조문 대비 데이터가 없습니다. 현행 규정 원문은 국가법령정보센터를 통해
                  확인하실 수 있습니다.
                </p>
              </div>
            </div>
          )}

          {/* Appendices & Forms Section */}
          {!loading && !error && appendices.length > 0 && (
            <div className="detail-section">
              <h3 className="detail-section-title">
                관련 별표·서식 ({appendices.length}건)
              </h3>
              <div className="appendices-list">
                {appendices.map((app, idx) => (
                  <div key={`${app.sequence}-${idx}`} className="appendix-item">
                    <div>
                      <span className="badge badge-admin" style={{ marginRight: '0.5rem' }}>
                        {app.type || '별표/서식'}
                      </span>
                      <span className="appendix-title">{app.title || `별표·서식 제${app.sequence}호`}</span>
                    </div>

                    <div className="appendix-links">
                      {app.url && (
                        <a
                          href={app.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-source"
                          title="공식 다운로드 링크 (국가법령정보센터)"
                        >
                          <FileSpreadsheet size={13} aria-hidden="true" />
                          <span>공식 다운로드</span>
                        </a>
                      )}
                      {app.pdf_url && (
                        <a
                          href={app.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-source"
                          title="공식 PDF 보기"
                        >
                          <span>PDF</span>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attachments Section */}
          {!loading && !error && attachments.length > 0 && (
            <div className="detail-section">
              <h3 className="detail-section-title">
                공식 첨부 자료 ({attachments.length}건)
              </h3>
              <div className="appendices-list">
                {attachments.map((att, idx) => (
                  <div key={idx} className="appendix-item">
                    <span className="appendix-title">{att.title || '공식 개정 첨부물'}</span>
                    {att.url && (
                      <a
                        href={att.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-source"
                      >
                        <ExternalLink size={13} aria-hidden="true" />
                        <span>원문 첨부 열기</span>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trust Notice and Official Link */}
          <div className="notice-box">
            <p>
              <strong>출처: 법제처 국가법령정보센터</strong>
            </p>
            <p style={{ marginTop: '0.25rem' }}>
              본 서비스는 법령·행정규칙 변경사항을 업무 편의를 위해 정리한 참고 서비스입니다.
              실제 업무 적용 시 국가법령정보센터의 공식 원문을 확인하세요.
            </p>
            {rule.official_source_url && (
              <p style={{ marginTop: '0.5rem' }}>
                <a
                  href={rule.official_source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontWeight: 600 }}
                >
                  <span>국가법령정보센터에서 {rule.current_name} 공식 전문 확인하기</span>
                  <ArrowRight size={14} />
                </a>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
