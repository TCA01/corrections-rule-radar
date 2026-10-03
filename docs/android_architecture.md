# Future Android v1

Phase 1B parity: consume canonical changed_articles, rename/repeal/event results
from the backend. Do not diff articles or infer legal changes on-device. For
D-Day use LocalDate and the Asia/Seoul civil date of the current Instant. See
phase1b_contract.md for the shared midnight/UTC test vectors.

Kotlin + Jetpack Compose uses a repository layer reading Firebase-hosted `/api/v1`
JSON. Android never receives `LAW_API_OC` and never calls authenticated Law.go.kr
endpoints. Official public deep links come from regulation/version URLs.

DataStore stores selected related-business domains and notification preferences.
Persist the last-good manifest, registry, details and event IDs locally to support
offline reading. Replace cached collections only after schema/model/version checks;
on failures show stale-data status and the last successful sync time.

WorkManager periodically refreshes JSON, subject to Android scheduling and network
constraints. It does not promise exact wall-clock times. Compare stable event IDs
with an acknowledged/seen set, filter by reviewed relevant domains, and generate
local notifications once per unseen relevant event. Account for notification
permission on supported Android versions. Domain matching is relevance, not legal
instruction. A renamed regulation retains the same selected logical identity.

No Firebase Auth, Firestore or FCM in v1. FCM is optional future work if justified;
local refresh/notifications are sufficient for initial planning.
