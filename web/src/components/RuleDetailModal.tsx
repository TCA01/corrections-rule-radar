import React, { useEffect, useState, useRef, useMemo } from 'react';
import { officialSource } from '../utils/officialSource';
import {
  RuleSummary,
  RuleDetailResponse,
  ChangedArticleDiff,
  PersistentChangeEvent,
} from '../types';
import { api, ApiError } from '../services/api';
import { formatDotDate } from '../utils/date';
import { displayArticleDiffs, computeWordDiff } from '../utils/diff';
import { isRemovedAppendix, getScopeClassLabel } from '../utils/format';
import { decodeDisplayText } from '../utils/text';
import { needsStructuredComparison, VisualComparison } from '../services/comparison';
import {
  X,
  ExternalLink,
  FileSpreadsheet,
  AlertCircle,
  Loader2,
  Calendar,
  Building2,
  Hash,
  FileText,
  Split,
  Eye,
  Download,
} from 'lucide-react';

export interface RuleDetailModalProps {
  rule: RuleSummary | null;
  initialEvent?: PersistentChangeEvent | null;
  initialEffectiveDate?: string | null;
  onClose: () => void;
}

type DiffDisplayMode = 'unified' | 'split';

interface VersionComparisonTarget {
  id: string;
  label: string;
  badge: string;
  effectiveDate: string | null;
  beforeVersion: string;
  afterVersion: string;
  changedArticles: ChangedArticleDiff[];
  comparisonSource: string;
  officialSourceUrl: string;
  unavailable?: boolean;
  cumulative?: { beforeVersion: string; changedArticles: ChangedArticleDiff[] };
}

function isDownloadResource(url: string | null): boolean {
  if (!url) return false;
  const lower = url.toLowerCase();
  return (
    lower.includes('fldownload.do') ||
    lower.endsWith('.hwp') ||
    lower.endsWith('.hwpx') ||
    lower.endsWith('.pdf') ||
    lower.endsWith('.zip') ||
    lower.endsWith('.doc') ||
    lower.endsWith('.docx')
  );
}



