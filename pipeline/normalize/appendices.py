"""Conservative metadata-only tombstones; original titles and URLs are retained."""
import re

DELETED=re.compile(r'^삭제(?:\s*[<〈(\[]?\s*\d{4}[년.\-/\s]+\d{1,2}[월.\-/\s]+\d{1,2}[일.\s]*[>〉)\]]?)?\s*$')

def appendix_status(appendix):
    # Structured API metadata can contain literal XML delimiter entities.
    # Decode just these delimiters for matching; keep the original metadata.
    title=(appendix.get('title') or '').replace('&lt;','<').replace('&gt;','>').strip()
    return 'REMOVED' if DELETED.fullmatch(title) else 'AVAILABLE'
