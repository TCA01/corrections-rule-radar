import { ChangedArticle, ChangedArticleDiff } from '../types';

/** Presentation only; Python owns membership, keys and comparison texts. */
export function displayArticleDiffs(articles: ChangedArticle[] = []): ChangedArticleDiff[] {
  const labels = { ADDED: '신설', MODIFIED: '일부개정', DELETED: '삭제' };
  return articles.map(article => ({
    ...article, title: article.article_title, change_type: labels[article.change_type],
    is_new: article.change_type === 'ADDED', is_deleted: article.change_type === 'DELETED',
  }));
}
