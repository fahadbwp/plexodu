# Plexudo Technical Debt & Operational Limitations

This document tracks intentional architectural trade-offs, deferred capabilities, and known operational limitations across phases.

---

## 1. Resolved in Phase 1 (Analytics Accuracy)

The following items previously deferred beyond Phase 0 have been fully resolved in Phase 1:
- **Momentum Saturation Cap (+950):** Removed arbitrary `+950` clamping in `real_api.py`. Replaced with deterministic relative midpoint percentile ranking (0–100 idx) across cohorts.
- **Default Regional Trending:** Default trending now uses official `videos.list?chart=mostPopular` (1 quota unit) with `regionCode="PK"` default, saving 99% of API quota compared to keyword search for "trending".
- **Hidden Likes Handling:** Creator-hidden likes are represented as `None` (JSON `null`) and displayed as `"Unavailable"` across UI, CSV, and PDF exports. Engagement averages strictly exclude videos with hidden likes.
- **Multilingual Sentiment:** Extended `nlp_engine.py` to preserve Urdu Arabic-script Unicode (`\u0600-\u06FF`) and curated lexicons for Urdu, Roman Urdu, and Hindi transliterated terms. Ambiguous comments return `unclassified`.

---

## 2. Active Technical Debt & Serverless Operational Constraints (Phase 2+)

### 2.1 Process-Local Caching & Serverless Boundary
- **Current Behavior:** `BoundedTTLCache` in `backend/services/real_api.py` operates strictly in-memory (`_CACHE_MAX_ENTRIES = 500`, TTL = 900s) inside the active Python runtime process.
- **Serverless Constraint:** In Vercel serverless (AWS Lambda), concurrent HTTP requests spawn independent container instances with isolated memory spaces. Cold-starts initialize an empty cache.
- **Production Consequence:** Cache hits only occur when requests hit a warm container instance. Repeated identical queries routed to distinct concurrent instances will both invoke upstream YouTube API calls.
- **Resolution Plan (Phase 2):** Integrate an external distributed cache (e.g. Upstash Redis / Redis REST API) with encryption in transit to enable global cross-instance cache deduplication.

### 2.2 Process-Local Rate Limiting
- **Current Behavior:** `SlidingWindowRateLimiter` in `backend/services/security_guard.py` maintains request timestamps in an in-memory dictionary.
- **Serverless Constraint:** Rate limits protect individual warm lambdas against rapid-fire request flooding, but cannot enforce a global aggregate limit across multiple concurrent lambdas.
- **Resolution Plan (Phase 2):** Implement edge rate limiting via Vercel Edge Middleware / WAF or backing the limiter with Upstash Redis token-bucket algorithms.

### 2.3 Process-Local YouTube Quota Tracking & Burst Risk
- **Current Behavior:** `YouTubeQuotaTracker` tracks endpoint calls (`search.list`, `videos.list`, etc.) and throttles search queries when `search_calls >= 100` within the active container.
- **Serverless Constraint:** The tracker is process-local and resets on cold starts. It cannot enforce a global hard ceiling across dozens of concurrent ephemeral containers.
- **Production Risk:** Under sudden high-traffic spikes across many concurrent cold lambdas, aggregate calls to `search.list` could collectively consume more than the project's 10,000 daily quota before individual containers reach their internal limits.
- **Mitigation in Place:**
  - Default trending queries use `videos.list?chart=mostPopular` (1 unit instead of 100).
  - In-flight 403 quota exhaustion responses from Google API are cleanly caught by `_is_quota_error()` and returned as honest HTTP 429 errors without leaking credentials or crashing.
- **Resolution Plan (Phase 2):** Move quota tracking to an atomic distributed counter (Redis or Supabase PostgreSQL atomic increment).

### 2.4 Data Retention & Snapshot Automation
- Searches commit `Trend`, `Metric`, and `Sentiment` rows to PostgreSQL without an automated lifecycle or retention policy.
- No background cron job exists to automatically trigger periodic trend snapshots outside of on-demand user searches.
- **Resolution Plan (Phase 2):** Implement Vercel Cron jobs for scheduled regional snapshots and define data retention / pruning policies.

### 2.5 Ephemeral Storage for PDF Reports
- PDF exports generated via ReportLab are written to temporary disk storage (`/tmp` on Vercel) when using file paths. The streaming endpoint `generate_pdf_report_buffer()` streams directly from in-memory `io.BytesIO`.
- Direct disk paths in `/tmp` are ephemeral and destroyed when serverless containers terminate.

### 2.6 Legacy User Model & Migration Scripts
- Legacy `User` model, table references, and `VALID_ROLES` remain preserved in code to ensure zero regressions with existing database foreign keys (`Trend.created_by`, `Report.generated_by`, `AuditLog.user_id`).
- Legacy explicit migration scripts (`backend/migrate_db.py`, etc.) remain potentially destructive and must never be run against production Supabase. Production DDL is governed exclusively by verified `database/schema_postgres.sql`.

### 2.7 Bandit Medium Report-Only Findings
- B108 (`/tmp` directory usage) and B104 (development server binding `0.0.0.0`) remain report-only findings in local/audit environments. High-severity Bandit gate is strictly enforced (0 findings).
