import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';
import {
  ManifestResponse,
  HealthResponse,
  RulesResponse,
  ChangesResponse,
  RuleDetailResponse,
} from '../types';

describe('Production Data Smoke Test (public/api/v1/)', () => {
  const publicDir = path.resolve(__dirname, '../../../public/api/v1');

  it('verifies manifest.json integrity and schema', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'manifest.json'), 'utf-8');
    const data: ManifestResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.2');
    expect(data.API_V1_CANDIDATE).toBe(true);
    expect(data.rule_count).toBe(68);
    expect(data.rules_url).toBe('/api/v1/rules.json');
    expect(data.health_url).toBe('/api/v1/health.json');
    expect(data.latest_changes_url).toBe('/api/v1/changes/latest.json');
    expect(data.upcoming_changes_url).toBe('/api/v1/changes/upcoming.json');
    expect(data.dataset_version).toMatch(/^ds-[a-f0-9]{64}$/);
  });

  it('verifies health.json matches current publication scope', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'health.json'), 'utf-8');
    const data: HealthResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.2');
    expect(data.status).toBe('OK');
    expect(data.health_scope).toBe('PUBLISHED_DATASET');
    expect(data.rule_count).toBe(68);
    expect(data.classification_review_count).toBeGreaterThanOrEqual(0);
    expect(data.last_successful_sync).toBeTruthy();
  });

  it('verifies rules.json contains expected 68 core rules, 66 classified, 2 review', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8');
    const data: RulesResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.2');
    expect(data.rules.length).toBe(68);

    const classified = data.rules.filter((r) => r.classification_status === 'REVIEWED');
    const review = data.rules.filter((r) => r.classification_status === 'REVIEW');

    expect(classified.length + review.length).toBe(data.rules.length);
    for (const row of review) { expect(row.business_domains).toEqual([]); expect(row.primary_domain).toBeNull(); }

    // Check all rules have official source url starting with law.go.kr
    for (const r of data.rules) {
      expect(r.official_source_url).toMatch(/^https:\/\/(www\.)?law\.go\.kr\//);
      expect(r.detail_url).toMatch(/^\/api\/v1\/rules\/(law|admrul)-\d+\.json$/);
    }
  });

  it('verifies repealed rules exist in dataset and are marked REPEALED', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules.json'), 'utf-8');
    const data: RulesResponse = JSON.parse(raw);

    const repealed = data.rules.filter((r) => r.status === 'REPEALED');
    for (const row of repealed) { expect(['폐지', '타법폐지']).toContain(row.metadata.amendment_type); }
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

    expect(data.schema_version).toBe('1.2');
    

    for (const futureEvent of data.events) {
      expect(futureEvent.effective_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(futureEvent.new_reference?.snapshot_url).toMatch(/^\/api\/v1\/rules\/.+\/versions\/.+\.json$/);
      expect(Array.isArray(futureEvent.changed_articles)).toBe(true);
    }
  });

  it('verifies rule detail JSON for law-001668 has upcoming versions and changed articles', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules/law-001668.json'), 'utf-8');
    const data: RuleDetailResponse = JSON.parse(raw);

    expect(data.schema_version).toBe('1.2');
    expect(data.rule.canonical_id).toBe('law-001668');
    expect(['CURRENT', 'REPEALED']).toContain(data.current.version_status);
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

  it('verifies at least one rule contains appendices', () => {
    const raw = fs.readFileSync(path.join(publicDir, 'rules/admrul-2046965.json'), 'utf-8');
    const data: RuleDetailResponse = JSON.parse(raw);

    expect(data.current.appendices.length).toBeGreaterThan(0);
    const firstAppendix = data.current.appendices[0];
    expect(firstAppendix.url).toMatch(/^https:\/\/(www\.)?law\.go\.kr\//);
    expect(firstAppendix.title).toBeTruthy();
  });
});
