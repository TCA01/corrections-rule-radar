import React, { useEffect, useState, useMemo } from 'react';
import {
  RuleSummary,
  HealthResponse,
  ChangesResponse,
  RecentChangesResponse,
  PersistentChangeEvent,
  BusinessDomain,
  CONTROLLED_DOMAINS,
  DisplayChangeEvent,
} from './types';
import { api, ApiError } from './services/api';
import { calculateDDay, isSameDay } from './utils/date';
import { getChangeTypeLabel, getFactualDescription } from './utils/format';
import { Header } from './components/Header';
import { GlobalSearch } from './components/GlobalSearch';
import { SummaryCards } from './components/SummaryCards';
import { DomainSelector } from './components/DomainSelector';
import { ChangeFeed } from './components/ChangeFeed';
import { UpcomingTimeline } from './components/UpcomingTimeline';
import { RecentChangesSection } from './components/RecentChangesSection';
import { RegulationDirectory } from './components/RegulationDirectory';
import { RuleDetailModal } from './components/RuleDetailModal';
import { NoticeFooter } from './components/NoticeFooter';
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react';

const STORAGE_KEY_DOMAINS = 'corrections_rule_tracker_domains';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [rules, setRules] = useState<RuleSummary[]>([]);
  const [upcomingChanges, setUpcomingChanges] = useState<ChangesResponse | null>(null);
  const [recentChanges, setRecentChanges] = useState<RecentChangesResponse | null>(null);
  const [, setLatestChanges] = useState<ChangesResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected business domains (stored in localStorage)
  const [selectedDomains, setSelectedDomains] = useState<BusinessDomain[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_DOMAINS) || localStorage.getItem('corrections_rule_radar_domains');
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

  // Active rule and change event for detail view modal
  const [activeRule, setActiveRule] = useState<RuleSummary | null>(null);
  const [activeChangeEvent, setActiveChangeEvent] = useState<PersistentChangeEvent | null>(null);
  const [activeUpcomingDate, setActiveUpcomingDate] = useState<string | null>(null);

  // Save selected domains to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_DOMAINS, JSON.stringify(selectedDomains));
      localStorage.setItem('corrections_rule_radar_domains', JSON.stringify(selectedDomains));
    } catch {
      // ignore storage errors
    }
  }, [selectedDomains]);

  // Load initial dataset (Schema 1.5)
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [manifestData, healthData, rulesData, upcomingData, recentData, latestData] = await Promise.all([
        api.getManifest(),
        api.getHealth().catch(() => null),
        api.getRules(),
        api.getUpcomingChanges().catch(() => ({ schema_version: '1.5', dataset_version: '', events: [] })),
        api.getRecentChanges().catch(() => ({ schema_version: '1.5', dataset_version: '', window_days: 90, date_basis: '', events: [] })),
        api.getLatestChanges().catch(() => ({ schema_version: '1.5', dataset_version: '', events: [] })),
      ]);

      if (manifestData.schema_version !== '1.5') {
        throw new ApiError(`지원되지 않는 스키마 버전입니다: ${manifestData.schema_version} (요구 버전: 1.5)`);
      }

      if (
        [healthData, rulesData, upcomingData, recentData, latestData].some(
          (data) => data?.dataset_version && data.dataset_version !== manifestData.dataset_version
        )
      ) {
        throw new ApiError('데이터 버전이 갱신 중입니다. 잠시 후 다시 시도하세요.');
      }

      setHealth(healthData);
      setRules(rulesData.rules);
      setUpcomingChanges(upcomingData);
      setRecentChanges(recentData);
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
        const dateA = a.effective_date || '';
        const dateB = b.effective_date || '';
        return dateA.localeCompare(dateB);
      });
  }, [upcomingChanges, ruleMap]);

  // Today effective events
  const todayEvents = useMemo(() => {
    const list: DisplayChangeEvent[] = [];
    for (const e of upcomingEvents) {
      if (e.d_day === 0) {
        list.push(e);
      }
    }
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
  }, [upcomingEvents, rules]);

  // Dynamic summary counts (Section 9: 오늘 시행, 30일 내 시행예정, 최근 90일 변경, 추적 규정)
  const summaryCounts = useMemo(() => {
    const todayCount = todayEvents.length;
    const upcoming30Count = upcomingEvents.filter(
      (e) => e.d_day !== null && e.d_day > 0 && e.d_day <= 30
    ).length;
    const recent90Count = recentChanges?.events?.length || 0;
    const totalTrackedCount = rules.length;

    return {
      todayCount,
      upcoming30Count,
      recent90Count,
      totalTrackedCount,
    };
  }, [todayEvents, upcomingEvents, recentChanges, rules]);

  // Filter events based on selected business domains
  const filterBySelectedDomains = (eventList: DisplayChangeEvent[]) => {
    if (selectedDomains.length === 0) return eventList;
    return eventList.filter((evt) => {
      return evt.business_domains.some((d) => selectedDomains.includes(d));
    });
  };

  const domainFilteredUpcoming = useMemo(
    () => filterBySelectedDomains(upcomingEvents),
    [upcomingEvents, selectedDomains]
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

  return (
    <div className="app-root">
      {/* 1. Header (Product title: 교정관련 규정 추적기, last sync) */}
      <Header health={health} />

      <main className="container" role="main" style={{ paddingBottom: '4rem' }}>
        {/* Loading State */}
        {loading && (
          <div className="main-loading-state">
            <Loader2 className="animate-spin" size={32} />
            <p>교정관련 규정 데이터(API v1)를 불러오고 있습니다...</p>
          </div>
        )}

        {/* Global Error State */}
        {error && !loading && (
          <div className="empty-state error" role="alert">
            <AlertCircle size={32} color="#e11d48" style={{ margin: '0 auto 0.75rem' }} />
            <h2 style={{ fontSize: '1.125rem', color: '#9f1239', fontWeight: 700 }}>
              데이터를 불러오지 못했습니다
            </h2>
            <p style={{ color: '#be123c', maxWidth: '500px', margin: '0.5rem auto 1.5rem' }}>
              {error}
            </p>
            <button
              type="button"
              className="btn-retry"
              onClick={loadData}
            >
              <RefreshCw size={14} style={{ marginRight: 6 }} />
              <span>다시 시도하기</span>
            </button>
          </div>
        )}

        {/* Normal Content: Page Order from Section 7 */}
        {!loading && !error && (
          <>
            {/* 2. GLOBAL SEARCH (Prominent, immediately below header) */}
            <GlobalSearch
              rules={rules}
              onSelectRule={(rule) => {
                setActiveChangeEvent(null);
                setActiveUpcomingDate(null);
                setActiveRule(rule);
              }}
            />

            {/* 3. EDITORIAL SUMMARY BAND (오늘 시행 / 30일 내 시행예정 / 최근 90일 변경 / 추적 규정) */}
            <SummaryCards
              todayCount={summaryCounts.todayCount}
              upcoming30Count={summaryCounts.upcoming30Count}
              recent90Count={summaryCounts.recent90Count}
              totalTrackedCount={summaryCounts.totalTrackedCount}
            />

            {/* 4. MY BUSINESS DOMAINS (VoiceBox Civic Segmented Filter Panel) */}
            <DomainSelector
              selectedDomains={selectedDomains}
              onToggleDomain={handleToggleDomain}
              onSelectAll={handleSelectAllDomains}
              onClearAll={handleClearAllDomains}
              domainCounts={domainCounts}
            />

            {/* 5. TODAY / UPCOMING */}
            {domainFilteredToday.length > 0 && (
              <ChangeFeed
                title="오늘 시행"
                badgeText={`${domainFilteredToday.length}건`}
                events={domainFilteredToday}
                onSelectEvent={(evt) => {
                  setActiveChangeEvent(null);
                  setActiveUpcomingDate(null);
                  setActiveRule(evt.rule_summary);
                }}
                featuredStyle="today"
              />
            )}

            <UpcomingTimeline
              events={domainFilteredUpcoming}
              onSelectEvent={(evt) => {
                setActiveChangeEvent(null);
                setActiveUpcomingDate(evt.effective_date);
                setActiveRule(evt.rule_summary);
              }}
            />

            {/* 6. RECENT 90-DAY CHANGES (Dedicated Persistent Change-History Section) */}
            <RecentChangesSection
              events={recentChanges?.events || []}
              ruleMap={ruleMap}
              selectedDomains={selectedDomains}
              onSelectEvent={(evt, rule) => {
                setActiveChangeEvent(evt);
                setActiveUpcomingDate(null);
                setActiveRule(rule || null);
              }}
            />

            {/* 7. ALL REGULATIONS DIRECTORY */}
            <RegulationDirectory
              rules={rules}
              onSelectRule={(rule) => {
                setActiveChangeEvent(null);
                setActiveUpcomingDate(null);
                setActiveRule(rule);
              }}
            />
          </>
        )}
      </main>

      {/* Rule Detail Modal */}
      {activeRule && (
        <RuleDetailModal
          rule={activeRule}
          initialEvent={activeChangeEvent}
          initialEffectiveDate={activeUpcomingDate}
          onClose={() => {
            setActiveRule(null);
            setActiveChangeEvent(null);
            setActiveUpcomingDate(null);
          }}
        />
      )}

      {/* 8. Trust & Source Notice Footer */}
      <NoticeFooter />
    </div>
  );
};

export default App;
