# Future Firebase Hosting

Phase 1B prepares firebase.json and the verified combined web/dist artifact;
actual deployment remains prohibited. See phase1b_operations.md for activation,
cache policy, post-deploy verification and retry behavior.

No Firebase project is initialized or deployed during Phase 0.

Future deployment root combines web build artifacts and `api/v1` generated JSON.
React and Android consume identical HTTPS URLs. No GitHub Pages base paths.

GitHub Actions → complete Python sync → schema/leak/fail-closed verification
→ build web if needed → `firebase deploy --only hosting` → verify live manifest,
health and dataset version. `LAW_API_OC` remains exclusively a GitHub Actions
secret available to the sync process; it is never copied to build environment
variables intended for frontend bundlers, Hosting files or app clients.

Recommended dynamic JSON headers: `Cache-Control: public, max-age=60, must-revalidate`
or `Cache-Control: no-cache` for manifest and health, using ETag validation. Reserve
long immutable caching for future content-addressed assets. Configure API headers
before SPA fallback so missing API paths cannot return `index.html` as JSON.
Android apps do not require CORS; browser cross-origin hosting may need explicit
allowed origins, and must never receive credentials.

Keep the last-good validated artifact and dataset digest. A failed or partial sync
does not deploy or replace public files. A failed post-deploy check restores the
previous complete Hosting release, not selected individual JSON files. Clients
should verify manifest version on collections and keep their local last-good cache.

Official header guidance: https://firebase.google.com/docs/hosting/full-config
and https://firebase.google.com/docs/hosting/manage-cache
