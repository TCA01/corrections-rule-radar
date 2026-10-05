import {
  ManifestResponse,
  RulesResponse,
  HealthResponse,
  ChangesResponse,
  RecentChangesResponse,
  PersistentChangeEvent,
  RuleDetailResponse,
  RuleVersionDetail,
} from '../types';
import { needsStructuredComparison, resolveVisualComparison, VisualComparison } from './comparison';

export class ApiError extends Error {
  status?: number;
  url?: string;
  constructor(message: string, status?: number, url?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
  }
}

function resolveApiUrl(path: string): string {
  const baseUrl = import.meta.env.BASE_URL || '/';
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

async function fetchJson<T>(path: string): Promise<T> {
  const url = resolveApiUrl(path);
  try {
    const response = await fetch(url, {
      cache: 'no-cache',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new ApiError(
        `Failed to fetch ${url} (status: ${response.status} ${response.statusText})`,
        response.status,
        url
      );
    }

    const data = await response.json();
    return data as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : String(err);
    throw new ApiError(`Network error while fetching ${url}: ${message}`, undefined, url);
  }
}

export const api = {
  async getVisualComparison(event: PersistentChangeEvent): Promise<VisualComparison> {
    if (!needsStructuredComparison(event)) return { articles: event.changed_articles, textSource: 'EVENT_TEXT' };
    try {
      const refs = [event.before_version, event.after_version];
      for (const ref of refs) {
        if (!ref?.snapshot_url || !new RegExp(`^/api/v1/rules/${event.canonical_id}/versions/\\d+-\\d{4}-\\d{2}-\\d{2}-[a-f0-9]{16}\\.json$`).test(ref.snapshot_url)) {
          throw new Error('COMPARISON_REFERENCES_UNAVAILABLE');
        }
      }
      const [before, after] = await Promise.all(refs.map(ref => fetchJson<{ version: RuleVersionDetail }>(ref!.snapshot_url!)));
      return resolveVisualComparison(event, before.version, after.version);
    } catch {
      // Fail closed: comparative shorthand is never passed to a legal word diff.
      return { articles: [], textSource: 'UNAVAILABLE' };
    }
  },
  getManifest(): Promise<ManifestResponse> {
    return fetchJson<ManifestResponse>('/api/v1/manifest.json');
  },

  getRules(): Promise<RulesResponse> {
    return fetchJson<RulesResponse>('/api/v1/rules.json');
  },

  getHealth(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>('/api/v1/health.json');
  },

  getLatestChanges(): Promise<ChangesResponse> {
    return fetchJson<ChangesResponse>('/api/v1/changes/latest.json');
  },

  getUpcomingChanges(): Promise<ChangesResponse> {
    return fetchJson<ChangesResponse>('/api/v1/changes/upcoming.json');
  },

  getRecentChanges(): Promise<RecentChangesResponse> {
    return fetchJson<RecentChangesResponse>('/api/v1/changes/recent.json');
  },

  getHistoryChanges(): Promise<RecentChangesResponse> {
    return fetchJson<RecentChangesResponse>('/api/v1/changes/history.json');
  },

  getChangeEvent(eventId: string): Promise<PersistentChangeEvent> {
    return fetchJson<PersistentChangeEvent>(`/api/v1/changes/${eventId}.json`);
  },

  getRuleDetail(canonicalId: string): Promise<RuleDetailResponse> {
    return fetchJson<RuleDetailResponse>(`/api/v1/rules/${canonicalId}.json`);
  },
};
