import { ChangedArticle, PersistentChangeEvent, PersistentVersionInfo, RuleVersionDetail } from '../types';

export interface VisualComparison {
  articles: ChangedArticle[];
  textSource: 'STRUCTURED_SNAPSHOT' | 'EVENT_TEXT' | 'UNAVAILABLE';
}

const articlePattern = /^제\s*(\d+)\s*조(?:\s*의\s*(\d+))?\s*(?:\(([^)]*)\))?/;
const asList = (value: unknown): unknown[] => value == null ? [] : Array.isArray(value) ? value : [value];

// Same canonical field order as pipeline.diff.articles.text_lines. Never remove
// legal words (including literal 생략 or 삭제) from a structured official body.
function textLines(value: unknown): string[] {
  if (typeof value === 'string') return value.trim() ? [value.trim()] : [];
  if (Array.isArray(value)) return value.flatMap(textLines);
  if (!value || typeof value !== 'object') return [];
  const object = value as Record<string, unknown>;
  return ['조문내용', '항내용', '호내용', '목내용', '내용', '항', '호', '목'].flatMap(key => textLines(object[key]));
}

export function structuredArticles(body: { articles: unknown }): Map<string, { title: string; text: string }> {
  const raw = body.articles;
  const law = !!raw && typeof raw === 'object' && '조문단위' in raw;
  const items = asList(law ? (raw as Record<string, unknown>).조문단위 : raw);
  const groups = new Map<string, { title: string; text: string }>();
  let active: string | undefined;
  for (const item of items) {
    if (law && item && typeof item === 'object') {
      const flag = (item as Record<string, unknown>).조문여부;
      if (flag != null && flag !== '조문') continue;
    }
    const content = textLines(item).join('\n');
    const match = content.match(articlePattern);
    if (match) {
      const number = match[1] + (match[2] ? `의${match[2]}` : '');
      if (groups.has(number)) throw new Error('DUPLICATE_ARTICLE_NUMBER');
      active = number;
      groups.set(number, { title: match[0].trim(), text: content });
    } else if (!law && active && content) {
      if (/^제\s*\d+\s*(편|장|절|관)/.test(content)) active = undefined;
      else groups.get(active)!.text += '\n' + content;
    }
  }
  if (!groups.size) throw new Error('STRUCTURED_ARTICLES_UNAVAILABLE');
  return groups;
}

function verifySnapshot(event: PersistentChangeEvent, ref: PersistentVersionInfo, snapshot: RuleVersionDetail) {
  if (snapshot.canonical_id !== event.canonical_id || snapshot.version_id !== (ref.identifier || ref.version_id)
      || snapshot.metadata.effective_date !== ref.effective_date || snapshot.hashes.body_hash !== ref.body_hash) {
    throw new Error('COMPARISON_SNAPSHOT_PAIR_MISMATCH');
  }
}

export function resolveVisualComparison(event: PersistentChangeEvent, before: RuleVersionDetail, after: RuleVersionDetail): VisualComparison {
  if (!event.before_version || !event.after_version) throw new Error('COMPARISON_REFERENCES_UNAVAILABLE');
  verifySnapshot(event, event.before_version, before);
  verifySnapshot(event, event.after_version, after);
  const old = structuredArticles(before.body);
  const next = structuredArticles(after.body);
  const articles: ChangedArticle[] = [];
  // Official comparison selects the article; exact event snapshots supply the
  // complete text. No current-version inference or shorthand-based rewriting.
  for (const article of event.changed_articles) {
    const left = old.get(article.article_number);
    const right = next.get(article.article_number);
    if (!left && !right) throw new Error('COMPARISON_ARTICLE_UNAVAILABLE');
    if (left?.text === right?.text) continue;
    articles.push({ ...article, article_title: (right || left)!.title,
      before_text: left?.text ?? null, after_text: right?.text ?? null,
      change_type: !left ? 'ADDED' : !right ? 'DELETED' : 'MODIFIED' });
  }
  return { articles, textSource: 'STRUCTURED_SNAPSHOT' };
}

export function needsStructuredComparison(event: PersistentChangeEvent): boolean {
  return event.comparison_scope === 'OFFICIAL_COMPARISON_EXCERPT'
    || event.comparison_source === 'LAWGO_OLD_NEW' || event.comparison_source === 'LAWGO_ADMIN_OLD_NEW';
}
