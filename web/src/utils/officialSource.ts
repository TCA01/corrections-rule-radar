// One state-aware builder. Only official structured identifiers may be used.
export function officialSource(source: {
  source_kind?: string; canonical_id?: string; version_id?: string | null;
  effective_date?: string | null; metadata?: { effective_date?: string | null };
  official_source_url?: string | null;
}): string {
  let url: URL;
  try { url = new URL(source.official_source_url || 'https://www.law.go.kr'); }
  catch { return 'https://www.law.go.kr'; }
  if (!['law.go.kr', 'www.law.go.kr'].includes(url.hostname) || !['https:', 'http:'].includes(url.protocol)) return 'https://www.law.go.kr';
  url.protocol = 'https:';
  const law = source.source_kind === 'law' || source.canonical_id?.startsWith('law-') || url.pathname.endsWith('/lsInfoP.do');
  const id = source.version_id || url.searchParams.get('lsiSeq');
  const day = source.effective_date || source.metadata?.effective_date;
  if (law && id && /^\d+$/.test(id) && day && /^\d{4}-\d{2}-\d{2}$/.test(day)) {
    return `https://www.law.go.kr/LSW/lsInfoP.do?efYd=${day.replace(/-/g, '')}&lsiSeq=${id}`;
  }
  // Administrative IDs and attachment URLs are not statute lsiSeq identifiers.
  for (const key of [...url.searchParams.keys()]) if (key.toLowerCase() === 'oc') url.searchParams.delete(key);
  return url.toString();
}
