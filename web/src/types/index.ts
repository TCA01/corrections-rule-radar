export const CONTROLLED_DOMAINS = [
  '수용·보안',
  '접견·외부교통',
  '보관금품',
  '분류·가석방',
  '교육·교화',
  '작업·직업훈련',
  '급식·복지',
  '의료',
  '심리치료',
  '인권·청원',
  '민원',
  '인사·조직',
  '정보화',
  '민영교도소',
  '보고',
  '기타',
] as const;

export type BusinessDomain = typeof CONTROLLED_DOMAINS[number];

export type CorrectionsCategory = '법률' | '대통령령' | '법무부령' | '예규' | '훈령' | '지침';
export type RuleStatus = 'CURRENT' | 'REPEALED' | 'REVIEW';
export type ClassificationStatus = 'REVIEW' | 'REVIEWED';
export type SourceKind = 'law' | 'admrul';

export type ScopeClass =
  | 'OFFICIAL_CORRECTIONS_LIST'
  | 'DIRECT_CORRECTIONS'
  | 'CROSS_DOMAIN_CORRECTIONS'
  | 'HISTORICAL_REPEALED';

export interface RuleProvenance {
  scope_class?: ScopeClass;
  selection_basis?: string;
  applies_to?: string[];
  official_seed_name?: string | null;
  official_seed_url?: string | null;
  canonical_source_url?: string;
  discovery_source?: string[];
  scope_review_status?: string;
  api_tracking_class?: 'API_TRACKABLE';
  structured_body_source?: string;
  history_source?: string;
  appendix_metadata_source?: string;
}

export type ChangeType =
  | 'NEW_RULE'
  | 'RULE_RENAMED'
  | 'RULE_AMENDED'
  | 'FUTURE_EFFECTIVE_VERSION'
  | 'EFFECTIVE_DATE_CHANGED'
  | 'ARTICLE_CHANGED'
  | 'APPENDIX_CHANGED'
  | 'ATTACHMENT_CHANGED'
  | 'RULE_REPEALED'
  | 'RULE_REMOVED_FROM_CORRECTIONS_SEED'
  | 'NEW_CORRECTIONS_SEED'
  | 'DISCOVERY_CANDIDATE';

export interface RuleMetadata {
  name: string;
  rule_type: string | null;
  issue_date: string | null;
  issue_number: string | null;
  effective_date: string | null;
  ministry: string | null;
  department: string | null;
  amendment_type: string | null;
  official_state: string | null;
}

export interface RuleSummary {
  canonical_id: string;
  source_kind: SourceKind;
  current_name: string;
  seed_names: string[];
  historical_names: string[];
  corrections_category: CorrectionsCategory;
  business_domains: BusinessDomain[];
  classification_status: ClassificationStatus;
  primary_domain: BusinessDomain | null;
  secondary_domains: BusinessDomain[];
  status: RuleStatus;
  version_id: string;
  metadata: RuleMetadata;
  official_source_url: string;
  detail_url: string;
  domain_assignment_status?: string;
  provenance?: RuleProvenance | string | null;
  selection_rationale?: string | null;
}

export interface RulesResponse {
  schema_version: string;
  dataset_version: string;
  rules: RuleSummary[];
}

export interface ManifestResponse {
  API_V1_CANDIDATE: boolean;
  dataset_version: string;
  published_at: string;
  rule_count: number;
  rules_url: string;
  schema_version: string;
  health_url: string;
  latest_changes_url: string;
  upcoming_changes_url: string;
  recent_changes_url?: string;
  history_changes_url?: string;
  change_detail_url_template?: string;
}

export interface HealthResponse {
  schema_version: string;
  dataset_version: string;
  health_scope: string;
  publication_status: string;
  status: 'OK' | 'DEGRADED' | 'ERROR' | string;
  rule_count: number;
  review_count: number;
  classification_review_count: number;
  last_successful_sync: string;
}

export interface VersionReference {
  version_id: string;
  effective_date: string | null;
  snapshot_url: string;
  official_source_url: string;
  identifier?: string;
  body_hash?: string;
}

export interface PersistentVersionInfo {
  version_id?: string;
  identifier?: string;
  effective_date?: string | null;
  official_source_url?: string;
  snapshot_url?: string;
  body_hash?: string;
}

export interface PersistentAppendixChange {
  change_type: string;
  status: 'AVAILABLE' | 'REMOVED' | string;
  before_metadata?: AppendixItem | null;
  after_metadata?: AppendixItem | null;
}

export interface PersistentChangeEvent {
  event_id: string;
  canonical_id: string;
  regulation_name: string;
  regulation_type: string;
  effective_date: string | null;
  promulgation_or_issue_date?: string | null;
  detected_at: string;
  change_type: ChangeType | string;
  change_types?: string[];
  changed_article_count: number;
  changed_articles: ChangedArticle[];
  before_version?: PersistentVersionInfo | null;
  after_version?: PersistentVersionInfo | null;
  comparison_status?: string;
  comparison_source?: string;
  comparison_scope?: string;
  comparison_unavailable_reason?: string | null;
  fallback_reason?: string | null;
  official_old_new_available?: boolean;
  official_source_url: string;
  appendix_changes?: PersistentAppendixChange[];
}

