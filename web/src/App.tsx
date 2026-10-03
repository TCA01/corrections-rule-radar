import React, { useEffect, useState, useMemo } from 'react';
import {
  RuleSummary,
  HealthResponse,
  ChangesResponse,
  BusinessDomain,
  CONTROLLED_DOMAINS,
  DisplayChangeEvent,
} from './types';
import { api, ApiError } from './services/api';
import { calculateDDay, isSameDay, isWithinPastDays } from './utils/date';
import { getChangeTypeLabel, getFactualDescription } from './utils/format';
import { Header } from './components/Header';
import { SummaryCards } from './components/SummaryCards';
import { DomainSelector } from './components/DomainSelector';
import { ChangeFeed } from './components/ChangeFeed';
import { UpcomingTimeline } from './components/UpcomingTimeline';
import { RegulationDirectory } from './components/RegulationDirectory';
import { RuleDetailModal } from './components/RuleDetailModal';
import { DemoHighlight } from './components/DemoHighlight';
import { NoticeFooter } from './components/NoticeFooter';
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react';

const STORAGE_KEY_DOMAINS = 'corrections_rule_radar_domains';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rules, setRules] = useState<RuleSummary[]>([]);
  const [upcomingChanges, setUpcomingChanges] = useState<ChangesResponse | null>(null);
  const [latestChanges, setLatestChanges] = useState<ChangesResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected business domains (stored in localStorage)
  const [selectedDomains, setSelectedDomains] = useState<BusinessDomain[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_DOMAINS);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return parsed.filter((d: string) =>
            (CONTROLLED_DOMAINS as readonly string[]).includes(d)
          ) as BusinessDomain[];
        }
      }
    } catch {
      // fallback
    }
    return [];
  });

  // Active rule for detail view modal
  const [activeRule, setActiveRule] = useState<RuleSummary | null>(null);

  // Save selected domains to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_DOMAINS, JSON.stringify(selectedDomains));
    } catch {
      // ignore storage errors
    }
  }, [selectedDomains]);

  // Load initial dataset
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [manifestData, healthData, rulesData, upcomingData, latestData] = await Promise.all([
        api.getManifest(),
        api.getHealth().catch(() => null),
        api.getRules(),
        api.getUpcomingChanges().catch(() => ({ schema_version: '1.2', dataset_version: '', events: [] })),
        api.getLatestChanges().catch(() => ({ schema_version: '1.2', dataset_version: '', events: [] })),
      ]);

      if ([healthData, rulesData, upcomingData, latestData].some(data =>
        data?.dataset_version && data.dataset_version !== manifestData.dataset_version
      )) throw new ApiError('데이터 버전이 갱신 중입니다. 잠시 후 다시 시도하세요.');
      setHealth(healthData);
      setRules(rulesData.rules);
      setUpcomingChanges(upcomingData);
      setLatestChanges(latestData);
      setLoading(false);
    } catch (err: unknown) {
      const msg =
        err instanceof ApiError
          ? `데이터를 불러올 수 없습니다: ${err.message}`
          : '데이터를 불러오는 중 예기치 못한 오류가 발생했습니다.';
      setError(msg);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Quick lookup map of rules by canonical_id
  const ruleMap = useMemo(() => {
    const map = new Map<string, RuleSummary>();
    for (const r of rules) {
      map.set(r.canonical_id, r);
    }
    return map;
  }, [rules]);

  // Domain rule counts
  const domainCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of CONTROLLED_DOMAINS) {
      counts[d] = 0;
    }
    for (const r of rules) {
      for (const d of r.business_domains) {
        counts[d] = (counts[d] || 0) + 1;
      }
    }
    return counts;
  }, [rules]);

  // Convert upcoming changes to display view models
  const upcomingEvents: DisplayChangeEvent[] = useMemo(() => {
    if (!upcomingChanges || !upcomingChanges.events) return [];

    return upcomingChanges.events
      .map<DisplayChangeEvent | null>((evt) => {
        const rule = ruleMap.get(evt.canonical_id);
        if (!rule) return null;

        const effectiveDate = evt.effective_date || rule.metadata.effective_date;
        const dDayInfo = calculateDDay(effectiveDate);

        return {
          id: evt.event_id,
          canonical_id: evt.canonical_id,
          rule_name: rule.current_name,
          corrections_category: rule.corrections_category,
          business_domains: rule.business_domains,
          classification_status: rule.classification_status,
          change_type: evt.change_type,
          change_type_label: getChangeTypeLabel(evt.change_type),
          detected_at: evt.detected_at,
          effective_date: effectiveDate,
          d_day: dDayInfo.dDay,
          department: rule.metadata.department,
          factual_description: getFactualDescription(evt.change_type, effectiveDate),
          official_source_url: evt.official_source_url || rule.official_source_url,
          is_upcoming: true,
          is_today: dDayInfo.dDay === 0,
          status: rule.status,
          rule_summary: rule,
        };
      })
      .filter((e): e is DisplayChangeEvent => e !== null)
      .sort((a, b) => {
        // Sort by effective date ascending
        const dateA = a.effective_date || '';
        const dateB = b.effective_date || '';
        return dateA.localeCompare(dateB);
      });
  }, [upcomingChanges, ruleMap]);

  // Recent changes:
  // Combines events from latest.json with rules from rules.json that took effect recently (last 30-60 days)
  const recentEvents: DisplayChangeEvent[] = useMemo(() => {
    const list: DisplayChangeEvent[] = [];
    const seenRules = new Set<string>();

    // 1. From latestChanges events
    if (latestChanges && latestChanges.events) {
      for (const evt of latestChanges.events) {
        const rule = ruleMap.get(evt.canonical_id);
        if (!rule) continue;
        seenRules.add(rule.canonical_id);
        const effDate = evt.effective_date || rule.metadata.effective_date;
        const dDayInfo = calculateDDay(effDate);

        list.push({
          id: evt.event_id,
          canonical_id: evt.canonical_id,
          rule_name: rule.current_name,
          corrections_category: rule.corrections_category,
          business_domains: rule.business_domains,
          classification_status: rule.classification_status,
          change_type: evt.change_type,
          change_type_label: getChangeTypeLabel(evt.change_type),
          detected_at: evt.detected_at,
          effective_date: effDate,
          d_day: dDayInfo.dDay,
          department: rule.metadata.department,
          factual_description: getFactualDescription(evt.change_type, effDate),
          official_source_url: evt.official_source_url || rule.official_source_url,
          is_upcoming: false,
          is_today: dDayInfo.dDay === 0,
          status: rule.status,
          rule_summary: rule,
        });
      }
    }

    // 2. From recent rules in rules.json
    for (const rule of rules) {
      if (seenRules.has(rule.canonical_id)) continue;
      if (rule.status === 'REPEALED') continue;
      const effDate = rule.metadata.effective_date;
      if (!effDate) continue;

      const dDayInfo = calculateDDay(effDate);
      // If effective date is within past 45 days or today
      if (isWithinPastDays(effDate, 45) || dDayInfo.dDay === 0) {
        list.push({
          id: `rule-recent-${rule.canonical_id}`,
          canonical_id: rule.canonical_id,
          rule_name: rule.current_name,
          corrections_category: rule.corrections_category,
          business_domains: rule.business_domains,
          classification_status: rule.classification_status,
          change_type: 'RULE_AMENDED',
          change_type_label: rule.metadata.amendment_type || '규정 개정',
          detected_at: null,
          effective_date: effDate,
          d_day: dDayInfo.dDay,
          department: rule.metadata.department,
          factual_description: `${effDate} 시행: ${
            rule.metadata.amendment_type || '개정'
          } 조문이 적용되었습니다.`,
          official_source_url: rule.official_source_url,
          is_upcoming: false,
          is_today: dDayInfo.dDay === 0,
          status: rule.status,
          rule_summary: rule,
        });
      }
    }

    // Sort descending by effective date
    return list.sort((a, b) => {
      const dateA = a.effective_date || '';
      const dateB = b.effective_date || '';
      return dateB.localeCompare(dateA);
    });
  }, [latestChanges, rules, ruleMap]);

  // Today effective events: items with d_day === 0
  const todayEvents = useMemo(() => {
    const list: DisplayChangeEvent[] = [];
    for (const e of [...upcomingEvents, ...recentEvents]) {
      if (e.d_day === 0) {
        list.push(e);
      }
    }
    // Also check all rules
    for (const r of rules) {
      if (r.metadata.effective_date && isSameDay(r.metadata.effective_date)) {
        if (!list.some((e) => e.canonical_id === r.canonical_id)) {
          list.push({
            id: `today-${r.canonical_id}`,
            canonical_id: r.canonical_id,
            rule_name: r.current_name,
            corrections_category: r.corrections_category,
            business_domains: r.business_domains,
            classification_status: r.classification_status,
            change_type: 'RULE_AMENDED',
            change_type_label: '오늘 시행',
            detected_at: null,
            effective_date: r.metadata.effective_date,
            d_day: 0,
            department: r.metadata.department,
            factual_description: '오늘부터 시행되는 규정입니다.',
            official_source_url: r.official_source_url,
            is_upcoming: false,
            is_today: true,
            status: r.status,
            rule_summary: r,
          });
        }
      }
    }
    return list;
  }, [upcomingEvents, recentEvents, rules]);

  // Dynamic summary card counts
  const summaryCounts = useMemo(() => {
    const todayCount = todayEvents.length;

    // Upcoming within 30 days
    const upcoming30Count = upcomingEvents.filter(
      (e) => e.d_day !== null && e.d_day > 0 && e.d_day <= 30
    ).length;

    // Recent within 30 days
    const recent30Count = recentEvents.filter((e) => {
      if (!e.effective_date) return false;
      return isWithinPastDays(e.effective_date, 30);
    }).length;

    const totalTrackedCount = rules.length;

    return {
      todayCount,
      upcoming30Count,
      recent30Count,
      totalTrackedCount,
    };
  }, [todayEvents, upcomingEvents, recentEvents, rules]);

  // Filter events based on selected business domains
  const filterBySelectedDomains = (eventList: DisplayChangeEvent[]) => {
    if (selectedDomains.length === 0) return eventList;
    return eventList.filter((evt) => {
      // Check if any business domain matches
      const hasDomainMatch = evt.business_domains.some((d) => selectedDomains.includes(d));
      return hasDomainMatch;
    });
  };

  const domainFilteredUpcoming = useMemo(
    () => filterBySelectedDomains(upcomingEvents),
    [upcomingEvents, selectedDomains]
  );

  const domainFilteredRecent = useMemo(
    () => filterBySelectedDomains(recentEvents),
    [recentEvents, selectedDomains]
  );

  const domainFilteredToday = useMemo(
    () => filterBySelectedDomains(todayEvents),
    [todayEvents, selectedDomains]
  );

  // Toggle domain in multi-select
  const handleToggleDomain = (domain: BusinessDomain) => {
    setSelectedDomains((prev) =>
      prev.includes(domain) ? prev.filter((d) => d !== domain) : [...prev, domain]
    );
  };

  const handleSelectAllDomains = () => {
    setSelectedDomains([...CONTROLLED_DOMAINS]);
  };

  const handleClearAllDomains = () => {
    setSelectedDomains([]);
  };

  // Demo selection: Law-001668 (future effective law) or first upcoming or first recent
  const demoTargetUpcoming = upcomingEvents.length > 0 ? upcomingEvents[0] : null;
  const demoTargetRule =
    rules.find((r) => r.canonical_id === 'law-001668') ||
    rules.find((r) => r.metadata.effective_date && r.metadata.effective_date.startsWith('2026-10')) ||
    rules[0] ||
    null;

  const handleOpenDemo = () => {
    if (demoTargetRule) {
      setActiveRule(demoTargetRule);
    }
  };

  return (
    <div className="app-root">
      <Header health={health} onOpenDemo={handleOpenDemo} />

      <main className="container" role="main" style={{ paddingBottom: '3rem' }}>
        {/* Loading State */}
        {loading && (
          <div
            style={{
              padding: '4rem 1rem',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
            }}
          >
            <Loader2 className="animate-spin" size={32} color="var(--color-primary-light)" />
            <p style={{ fontSize: '1rem', color: 'var(--color-text-muted)' }}>
              교정업무 규정 데이터(API v1)를 불러오고 있습니다...
            </p>
          </div>
        )}

        {/* Global Error State */}
        {error && !loading && (
          <div
            className="empty-state"
            style={{
              borderColor: '#fca5a5',
              backgroundColor: '#fff1f2',
              marginTop: '2rem',
              padding: '2.5rem',
            }}
            role="alert"
          >
            <AlertCircle size={32} color="#e11d48" style={{ margin: '0 auto 0.75rem' }} />
            <h2 style={{ fontSize: '1.125rem', color: '#9f1239', fontWeight: 700 }}>
              데이터를 불러오지 못했습니다
            </h2>
            <p style={{ color: '#be123c', maxWidth: '500px', margin: '0.5rem auto 1.5rem' }}>
              {error}
            </p>
            <button
              type="button"
              className="btn-detail"
              onClick={loadData}
              style={{ backgroundColor: '#be123c', color: 'white', borderColor: '#9f1239' }}
            >
              <RefreshCw size={14} style={{ marginRight: 6 }} />
              <span>다시 시도하기</span>
            </button>
          </div>
        )}

        {/* Normal Content */}
        {!loading && !error && (
          <>
            {/* Summary Cards */}
            <SummaryCards
              todayCount={summaryCounts.todayCount}
              upcoming30Count={summaryCounts.upcoming30Count}
              recent30Count={summaryCounts.recent30Count}
              totalTrackedCount={summaryCounts.totalTrackedCount}
            />

            {/* 30-Second Demo Highlight */}
            <DemoHighlight
              upcomingEvent={demoTargetUpcoming}
              latestRule={demoTargetRule}
              onOpenDetail={(rule) => setActiveRule(rule)}
            />

            {/* Business Domain Selector */}
            <DomainSelector
              selectedDomains={selectedDomains}
              onToggleDomain={handleToggleDomain}
              onSelectAll={handleSelectAllDomains}
              onClearAll={handleClearAllDomains}
              domainCounts={domainCounts}
            />

            {/* Priority A: 오늘 시행 */}
            {domainFilteredToday.length > 0 && (
              <ChangeFeed
                title="오늘 시행"
                badgeText={`${domainFilteredToday.length}건`}
                events={domainFilteredToday}
                onSelectEvent={(evt) => setActiveRule(evt.rule_summary)}
                featuredStyle="today"
              />
            )}

            {/* Priority B: 시행 예정 규정 타임라인 */}
            <UpcomingTimeline
              events={domainFilteredUpcoming}
              onSelectEvent={(evt) => setActiveRule(evt.rule_summary)}
            />

            {/* Priority C: 최근 변경 */}
            <ChangeFeed
              title="최근 규정 변경 사항"
              badgeText={`${domainFilteredRecent.length}건`}
              events={domainFilteredRecent}
              emptyMessage={
                selectedDomains.length > 0
                  ? '선택하신 업무 분야에 해당하는 최근 45일 내 규정 변경 내역이 없습니다.'
                  : '최근 변경 내역이 없습니다.'
              }
              onSelectEvent={(evt) => setActiveRule(evt.rule_summary)}
              featuredStyle="recent"
            />

            {/* Regulation Directory */}
            <RegulationDirectory
              rules={rules}
              onSelectRule={(rule) => setActiveRule(rule)}
            />
          </>
        )}
      </main>

      {/* Rule Detail Modal */}
      {activeRule && (
        <RuleDetailModal
          rule={activeRule}
          onClose={() => setActiveRule(null)}
        />
      )}

      {/* Trust & Source Notice Footer */}
      <NoticeFooter />
    </div>
  );
};

export default App;