export const RuleDetailModal: React.FC<RuleDetailModalProps> = ({
  rule,
  initialEvent,
  initialEffectiveDate,
  onClose,
}) => {
  const [detail, setDetail] = useState<RuleDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiffKey, setActiveDiffKey] = useState<string | null>(null);
  const [diffMode, setDiffMode] = useState<DiffDisplayMode>('unified'); // Default: [변경된 부분]
  const [selectedComparisonId, setSelectedComparisonId] = useState<string>('');
  const [baselineMode, setBaselineMode] = useState<'incremental' | 'cumulative'>('incremental');
  const [visualEvent, setVisualEvent] = useState<{ eventId: string; comparison: VisualComparison } | null>(null);

  useEffect(() => {
    let active = true;
    setVisualEvent(null);
    if (initialEvent && needsStructuredComparison(initialEvent)) {
      api.getVisualComparison(initialEvent).then(comparison => {
        if (active) setVisualEvent({ eventId: initialEvent.event_id, comparison });
      });
    }
    return () => { active = false; };
  }, [initialEvent]);

  const diffRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!rule) {
      setDetail(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setBaselineMode('incremental');
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

  // Build available comparison targets (upcoming, past-effective, or initialEvent)
  const comparisons: VersionComparisonTarget[] = useMemo(() => {
    const list: VersionComparisonTarget[] = [];

    // 1. If opened with a specific event from recent changes
    if (initialEvent) {
      list.push({
        id: `event-${initialEvent.event_id}`,
        label: `${formatDotDate(initialEvent.effective_date)} 개정`,
        badge: '최근 시행',
        effectiveDate: initialEvent.effective_date,
        beforeVersion: initialEvent.before_version?.effective_date || initialEvent.before_version?.identifier || '종전 규정',
        afterVersion: initialEvent.after_version?.effective_date || initialEvent.after_version?.identifier || '개정 규정',
        changedArticles: displayArticleDiffs(needsStructuredComparison(initialEvent)
          ? visualEvent?.eventId === initialEvent.event_id ? visualEvent.comparison.articles : []
          : initialEvent.changed_articles),
        unavailable: needsStructuredComparison(initialEvent) && visualEvent?.eventId === initialEvent.event_id && visualEvent.comparison.textSource === 'UNAVAILABLE',
        comparisonSource: initialEvent.comparison_source || '정밀 조문 대비',
        officialSourceUrl: officialSource({ ...rule, version_id: initialEvent.after_version?.version_id || initialEvent.after_version?.identifier, effective_date: initialEvent.effective_date, official_source_url: initialEvent.official_source_url }),
      });
    }

    // 2. Upcoming future version in detail
    if (detail?.upcoming && detail.upcoming.length > 0) {
      for (const up of detail.upcoming) {
        if (up.changed_articles) {
          const effDate = up.metadata?.effective_date || up.version_reference?.effective_date;
          list.push({
            id: `upcoming-${up.version_id}-${effDate}`,
            label: `${formatDotDate(effDate)} 시행 예정`,
            badge: '시행 예정',
            effectiveDate: effDate,
            beforeVersion: formatDotDate(up.articles_compared_to?.effective_date) || up.articles_compared_to?.version_id || '종전 규정',
            afterVersion: up.version_reference?.effective_date || up.version_id,
            changedArticles: displayArticleDiffs(up.changed_articles),
            comparisonSource: up.comparison_source || 'STRUCTURED_SNAPSHOT_DIFF',
            officialSourceUrl: officialSource({ ...up, source_kind: rule?.source_kind, effective_date: effDate }),
            cumulative: up.cumulative_articles_compared_to && up.cumulative_changed_articles ? {
              beforeVersion: formatDotDate(up.cumulative_articles_compared_to.effective_date),
              changedArticles: displayArticleDiffs(up.cumulative_changed_articles),
            } : undefined,
          });
        }
      }
    }

    // 3. Past-effective current version changes in detail (Phase 1E)
    if (detail?.changed_articles && detail.changed_articles.length > 0) {
      const effDate = detail.current?.metadata?.effective_date || detail.current?.version_reference?.effective_date;
      const alreadyHas = list.some((c) => c.effectiveDate === effDate);
      if (!alreadyHas) {
        list.push({
          id: `current-diff-${detail.current?.version_id}`,
          label: `${formatDotDate(effDate)} 최근 시행`,
          badge: '최근 시행',
          effectiveDate: effDate,
          beforeVersion: detail.articles_compared_to?.effective_date || detail.articles_compared_to?.version_id || '종전 규정',
          afterVersion: detail.current?.version_reference?.effective_date || detail.current?.version_id || '현행 규정',
          changedArticles: displayArticleDiffs(detail.changed_articles),
          comparisonSource: '정밀 조문 대비 (Phase 1E)',
          officialSourceUrl: officialSource(detail.current),
        });
      }
    }

    return list;
  }, [detail, initialEvent, rule, visualEvent]);

  // Set default active comparison target
  useEffect(() => {
    if (comparisons.length > 0) {
      if (!selectedComparisonId || !comparisons.some((c) => c.id === selectedComparisonId)) {
        setSelectedComparisonId(comparisons.find((c) => c.badge === '시행 예정' && c.effectiveDate === initialEffectiveDate)?.id || comparisons[0].id);
      }
    }
  }, [comparisons, selectedComparisonId, initialEffectiveDate]);

  if (!rule) return null;

  const activeComparison =
    comparisons.find((c) => c.id === selectedComparisonId) || comparisons[0] || null;
  const cumulative = baselineMode === 'cumulative' ? activeComparison?.cumulative : undefined;
  const articleDiffs: ChangedArticleDiff[] = cumulative?.changedArticles || activeComparison?.changedArticles || [];
  const beforeVersion = cumulative?.beforeVersion || activeComparison?.beforeVersion;

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

  // Check if provenance exists in backend data (Section 5 & 6)
  const effectiveRule = detail?.rule || rule;
  const provObj =
    typeof effectiveRule.provenance === 'object' && effectiveRule.provenance !== null
      ? (effectiveRule.provenance as import('../types').RuleProvenance)
      : null;
  const selectionBasis =
    provObj?.selection_basis ||
    (typeof effectiveRule.provenance === 'string' ? effectiveRule.provenance : '') ||
    effectiveRule.selection_rationale ||
    '';
  const appliesTo = provObj?.applies_to || [];
  const scopeClassLabel = getScopeClassLabel(provObj?.scope_class);
  const hasProvenance = Boolean(selectionBasis || appliesTo.length > 0 || scopeClassLabel);

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
        {/* Header: VoiceBox Civic Style with Official Source Link right at top (Section 14) */}
        <div className="modal-header">
          <div className="modal-header-top">
            <div className="modal-badges-row">
              <span className={`badge ${rule.source_kind === 'law' ? 'badge-law' : 'badge-admin'}`}>
                {rule.corrections_category}
              </span>
              <span className={`badge ${rule.status === 'REPEALED' ? 'badge-repealed' : 'badge-current'}`}>
                {rule.status === 'REPEALED' ? '폐지' : '현행'}
              </span>
              {rule.business_domains.map((dom) => (
                <span key={dom} className="badge badge-domain-reviewed">
                  {dom}
                </span>
              ))}
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

          <div className="modal-title-row">
            <h2 id="rule-modal-title" className="modal-rule-title">
              {rule.current_name}
            </h2>

            {/* Official Source Action moved to Header (Section 14) */}
            <a
              href={activeComparison?.officialSourceUrl || officialSource(rule)}
              target="_blank"
              rel="noopener noreferrer"
              className="modal-official-link"
              title="국가법령정보센터 공식 원문 새 창 열기"
            >
              <span>공식 원문</span>
              <ExternalLink size={13} aria-hidden="true" />
            </a>
          </div>

          <div className="modal-submeta-row">
            <span className="modal-submeta-item">
              시행 {formatDotDate(rule.metadata.effective_date)}
              {rule.metadata.amendment_type ? ` [${rule.metadata.amendment_type}]` : ''}
            </span>
            <span className="modal-submeta-divider">·</span>
            <span className="modal-submeta-item">
              {rule.metadata.ministry || '법무부'}
              {rule.metadata.department ? ` (${rule.metadata.department})` : ''}
            </span>
          </div>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Metadata Section */}
          <div className="detail-section metadata-section">
            <h3 className="detail-section-title">기본 규정 정보</h3>

            {aliasNames.length > 0 && (
              <div className="stale-name-box">
                <span className="stale-name-label">이전 명칭:</span>
                <span className="stale-name-value">{aliasNames.join(', ')}</span>
                <span className="stale-divider">|</span>
                <span className="stale-name-label">현재 명칭:</span>
                <strong>{rule.current_name}</strong>
              </div>
            )}

            <div className="meta-grid">
              <div className="meta-item">
                <span className="meta-label">
                  <Building2 size={13} aria-hidden="true" />
                  소관 부처 / 부서
                </span>
                <span className="meta-val">
                  {rule.metadata.ministry || '법무부'}
                  {rule.metadata.department ? ` (${rule.metadata.department})` : ''}
                </span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Calendar size={13} aria-hidden="true" />
                  시행일자
                </span>
                <span className="meta-val">
                  {formatDotDate(rule.metadata.effective_date)}
                  {rule.metadata.amendment_type ? ` [${rule.metadata.amendment_type}]` : ''}
                </span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Calendar size={13} aria-hidden="true" />
                  공포 / 발령일자
                </span>
                <span className="meta-val">{formatDotDate(rule.metadata.issue_date)}</span>
              </div>

              <div className="meta-item">
                <span className="meta-label">
                  <Hash size={13} aria-hidden="true" />
                  발령번호
                </span>
                <span className="meta-val">
                  {rule.metadata.issue_number ? `제${rule.metadata.issue_number}호` : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Provenance Slot: Section 5 & 6 */}
          {hasProvenance && (
            <div className="detail-section provenance-section">
              <div className="provenance-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <h3 className="detail-section-title" style={{ margin: 0 }}>선정 근거</h3>
                {scopeClassLabel && (
                  <span className="badge badge-scope-class" style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {scopeClassLabel}
                  </span>
                )}
              </div>
              {selectionBasis ? (
                <p className="provenance-text" style={{ margin: '0 0 0.5rem 0', lineHeight: 1.6 }}>
                  {selectionBasis}
                </p>
              ) : null}
              {appliesTo.length > 0 ? (
                <div className="provenance-applies-to" style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                  <span style={{ fontWeight: 600, marginRight: '0.5rem' }}>관련 대상</span>
                  <span>{appliesTo.join(' · ')}</span>
                </div>
              ) : null}
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="modal-loading-state" role="status">
              <Loader2 className="animate-spin" size={24} />
              <p>규정 상세 정보 및 조문 대비표를 불러오는 중입니다...</p>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="empty-state error" role="alert">
              <AlertCircle size={24} color="#e11d48" />
              <p>{error}</p>
            </div>
          )}

          {/* Legal Diff Comparison Section (Upcoming & Past-Effective Changes) */}
          {!loading && !error && activeComparison && (
            <div className="detail-section diff-section">
              {/* Multiple Version Selector Tabs (if both upcoming and past exist) */}
              {comparisons.length > 1 && (
                <div className="diff-version-tabs" role="tablist" aria-label="개정 버전 선택">
                  {comparisons.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      role="tab"
                      aria-selected={c.id === selectedComparisonId}
                      className={`diff-version-tab ${c.id === selectedComparisonId ? 'active' : ''}`}
                      onClick={() => setSelectedComparisonId(c.id)}
                    >
                      <span className="version-tab-badge">{c.badge}</span>
                      <span className="version-tab-label">{c.label}</span>
                    </button>
                  ))}
                </div>
              )}

              {activeComparison.badge === '시행 예정' && (
                <div className="diff-mode-toggle" role="group" aria-label="시행 예정 비교 기준">
                  <button type="button" aria-pressed={!cumulative} className={`diff-mode-btn ${!cumulative ? 'active' : ''}`} onClick={() => setBaselineMode('incremental')}>
                    직전 시행상태 대비
                  </button>
                  {activeComparison.cumulative && (
                    <button type="button" aria-pressed={Boolean(cumulative)} className={`diff-mode-btn ${cumulative ? 'active' : ''}`} onClick={() => setBaselineMode('cumulative')}>
                      현재 기준 누적 비교
                    </button>
                  )}
                </div>
              )}

              {activeComparison.badge === '시행 예정' && <p className="comparison-explanation">{cumulative ? '현재 시행상태 대비 해당 날짜까지 누적된 변경입니다.' : '직전 시행상태 대비 해당 시행일에 새로 달라지는 조문입니다.'}</p>}
              <div className="diff-header-bar">
                <div className="diff-header-left">
                  <h3 className="detail-section-title">
                    {`개정 조문 대비표 (${formatDotDate(activeComparison.effectiveDate)} ${
                      activeComparison.badge === '시행 예정' ? '시행 예정' : '시행'
                    })`}
                  </h3>
                  <div className="diff-meta-strip">
                    <span className="diff-meta-item">
                      종전 버전: <strong>{beforeVersion}</strong>
                    </span>
                    <span className="diff-meta-divider">→</span>
                    <span className="diff-meta-item">
                      개정 버전: <strong>{formatDotDate(activeComparison.effectiveDate)}</strong>
                    </span>
                    <span className="diff-meta-divider">·</span>
                    <span className="diff-meta-item">
                      개정 조문: <strong>{articleDiffs.length}개</strong>
                    </span>
                  </div>
                </div>

                {/* Diff Mode Selector: [변경된 부분] (DEFAULT) vs [전·후 전체 비교] */}
                <div className="diff-mode-toggle" role="tablist" aria-label="조문 비교 방식 선택">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={diffMode === 'unified'}
                    className={`diff-mode-btn ${diffMode === 'unified' ? 'active' : ''}`}
                    onClick={() => setDiffMode('unified')}
                  >
                    <Eye size={13} />
                    <span>변경된 부분</span>
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={diffMode === 'split'}
                    className={`diff-mode-btn ${diffMode === 'split' ? 'active' : ''}`}
                    onClick={() => setDiffMode('split')}
                  >
                    <Split size={13} />
                    <span>전·후 전체 비교</span>
                  </button>
                </div>
              </div>

              {articleDiffs.length === 0 && <p className="empty-state">{activeComparison.unavailable
                ? '공식 전체 본문을 불러오지 못해 문구 비교를 표시하지 않습니다. 공식 원문을 확인해 주세요.'
                : initialEvent && needsStructuredComparison(initialEvent) && activeComparison.id === `event-${initialEvent.event_id}` && visualEvent?.eventId !== initialEvent.event_id
                  ? '공식 전체 본문을 불러오는 중입니다.' : '이 비교 기준에서는 조문 변경이 없습니다.'}</p>}
              {initialEvent && activeComparison.id === `event-${initialEvent.event_id}`
                && visualEvent?.eventId === initialEvent.event_id && visualEvent.comparison.textSource === 'STRUCTURED_SNAPSHOT'
                && <p className="detail-source-disclaimer">문구 비교: 해당 개정 전·후 공식 전체 본문. 대비표의 축약 표기는 문구 비교에 사용하지 않습니다.</p>}
              {/* Changed Articles Quick Navigation */}
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

              {/* Diff Cards List */}
              <div className="diff-comparison-list">
                {articleDiffs.map((diff) => {
                  const chunks = diff.diff_chunks || computeWordDiff(diff.before_text, diff.after_text);
                  const isModified = diff.change_type === '일부개정' || (!diff.is_new && !diff.is_deleted);

                  return (
                    <div
                      key={diff.article_key}
                      ref={(el) => (diffRefs.current[diff.article_key] = el)}
                      className={`diff-article-card ${diffMode}`}
                      style={{
                        borderColor: activeDiffKey === diff.article_key ? 'var(--color-accent-navy)' : undefined,
                      }}
                    >
                      <div className="diff-card-header">
                        <span className="diff-card-title">{diff.title}</span>
                        <span className={`badge badge-change-type ${diff.is_new ? 'new' : diff.is_deleted ? 'deleted' : 'modified'}`}>
                          {diff.change_type}
                        </span>
                      </div>

                      {/* MODE 1: [변경된 부분] (DEFAULT UNIFIED DIFF) */}
                      {diffMode === 'unified' && (
                        <div className="unified-diff-view">
                          {isModified ? (
                            <div className="unified-diff-content legal-text-wrap">
                              {chunks.map((chunk, cIdx) => {
                                if (chunk.type === 'deleted') {
                                  return (
                                    <del key={cIdx} className="diff-token-del" title="삭제된 문구">
                                      {chunk.text}
                                    </del>
                                  );
                                }
                                if (chunk.type === 'added') {
                                  return (
                                    <ins key={cIdx} className="diff-token-ins" title="추가된 문구">
                                      {chunk.text}
                                    </ins>
                                  );
                                }
                                return (
                                  <span key={cIdx} className="diff-token-context">
                                    {chunk.text}
                                  </span>
                                );
                              })}
                            </div>
                          ) : diff.is_new ? (
                            <div className="unified-diff-content new-article legal-text-wrap">
                              <div className="diff-status-notice new">신설 조문</div>
                              <ins className="diff-token-ins full-text">
                                {diff.after_text || '〔신설 규정 내용 없음〕'}
                              </ins>
                            </div>
                          ) : (
                            <div className="unified-diff-content deleted-article legal-text-wrap">
                              <div className="diff-status-notice deleted">삭제 조문</div>
                              <del className="diff-token-del full-text">
                                {diff.before_text || '〔삭제된 조문 내용 없음〕'}
                              </del>
                            </div>
                          )}
                        </div>
                      )}

                      {/* MODE 2: [전·후 전체 비교] (SPLIT TWO COLUMNS) */}
                      {diffMode === 'split' && (
                        <div className="diff-panels">
                          <div className="diff-panel before">
                            <span className="diff-panel-label">변경 전 ({beforeVersion})</span>
                            <div className="legal-text-wrap">
                              {diff.before_text || '〔신설된 조문으로 종전 규정 없음〕'}
                            </div>
                          </div>

                          <div className="diff-panel after">
                            <span className="diff-panel-label">변경 후 (개정안)</span>
                            <div className="legal-text-wrap">
                              {diff.after_text || '〔삭제됨〕'}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {!loading && !error && !activeComparison && (
            <div className="detail-section">
              <h3 className="detail-section-title">조문 변경 대비표</h3>
              <div className="empty-state">
                <FileText size={24} style={{ margin: '0 auto', opacity: 0.5 }} />
                <p>
                  별도의 개정 조문 대비 데이터가 없습니다. 현행 규정 원문은 상단 공식 원문 링크를 통해
                  확인하실 수 있습니다.
                </p>
              </div>
            </div>
          )}

          {/* Appendices & Forms Section: Sections 15 & 16 */}
          {!loading && !error && appendices.length > 0 && (
            <div className="detail-section">
              <h3 className="detail-section-title">
                현행 규정의 관련 별표·서식 ({appendices.length}건)
              </h3>
              <div className="appendices-list">
                {appendices.map((app, idx) => {
                  const isDeleted = isRemovedAppendix(app);
                  const isDownload = isDownloadResource(app.url);
                  const isPdfPreview = Boolean(app.pdf_url && !isDownloadResource(app.pdf_url));

                  return (
                    <div key={`${app.sequence}-${idx}`} className={`appendix-item ${isDeleted ? 'deleted' : ''}`}>
                      <div className="appendix-icon">
                        <FileSpreadsheet size={16} />
                      </div>
                      <div className="appendix-info">
                        <div className="appendix-title-row">
                          <span className="appendix-title">{decodeDisplayText(app.title || `별표·서식 제${app.sequence}호`)}</span>
                          {isDeleted && <span className="badge badge-repealed">삭제</span>}
                        </div>
                        <span className="appendix-meta">
                          {app.type || '별표/서식'} {app.sequence ? `(제${app.sequence}호)` : ''}
                        </span>
                      </div>

                      {/* Section 15 & 16: Accurate Action Button or Deleted Notice */}
                      {isDeleted ? (
                        <span className="appendix-deleted-badge">해당 개정에서 삭제된 서식</span>
                      ) : isPdfPreview ? (
                        <a
                          href={app.pdf_url!}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="appendix-action-btn preview"
                          title="미리보기 새 창 열기"
                        >
                          <span>미리보기</span>
                          <ExternalLink size={12} aria-hidden="true" />
                        </a>
                      ) : app.url ? (
                        <a
                          href={app.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`appendix-action-btn ${isDownload ? 'download' : 'preview'}`}
                          title={isDownload ? '서식 파일 다운로드' : '미리보기 새 창 열기'}
                        >
                          <span>{isDownload ? '다운로드' : '미리보기'}</span>
                          {isDownload ? <Download size={12} aria-hidden="true" /> : <ExternalLink size={12} aria-hidden="true" />}
                        </a>
                      ) : (
                        <span className="appendix-no-link">링크 없음</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Official Source Link & Trust Notice */}
          <div className="detail-source-section">
            <div className="detail-source-row">
              <span className="source-label">출처: 법제처 국가법령정보센터</span>
              <a
                href={activeComparison?.officialSourceUrl || officialSource(rule)}
                target="_blank"
                rel="noopener noreferrer"
                className="official-source-link"
              >
                <span>공식 원문 페이지 바로가기</span>
                <ExternalLink size={14} />
              </a>
            </div>
            <p className="detail-source-disclaimer">
              본 서비스는 법령·행정규칙 변경사항을 업무 편의를 위해 정리한 참고 서비스입니다.
              실제 업무 적용 시 국가법령정보센터의 공식 원문을 확인하세요.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