export interface RecentChangesResponse {
  schema_version: string;
  dataset_version: string;
  window_days: number;
  date_basis: string;
  events: PersistentChangeEvent[];
}

export interface ChangeEvent extends Partial<PersistentChangeEvent> {
  changed_articles?: ChangedArticle[];
  articles_compared_to?: VersionReference | null;
  event_id: string;
  canonical_id: string;
  change_type: ChangeType;
  detected_at: string;
  effective_date: string | null;
  official_source_url: string;
  new_version?: string | null;
  old_version?: string | null;
  new_reference?: VersionReference | null;
  old_reference?: VersionReference | null;
  evidence?: Record<string, unknown> | null;
  new_hashes?: Record<string, string> | null;
  old_hashes?: Record<string, string> | null;
}

export interface ChangesResponse {
  schema_version: string;
  dataset_version: string;
  events: ChangeEvent[];
}

export interface AppendixItem {
  branch: string;
  pdf_url: string | null;
  sequence: string;
  title: string | null;
  type: string | null;
  url: string | null;
  status?: 'AVAILABLE' | 'REMOVED' | 'DELETED' | string;
  is_deleted?: boolean;
}

export interface AttachmentItem {
  title: string | null;
  type: 'OFFICIAL_ATTACHMENT';
  url: string | null;
}

export interface ArticleItem {
  조문키?: string;
  조문번호?: string;
  조문여부?: string;
  조문제목?: string;
  조문시행일자?: string;
  조문제개정유형?: string;
  조문내용?: string;
  조문변경여부?: 'Y' | 'N' | string;
  조문참고자료?: string;
  조문이동이전?: string;
  조문이동이후?: string;
  항?: Array<{
    항번호?: string;
    항내용?: string;
    호?: Array<{
      호번호?: string;
      호내용?: string;
    }>;
  }>;
}

export interface AddendumItem {
  부칙키?: string;
  부칙공포일자?: string;
  부칙공포번호?: string;
  부칙내용?: string[] | string[][];
}

export interface RuleBody {
  articles: {
    조문단위?: ArticleItem[];
    [key: string]: unknown;
  };
  addenda: {
    부칙단위?: AddendumItem[];
    [key: string]: unknown;
  };
}

export interface RuleVersionDetail {
  changed_articles?: ChangedArticle[];
  articles_compared_to?: VersionReference | null;
  canonical_id: string;
  source_kind: SourceKind;
  stable_identifier: string;
  version_id: string;
  version_status: 'CURRENT' | 'FUTURE' | 'REPEALED' | 'REVIEW' | 'HISTORICAL' | 'ARCHIVE';
  version_reference: VersionReference;
  metadata: RuleMetadata;
  official_source_url: string;
  appendices: AppendixItem[];
  attachments: AttachmentItem[];
  body: RuleBody;
  hashes: {
    appendix_hash: string;
    attachment_link_hash: string;
    body_hash: string;
    metadata_hash: string;
  };
}

export interface RuleDetailResponse {
  changed_articles?: ChangedArticle[];
  articles_compared_to?: VersionReference | null;
  schema_version: string;
  dataset_version: string;
  rule: RuleSummary;
  current: RuleVersionDetail;
  upcoming: RuleVersionDetail[];
}

// Front-end display view models
export interface ChangedArticle {
  article_key: string;
  article_number: string;
  article_title: string;
  change_type: 'ADDED' | 'MODIFIED' | 'DELETED';
  before_text: string | null;
  after_text: string | null;
  effective_date: string | null;
}

export interface DisplayChangeEvent {
  id: string;
  canonical_id: string;
  rule_name: string;
  corrections_category: CorrectionsCategory;
  business_domains: BusinessDomain[];
  classification_status: ClassificationStatus;
  change_type: ChangeType;
  change_type_label: string;
  detected_at: string | null;
  effective_date: string | null;
  d_day: number | null; // e.g. 0 -> D-DAY, 3 -> D-3, 82 -> D-82, -2 -> D+2 (or past)
  department: string | null;
  factual_description: string;
  official_source_url: string;
  is_upcoming: boolean;
  is_today: boolean;
  status: RuleStatus;
  rule_summary: RuleSummary;
}

export interface ChangedArticleDiff {
  article_key: string;
  article_number: string;
  title: string;
  change_type: string;
  before_text: string | null;
  after_text: string | null;
  is_new: boolean;
  is_deleted: boolean;
  diff_chunks?: Array<{ type: 'unchanged' | 'deleted' | 'added'; text: string }>;
}
