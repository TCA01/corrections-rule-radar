import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import {
  ManifestResponse,
  HealthResponse,
  RulesResponse,
  ChangesResponse,
  RecentChangesResponse,
  RuleDetailResponse,
} from '../types';
import { isRemovedAppendix } from '../utils/format';

describe('Production Data Smoke Test (public/api/v1/)', () => {
  const publicDir = path.resolve(__dirname, '../../../public/api/v1');

  it('verifies manifest.json integrity and schema 1.5', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'manifest.json'), 'utf-8');
    const data: ManifestResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.API_V1_CANDIDATE).toBe(true);
    expect(data.rule_count).toBe(107);
    expect(data.rules_url).toBe('/api/v1/rules.json');
    expect(data.health_url).toBe('/api/v1/health.json');
    expect(data.latest_changes_url).toBe('/api/v1/changes/latest.json');
    expect(data.upcoming_changes_url).toBe('/api/v1/changes/upcoming.json');
    expect(data.recent_changes_url).toBe('/api/v1/changes/recent.json');
    expect(data.history_changes_url).toBe('/api/v1/changes/history.json');
    expect(data.dataset_version).toMatch(/^ds-[a-f0-9]{64}$/);
  });

  it('verifies health.json matches current publication scope under schema 1.5', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'health.json'), 'utf-8');
    const data: HealthResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.status).toBe('OK');
    expect(data.health_scope).toBe('PUBLISHED_DATASET');
    expect(data.rule_count).toBe(107);
    expect(data.classification_review_count).toBe(0);
    expect(data.review_count).toBe(0);
    expect(data.last_successful_sync).toBeTruthy();
  });

  it('verifies all 107 tracked rules have statuses supported by official body metadata, zero review', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8');
    const data: RulesResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.rules.length).toBe(107);

    const currentRules = data.rules.filter((r) => r.status === 'CURRENT');
    const repealedRules = data.rules.filter((r) => r.status === 'REPEALED');
    expect(currentRules.length + repealedRules.length).toBe(107);
    for (const r of data.rules) {
      expect(r.status).toBe(['폐지', '타법폐지'].includes(r.metadata.amendment_type || '') ? 'REPEALED' : 'CURRENT');
      const detail: RuleDetailResponse = JSON.parse(fs.readFileSync(path.join(publicDir, 'rules', r.canonical_id + '.json'), 'utf8'));
      expect(detail.current.metadata).toEqual(r.metadata);
      expect(detail.current.version_id).toBe(r.version_id);
    }
    expect(repealedRules.map(r=>r.canonical_id)).toEqual(expect.arrayContaining(['admrul-26424','admrul-26917']));

    const classified = data.rules.filter((r) => r.classification_status === 'REVIEWED');
    const review = data.rules.filter((r) => r.classification_status === 'REVIEW');
    expect(classified.length).toBe(107);
    expect(review.length).toBe(0);

    // Verify all rules have provenance with selection_basis and API_TRACKABLE
    for (const r of data.rules) {
      expect(r.provenance).toBeDefined();
      const prov = r.provenance as any;
      expect(prov.selection_basis).toBeTruthy();
      expect(prov.api_tracking_class).toBe('API_TRACKABLE');
      expect(['OFFICIAL_CORRECTIONS_LIST', 'DIRECT_CORRECTIONS', 'CROSS_DOMAIN_CORRECTIONS', 'HISTORICAL_REPEALED']).toContain(prov.scope_class);
    }

    // Check all rules have official source url starting with law.go.kr
    for (const r of data.rules) {
      expect(r.official_source_url).toMatch(/^https:\/\/(www\.)?law\.go\.kr\//);
      expect(r.detail_url).toMatch(/^\/api\/v1\/rules\/(law|admrul)-\d+\.json$/);
    }

    // Verify admrul-32484 and admrul-51868 have '보고' domain
    const rule32484 = data.rules.find((r) => r.canonical_id === 'admrul-32484');
    expect(rule32484).toBeDefined();
    expect(rule32484!.business_domains).toContain('보고');

    const rule51868 = data.rules.find((r) => r.canonical_id === 'admrul-51868');
    expect(rule51868).toBeDefined();
    expect(rule51868!.business_domains).toContain('보고');

    // Verify excluded rules are absent
    const excludedServ = data.rules.find((r) => r.current_name.includes('복무·징계'));
    expect(excludedServ).toBeUndefined();
    const excludedPersonnel = data.rules.find((r) => r.current_name.includes('인사운영처리지침'));
    expect(excludedPersonnel).toBeUndefined();

    // Verify newly added Phase 1F regulations are present
    expect(data.rules.some((r) => r.canonical_id === 'admrul-78303')).toBe(true); // 전문 강사 자격인정
    expect(data.rules.some((r) => r.canonical_id === 'admrul-97044')).toBe(true); // 중독재활
    expect(data.rules.some((r) => r.canonical_id === 'admrul-87003')).toBe(true); // 교도관 훈련
    expect(data.rules.some((r) => r.canonical_id === 'admrul-2036599')).toBe(true); // 교육훈련시간 (CROSS_DOMAIN)
  });

  it('verifies recent.json contains persistent 90-day changes (schema 1.5)', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'changes/recent.json'), 'utf-8');
    const data: RecentChangesResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.window_days).toBe(90);
    const history = JSON.parse(fs.readFileSync(path.join(publicDir, 'changes/history.json'), 'utf-8'));
    const publishedDay = JSON.parse(fs.readFileSync(path.join(publicDir, 'manifest.json'), 'utf-8')).published_at;
    const today = new Date(new Date(publishedDay).getTime() + 9 * 3600_000).toISOString().slice(0, 10);
    const cutoff = new Date(new Date(today).getTime() - 89 * 86400_000).toISOString().slice(0, 10);
    expect(data.events.map((e) => e.event_id)).toEqual(history.events.filter((e: any) => cutoff <= e.effective_date && e.effective_date <= today).map((e: any) => e.event_id));

    for (const evt of data.events) {
      expect(evt.event_id).toMatch(/^evt-[a-f0-9]{64}$/);
      expect(evt.canonical_id).toMatch(/^(law|admrul)-\d+$/);
      expect(evt.regulation_name).toBeTruthy();
      expect(evt.effective_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(Array.isArray(evt.changed_articles)).toBe(true);
      expect(evt.changed_article_count).toBeGreaterThanOrEqual(0);
    }
  });

  it('verifies repealed rules exist in dataset and are marked REPEALED', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8');
    const data: RulesResponse = JSON.parse(raw);

    const repealed = data.rules.filter((r) => r.status === 'REPEALED');
    for (const row of repealed) {
      expect(['폐지', '타법폐지']).toContain(row.metadata.amendment_type);
    }
  });

  it('verifies renamed/alias rules exist in dataset', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8');
    const data: RulesResponse = JSON.parse(raw);

    const withAliases = data.rules.filter((r) => {
      const aliases = new Set([...r.historical_names, ...r.seed_names]);
      aliases.delete(r.current_name);
      return aliases.size > 0;
    });

    expect(withAliases.length).toBeGreaterThanOrEqual(10);

    // Verify specific well-known alias
    const boKwan = data.rules.find((r) => r.canonical_id === 'admrul-37590');
    expect(boKwan).toBeDefined();
    if (boKwan) {
      const aliases = [...boKwan.historical_names, ...boKwan.seed_names];
      expect(aliases).toContain('영치금품 관리지침');
    }
  });

  it('verifies upcoming.json contains future-effective law event', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'changes/upcoming.json'), 'utf-8');
    const data: ChangesResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');

    for (const futureEvent of data.events) {
      expect(futureEvent.effective_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(Array.isArray(futureEvent.changed_articles)).toBe(true);
    }
  });

  it('verifies rule detail JSON for law-001668 has upcoming versions and past-effective root diffs', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules/law-001668.json'), 'utf-8');
    const data: RuleDetailResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.rule.canonical_id).toBe('law-001668');
    expect(['CURRENT', 'REPEALED']).toContain(data.current.version_status);

    // Past-effective comparison at root
    expect(Array.isArray(data.changed_articles)).toBe(true);
    expect(data.changed_articles!.length).toBeGreaterThan(0);
    expect(data.articles_compared_to).toBeDefined();

    // Upcoming versions
    for (const version of data.upcoming) {
      expect(version.version_status).toBe('FUTURE');
      expect(version.metadata.effective_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(Array.isArray(version.changed_articles)).toBe(true);
      for (const article of version.changed_articles || []) {
        expect(article.effective_date).toBe(version.metadata.effective_date);
        expect(['ADDED', 'MODIFIED', 'DELETED']).toContain(article.change_type);
      }
    }
  });

  it('verifies rule detail JSON for admrul-36283 has past-effective comparison without upcoming', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules/admrul-36283.json'), 'utf-8');
    const data: RuleDetailResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.5');
    expect(data.upcoming.length).toBe(0);
    expect(Array.isArray(data.changed_articles)).toBe(true);
    expect(data.changed_articles!.length).toBe(71);
    expect(data.articles_compared_to?.version_id).toBe('2100000236340');
  });

  it('verifies at least one rule contains appendices', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules/admrul-2046965.json'), 'utf-8');
    const data: RuleDetailResponse = JSON.parse(raw);

    expect(data.current.appendices.length).toBeGreaterThan(0);
    const firstAppendix = data.current.appendices[0];
    expect(firstAppendix.url).toMatch(/^https:\/\/(www\.)?law\.go\.kr\//);
    expect(firstAppendix.title).toBeTruthy();
  });

  it('verifies real deleted appendices in production data are correctly detected by isRemovedAppendix (Web W3.1a)', () => {
    // 1. admrul-34791: sequence 0003, 0005 (title: '삭제', has historical download url)
    const raw34791 = fs.readFileSync(path.join(publicDir, 'rules/admrul-34791.json'), 'utf-8');
    const data34791: RuleDetailResponse = JSON.parse(raw34791);
    const app34791_0003 = data34791.current.appendices.find((a) => a.sequence === '0003');
    expect(app34791_0003).toBeDefined();
    expect(app34791_0003!.title).toBe('삭제');
    expect(app34791_0003!.url).toMatch(/flDownload\.do/);
    expect(isRemovedAppendix(app34791_0003)).toBe(true);

    const app34791_0005 = data34791.current.appendices.find((a) => a.sequence === '0005');
    expect(app34791_0005).toBeDefined();
    expect(app34791_0005!.title).toBe('삭제');
    expect(isRemovedAppendix(app34791_0005)).toBe(true);

    // 2. admrul-36282: sequence 0008 (title: '삭제', has historical download url)
    const raw36282 = fs.readFileSync(path.join(publicDir, 'rules/admrul-36282.json'), 'utf-8');
    const data36282: RuleDetailResponse = JSON.parse(raw36282);
    const app36282_0008 = data36282.current.appendices.find((a) => a.sequence === '0008');
    expect(app36282_0008).toBeDefined();
    expect(app36282_0008!.title).toBe('삭제');
    expect(app36282_0008!.url).toMatch(/flDownload\.do/);
    expect(isRemovedAppendix(app36282_0008)).toBe(true);

    // 3. admrul-37584: sequence 0005 (title: '삭제', has historical download url)
    const raw37584 = fs.readFileSync(path.join(publicDir, 'rules/admrul-37584.json'), 'utf-8');
    const data37584: RuleDetailResponse = JSON.parse(raw37584);
    const app37584_0005 = data37584.current.appendices.find((a) => a.sequence === '0005');
    expect(app37584_0005).toBeDefined();
    expect(app37584_0005!.title).toBe('삭제');
    expect(app37584_0005!.url).toMatch(/flDownload\.do/);
    expect(isRemovedAppendix(app37584_0005)).toBe(true);

    // 4. law-002049: sequence 0004 (title: '삭제 <2016.1.22.>' / '삭제 &lt;2016.1.22.&gt;', has historical download url)
    const raw2049 = fs.readFileSync(path.join(publicDir, 'rules/law-002049.json'), 'utf-8');
    const data2049: RuleDetailResponse = JSON.parse(raw2049);
    const app2049_0004 = data2049.current.appendices.find((a) => a.sequence === '0004');
    expect(app2049_0004).toBeDefined();
    expect(app2049_0004!.title).toMatch(/^삭제/);
    expect(app2049_0004!.url).toMatch(/flDownload\.do/);
    expect(isRemovedAppendix(app2049_0004)).toBe(true);

    // 5. Active downloadable appendix: admrul-2046965 sequence 0001 (별지 수형자 분류처우심사표)
    const raw2046965 = fs.readFileSync(path.join(publicDir, 'rules/admrul-2046965.json'), 'utf-8');
    const data2046965: RuleDetailResponse = JSON.parse(raw2046965);
    const appActive = data2046965.current.appendices.find(
      (a) => a.sequence === '0001' && a.type === '별지'
    );
    expect(appActive).toBeDefined();
    expect(appActive!.title).toBe('수형자 분류처우심사표');
    expect(appActive!.url).toMatch(/flDownload\.do/);
    expect(isRemovedAppendix(appActive)).toBe(false);
  });
});
