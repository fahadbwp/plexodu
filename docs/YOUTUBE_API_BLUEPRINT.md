# Plexudo — YouTube Data API v3 Architecture Blueprint & Compliance Specification

## 1. Executive Summary & Compliance Posture

Plexudo is committed to authentic, honest, and reproducible analytics. This document formalizes the production architecture, quota economics, metric definitions, and policy guardrails governing YouTube Data integration.

### Core Architectural Principles
- **Official API Exclusivity:** All YouTube platform data is retrieved exclusively via official Google YouTube Data API v3 REST endpoints authenticated with authorized API credentials.
- **Zero Scraping Policy:** Plexudo strictly forbids unofficial scrapers, reverse-engineered InnerTube client payloads, headless browser scraping, or undocumented private endpoints. Such mechanisms violate Google Terms of Service, jeopardize IP reputation, introduce brittle schema breakages, and risk service blacklisting.
- **Authentic Metrics:** Plexudo never synthesizes, fabricates, or interpolates analytics data. Unobserved metrics, hidden creator stats, and baseline observations are honestly surfaced as `Pending` or `Unavailable`.

---

## 2. Verified Endpoint Specifications & Quota Economics

YouTube Data API v3 enforces a default project quota of 10,000 units per calendar day (resetting at midnight Pacific Time / 07:00 UTC).

| Endpoint | Quota Cost | Purpose in Plexudo | Invocation Trigger |
| :--- | :--- | :--- | :--- |
| `videos.list?chart=mostPopular` | **1 unit** | Default regional trending feed | Feed load, category chip selection, region change |
| `search.list` | **100 units** | Keyword-specific topic discovery | Explicit search bar query input (not trending feed) |
| `videos.list?id={ids}` | **1 unit** | Cohort statistics batch retrieval | Follow-up batch request for search results (up to 18 IDs) |
| `commentThreads.list` | **1 unit** | Audience comments & sentiment | Video analysis, top trending video audience feedback |
| `channels.list` | **1 unit** | Channel subscriber count & branding | Competitor channel audit, video creator meta |
| `playlistItems.list` | **1 unit** | Channel upload playlist inspection | Channel uploads audit |

### Quota Allocation & Protection Strategy
1. **Separation of Trending vs Search:**
   - Default trending uses `videos.list?chart=mostPopular` (cost: 1 unit). This achieves a 99% quota saving compared to running keyword search for "trending" (101 units).
   - Keyword search via `search.list` (cost: 100 units) is isolated and restricted to deliberate search queries.
2. **Dedicated Search Call Allowance:**
   - `search.list` is bounded by a dedicated daily limit (`YOUTUBE_SEARCH_DAILY_LIMIT`, default 100 calls/day = 10,000 quota units).
   - Once the search allowance is exhausted, Plexudo returns HTTP 429 with honest explanatory copy, directing users to browse trending topics without failing catastrophically.
3. **Active Quota Tracking:**
   - Every attempted API call increments the thread-safe `YouTubeQuotaTracker` instance.
   - Units consumed, endpoint call counts, cache hits, and 403 quota exhaustion errors are tracked in real-time.

---

## 3. Metric Definitions & Semantics

### 3.1 Momentum Scoring & Deterministic Percentile
- **Legacy Flaw:** Previously calculated as `((velocity / 1500 - 1) * 100)` with an arbitrary ceiling at `+950`. This compressed viral breakout videos and distorted cross-category comparisons.
- **Standardized Algorithm:** Relative cohort midpoint percentile ranking:
  $$\text{Percentile} = \text{round}\left(\frac{\text{less} + 0.5 \times \text{equal}}{N} \times 100, 1\right)$$
  Where $N$ is the number of videos in the active cohort, $\text{less}$ is the count of cohort videos with lower estimated views/hour, and $\text{equal}$ is the count with identical views/hour.
- **Velocity Distinction:** Single-snapshot estimated lifetime-average velocity ($\text{views} / \max(1, \text{hours\_ago})$) is explicitly separated from multi-point time-series growth velocity.

### 3.2 Hidden Likes Representation
- When video creators disable public like counts, YouTube API omits the `likeCount` attribute.
- **Rule:** Missing likes must be represented as `None` (JSON `null`) and labeled `"Unavailable"` in UI and CSV/PDF exports.
- Missing likes are never treated as `0`. Cohort engagement rate calculations and aggregate like totals strictly exclude videos with hidden likes to prevent deflating performance averages.

### 3.3 Multilingual Sentiment Analysis
- Multi-token lexical and semantic evaluation supporting English, Urdu (Arabic script Unicode `\u0600-\u06FF`), Roman Urdu, and Hindi transliterated terms.
- Low-confidence, pure-emoji, or conflicting comments are classified as `unclassified` rather than being forced into artificial `neutral` or `positive` buckets.

---

## 4. In-Memory Caching & Serverless Safety

- **BoundedTTLCache:** Replaces unbounded dictionary caching with a thread-safe, bounded LRU/FIFO eviction cache (`_CACHE_MAX_ENTRIES = 500`, TTL = 900 seconds / 15 minutes).
- **Concurrency Protection:** Cache reads, writes, and prunes are protected by reentrant locks (`threading.RLock`) to prevent race conditions during high-concurrency bursts.
- **Rate Limiting:** `SlidingWindowRateLimiter` enforces per-IP and per-endpoint boundaries with automatic key pruning to prevent serverless heap exhaustion.

---

## 5. Architectural Evaluation Matrix

| Capability | Approach | Status | Rationale |
| :--- | :--- | :--- | :--- |
| **Regional Trending** | `videos.list?chart=mostPopular` | **Approved (Active)** | 1 quota unit, official Google support, instant snippet+stats. |
| **Topic Search** | `search.list` + batch `videos.list` | **Approved (Active)** | 101 quota units, strictly gated by 100/day allowance. |
| **Single Video Details** | `videos.list?id={id}` | **Approved (Active)** | 1 quota unit, full video statistics and content details. |
| **Audience Feedback** | `commentThreads.list?videoId={id}` | **Approved (Active)** | 1 quota unit, authentic top-level viewer discussion. |
| **Distributed Cache** | Upstash Redis / Memcached | **Deferred (Phase 2)** | Evaluate after traffic scaling; bounded local memory is safe for Phase 1. |
| **InnerTube Scraping** | Python `pytube` / `innertube` | **REJECTED** | Severe TOS violation, frequent breaking changes, IP blocks. |
| **Synthetic Curves** | Mathematical decay / sine generators | **REJECTED** | Violates truth-in-data core principle; honest pending states required. |
| **Headless Browser Scraping** | Puppeteer / Playwright | **REJECTED** | High compute cost, slow latency (5s+), fragile DOM selectors. |
