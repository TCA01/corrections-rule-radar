/** Decode known entities once, returning plain text for React text nodes. */
export function decodeDisplayText(value: string): string {
  const entities: Record<string, string> = { '&lt;': '<', '&gt;': '>', '&amp;': '&', '&quot;': '"', '&#39;': "'" };
  return value.replace(/&(?:lt|gt|amp|quot);|&#39;/g, entity => entities[entity]);
}
