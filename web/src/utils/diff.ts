import { ChangedArticle, ChangedArticleDiff } from '../types';

export type DiffChunkType = 'unchanged' | 'deleted' | 'added';

export interface DiffChunk {
  type: DiffChunkType;
  text: string;
}

/**
 * Tokenize Korean legal text into word and punctuation/whitespace tokens.
 * Uses Intl.Segmenter with word granularity where available,
 * falling back to regex preserving Korean words, punctuation, and whitespace.
 */
export function tokenizeLegalText(text: string): string[] {
  if (!text) return [];

  // Regex tokenization that treats Korean word chunks, legal numbers (e.g., 제53조의2),
  // punctuation, and whitespace sequences as atomic tokens.
  const regex = /([가-힣a-zA-Z0-9_]+|[^\s가-힣a-zA-Z0-9_]+|\s+)/g;
  const tokens = text.match(regex);
  return tokens || [text];
}

/**
 * Computes a word/phrase-level diff between beforeText and afterText
 * using Longest Common Subsequence (LCS).
 * Produces clean, non-noisy diff chunks without splitting Korean syllables.
 */
export function computeWordDiff(beforeText: string | null | undefined, afterText: string | null | undefined): DiffChunk[] {
  const before = beforeText || '';
  const after = afterText || '';

  // Edge cases
  if (!before && !after) return [];
  if (!before && after) {
    return [{ type: 'added', text: after }];
  }
  if (before && !after) {
    return [{ type: 'deleted', text: before }];
  }
  if (before === after) {
    return [{ type: 'unchanged', text: before }];
  }

  const a = tokenizeLegalText(before);
  const b = tokenizeLegalText(after);
  const m = a.length;
  const n = b.length;

  // Use DP table for LCS
  // For long articles, memory is bounded because token count rarely exceeds 1500
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (a[i] === b[j]) {
        dp[i + 1][j + 1] = dp[i][j] + 1;
      } else {
        dp[i + 1][j + 1] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }

  // Backtrack to find diff chunks
  let i = m;
  let j = n;
  const rawChunks: DiffChunk[] = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      rawChunks.push({ type: 'unchanged', text: a[i - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rawChunks.push({ type: 'added', text: b[j - 1] });
      j--;
    } else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) {
      rawChunks.push({ type: 'deleted', text: a[i - 1] });
      i--;
    }
  }

  rawChunks.reverse();

  // Merge consecutive chunks of same type to avoid fragmented DOM nodes
  const merged: DiffChunk[] = [];
  for (const chunk of rawChunks) {
    if (merged.length > 0 && merged[merged.length - 1].type === chunk.type) {
      merged[merged.length - 1].text += chunk.text;
    } else {
      merged.push({ ...chunk });
    }
  }

  return merged;
}

/**
 * Enhanced article diff view model for presentation.
 * Preserves canonical backend text, order, and flags, while augmenting with word diff chunks.
 */
export function displayArticleDiffs(articles: ChangedArticle[] = []): ChangedArticleDiff[] {
  const labels: Record<string, string> = { ADDED: '신설', MODIFIED: '일부개정', DELETED: '삭제' };

  return articles.map((article) => {
    const isNew = article.change_type === 'ADDED';
    const isDeleted = article.change_type === 'DELETED';
    const chunks = computeWordDiff(article.before_text, article.after_text);

    return {
      ...article,
      title: article.article_title,
      change_type: labels[article.change_type] || article.change_type,
      is_new: isNew,
      is_deleted: isDeleted,
      diff_chunks: chunks,
    };
  });
}
