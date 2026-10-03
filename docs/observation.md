# Live stability observation

From the repository root with LAW_API_OC in the process environment and network
access permitted:

```powershell
python scripts/observe.py
python scripts/observe.py --runs 3
python scripts/verify.py
```

Uses the normal live collector/publisher, sequentially, up to 10 runs. Keep one
writer active; do not overlap sync, observation or tests reading transient reports.
Reports: data/reports/observation/{run_id}.json. RUNNING survives interruption and
is not a completed success. No scheduler or deployment is enabled.

Reports record start/end/duration, API and official-page requests, API response
average, retries, success/review/failure counts, new events, publication status,
last-good version, safe error codes and public content/mtime/event/hash stability.
Requests include retry attempts; response time includes transport/read; wall time
also includes pacing, parsing, official pages and validation.

Unchanged runs update only private ops/reports. Genuine source changes or explicit
contract/classification review can publish; contract review is not a legal event.
The first three blocked attempts occurred with restricted execution networking:
OFFICIAL_PAGE_FAILED, zero API requests. They remain in the record. Successful
permitted runs measure actual source traffic separately.

Recovery tests use actual observer/publisher code, temporary repositories and real
normalized evidence with injected timeout/partial failures: success → blocked →
NO_CHANGE recovery. Last-good public bytes/mtimes and successful version survive.

Twice-daily feasibility is a measured capacity observation, not an official quota
guarantee. This phase proves same-session stability; multi-day observation and
scheduler approval remain necessary for production operations.
