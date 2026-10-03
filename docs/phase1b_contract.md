# Phase 1B contract migration and Android parity

Active API schema is **1.2** at `/api/v1`. No previous field is removed or
renamed. Strict schema 1.1 forbids additional properties and fixes the version;
therefore this is an explicit migration, not a silent schema 1.1 modification.
The schema freeze lock now identifies 1.2. Existing immutable version URLs keep
their original **archive format 1.1** and byte content; the archive schema remains
unchanged. Client DTOs must accept this documented distinction.

The web production build now runs TypeScript noEmit checks before Vite. Fetches
request revalidation and compare manifest/list/health/change dataset versions;
mixed versions are rejected with the existing retry/error presentation.

Rule detail exposes `changed_articles` and nullable `articles_compared_to` for
the closest retained earlier-effective official version. This is a textual
comparison, not a new observed event or legal interpretation. Each upcoming
version exposes the same fields against current. Every change event exposes
these fields against its recorded old version, or current baseline at first
observation of a future version. The comparison reference is persisted so the
future event retains its original baseline after becoming current.

Each changed article has:

```json
{
  "article_key": "0053021",
  "article_number": "53의2",
  "article_title": "제53조의2(조문 제목)",
  "change_type": "MODIFIED",
  "before_text": "공식 종전 본문",
  "after_text": "공식 신규 본문",
  "effective_date": "2026-12-24"
}
```

Types are ADDED, MODIFIED, DELETED. Missing before/after text is null. Keys use
official article keys where available; administrative prose uses article number
including branch as its key. Chapter headings are excluded. Paragraphs/items/
subitems and singleton XML objects are supported. Parent text precedes children
regardless of JSON key order. A flag alone with identical text does not create a
text difference. Unknown/unstructured comparison or absent baseline yields an
empty array; clients must not infer legal equivalence from that. Renumbering can
appear as removal/addition; no semantic equivalence or duty inference is made.
An official tombstone retained as article text appears as a textual modification;
DELETED identifies a missing article key in an otherwise structured newer body.

## Civil date and timestamp contract

- effective_date is strictly YYYY-MM-DD, a civil calendar date. Never parse it
  as an instant or apply a timezone conversion.
- D-Day is target civil date minus the **Asia/Seoul current civil date**. The
  effective day is zero (D-DAY). Use integer calendar-day differences, not local
  midnight timestamps or elapsed 24-hour divisions across device timezones.
- last_successful_sync and other timestamps are ISO-8601 instants with explicit
  offset/Z. Display timestamps in Seoul; compare instants normally.

Shared regression vectors for effective_date 2026-10-03:

| Instant | Seoul date | D-Day |
|---|---|---:|
| 2026-10-02T23:59:00+09:00 | 2026-10-02 | 1 |
| 2026-10-03T00:00:00+09:00 | 2026-10-03 | 0 |
| 2026-10-02T14:59:00Z | 2026-10-02 | 1 |
| 2026-10-02T15:00:00Z | 2026-10-03 | 0 |
| 2026-10-03T00:00:00Z | 2026-10-03 | 0 |
| 2026-10-03T15:00:00Z | 2026-10-04 | -1 |

Kotlin parity: LocalDate.parse(effective_date),
Instant.now().atZone(ZoneId.of("Asia/Seoul")).toLocalDate(), then
ChronoUnit.DAYS.between(today, effectiveDate). Never use the device default zone.

Android and React display backend changed_articles. Neither client reimplements
article/legal change detection, rename resolution or repeal detection. Android
owns D-Day presentation, filtering/sorting, local domain preference, verified
offline cache and notification/seen-event state. No Android build is performed
in this phase. Public health retains last_successful_sync for the published
last-good dataset; private attempt health advances on every successful check.
