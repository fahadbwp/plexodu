# Trend Analyzer critical data-integrity audit and hotfix

Date: October 26, 2026 (Asia/Karachi).

## Release decision

**NO-GO for production.** The owner cannot confirm YouTube approval for derived analytics or extended public-statistics storage. This hotfix corrects numerical truth and preserves the Stitch Option A interface; it does not grant API-policy permission or implement a data-retention program. Gate B and Gate C are unchanged. No production SQL, migrations, data changes, merge or deployment were performed.

## Verified identity

- Repository: `C:\Users\Fahad Saleem\Documents\plexodu-main\plexodu-phase0`.
- Branch: `fix/trend-analyzer-data-truth`, created from freshly fetched `origin/main`.
- Verified production and main baseline: `4a00f46e65cff40057521e2c270aa9e849e11791`.
- Vercel production deployment: `dpl_C5u2skUvVShTXQXnLLU52MTKFjWG`, READY, alias `plexudo.vercel.app`, Git metadata `main` / `4a00f46`. This was a read-only inspection.
- Gate B: `feat/gate-b-quota-guard` at `8cc12d2977daceae84d12f91db5f9daa148d9ad3`, unchanged.
- Final implementation commit SHA: **c482a971c94103d8ee2081174fd3d11cdd4433d9**. The evidence/documentation follow-up does not change executable code; final branch HEAD is recorded in the PR and delivery response.

## Confirmed findings and corrected behavior

| Suspect display | Source/proof | Hotfix |
|---|---|---|
| `+38.4%` and initial `+42.8%` | Hardcoded fallback/HTML, not measured growth | Unavailable unless finite growth and explicit comparability evidence; real zero and negative changes preserved |
| `+167% Surge` | Peak divided by 60% of the same maximum, approximately 167% regardless of actual growth | Removed; no surge pin on upload-age data |
| `30d Baseline` | Observed curve offset by 10–15 SVG pixels | Removed; no historical comparator in Chart A |
| `Algorithmic confidence 94.2%` | Literal HTML | Unavailable; no calibrated confidence probability claimed |
| Fixed sparklines and mini bars | Literal paths/bar heights | Removed; compatibility anchors retained empty |
| `Median 24h Views` | Total lifetime views divided by video count (mean) | Actual median of returned lifetime counters; accurately titled |
| Momentum speed/gauge | Missing score defaulted to 74.2 or 50 + count*4, with “Ultra Fast” | Actual eligible cohort index or unavailable; no measured-speed or probability claim and no fabricated arc |
| Format 52/34/14 and capsule mismatch | Static donut vs separate helper; helper was nested inside another function but called globally | One top-level shared duration computation; unknown durations unavailable; buckets explicitly not official Shorts/Live classification |
| `+68% Shorts Velocity`, retention 64.5%, benchmark advantages | Unsupported public-API metrics | Earlier `7a857f4`/baseline changes already removed some; hotfix guards against reintroduction. Retention remains unavailable |
| `Updated just now`, 26-minute re-index | Literal text without fetch timestamp or scheduled job | Explicit response-fetched metadata when supplied; otherwise freshness unavailable; no countdown |
| Rows using missing views/age | `views || 1000`, `hoursAgo || 6`, backend missing-date default 24h | Unknown inputs unavailable; invalid/future upload times excluded from age/momentum estimates |
| Missing category | Invented Tech/requested category | Explicit unavailable category; no fake highest-category label |
| Upload-age overflow bucket | Older videos clamped into a bounded final interval | Final interval labelled open-ended; missing-age videos excluded and disclosed |
| Null counters saved as zero | SQLAlchemy insert defaults could replace supplied Python None | Explicit SQL NULL for unknown counters and observation metrics, retaining valid zero |
| Unknown growth/hidden counters in exports | Empty cells, historical daily labels, legacy fallback values | Unavailable/null handling, heuristic labels, lifetime-counter snapshot labels, local API/CSV/PDF regressions |
| Timeline corruption risks | KPI total could overwrite single persisted point; daily_metrics fallback; unproven cohort; smoothing | Exact timestamped raw counters, no KPI overwrite or daily fallback; multi-point comparison requires explicit cohort compatibility |
| Zero denominator / insufficient history | Zero-percent growth or zero change-difference despite unavailable calculation | Unavailable while preserving actual zero counters; 3 observations required for change difference |

Legitimate chart geometry, rounding, API category IDs, ranking coefficients, thresholds, cache TTL and pagination are retained. They are not observation data. API HTTP 200 alone is never evidence that every optional metric is present.

## Dual-chart contract

**Chart A: Lifetime Views by Upload Age.** Current sample's lifetime counters are grouped by genuine publication age. It shows bars, exact response labels and dynamically scaled count axes. Unknown timestamps are excluded; the last bucket includes older videos. Desktop retains the approved SVG card; phones/tablets use the actual responsive Chart.js canvas so labels are readable. There is no historical line, synthetic surge, fixed sparkline or time-series interpretation. Its accessible table is not inside an aria-hidden ancestor.

**Chart B: Time-Series View Trajectory.** Actual saved observations retain their counters and timestamps. Backend matching uses a SHA-256 key of normalized keyword, platform, region, category, timeframe and sorted video IDs. Legacy rows without that key do not join a compatible cohort. Refreshed responses preserve original fetch time; cached repeats do not become new independent time-series evidence. Independent comparison points are spaced at least 24h. Unknown legacy timestamps are skipped, not invented as now. One point is a baseline with no fake line; multiple points use raw values with straight visual connectors, not synthetic smoothed measurements. A changed or unproven cohort has no growth comparison. A prior zero counter cannot supply a percentage denominator.

## Complete provenance matrix

[Machine-readable matrix: every metric has all 10 requested fields](qa/trend-data-truth/metric-provenance.json). It includes hidden compatibility anchors, nested summaries, both renderers, axes/tooltips, historical windows, forecasts, classifications, cache fields and exports. The summary below does not replace that detailed matrix.

| UI metric | DOM / surface | Unit / classification | Backend source |
|---|---|---|---|
| Top topic growth | `kpiTopTopicVelocity` | % observed change; Unavailable / derived if evidenced | `kpis.growthRate; kpis.growthComparable` |
| Median lifetime views | `kpiMedianViewsVal` | lifetime views per returned video; Derived aggregate | `videos[].views` |
| Relative momentum index | `kpiMomentumScoreVal; kpiMomentumSpeedBadge` | relative 0–100 percentile; Heuristic | `videos[0].momentumScore` |
| Sample engagement | `kpiEngagementRatioDisplay; kpiAvgEngVal` | mean of per-video percentages; Derived ratio | `kpis.avgEngagement` |
| Total views anchor | `kpiTotalViewsVal` | sum of returned lifetime counters; Derived aggregate | `kpis.totalViews` |
| Lead category and views | `kpiTopCatVal; kpiTopCatDeltaText` | category label / lifetime views; Observed grouping + aggregate | `kpis.topCategory/topCategoryViews` |
| Relative count above index 40 | `kpiRisingCountVal; kpiRisingCountDeltaText` | count / returned sample; Heuristic count | `kpis.risingCount/totalTracked` |
| Chart A visible bars | `velocitySvgChart; svgVolumeBars; pulseViewsChart` | upload-age bucket / lifetime views; Derived grouped snapshot | `timeSeries[].label/views` |
| Chart A axes and accessible table | `svgGridLines; svgXAxisLabels; viewsChartA11y` | views / upload-age interval; Presentation | `timeSeries` |
| Historical baseline/surge curves | `svgBaselineCurve; svgObservedCurve; svgAreaCurve; svgSurgePin; svgSurgeText` | none; Unavailable | `None` |
| KPI microcharts | `sparklineAreaPath; sparklineLinePath; kpiMiniBarsContainer` | none; Unavailable | `None` |
| Confidence / freshness footer | `algoConfidenceVal; static re-index footer` | none; Unavailable | `None` |
| Duration buckets / donut and legend | `donutShortsPct; donutShortsArc; donutLongArc; formatShortsStat; formatLongStat; formatLiveStat; kpiFormatLegend` | percentage of returned video count; Derived duration distribution | `videos[].duration_sec` |
| Shorts and livestream classification | `data-filter=shorts; duration bucket labels` | seconds, not observed format; Observed duration / unavailable format | `videos[].duration_sec` |
| Audience retention | `30-Second Hold Rate card` | none; Unavailable | `None` |
| Chart B observed trajectory | `viewsChart; viewsTrajectoryA11y` | observation timestamp / lifetime views; Observed local snapshots of API counters | `results.YouTube.trend_intelligence.timeline` |
| Change vs prior observation | `chartBaselineNote` | views difference / %; Derived comparison | `timeline[-2:].views` |
| History windows | `historyTableBody` | % change; Derived comparison | `trend_intelligence.historical_context.1d/7d/30d/90d` |
| Stage / observed change / change difference | `summaryDirection; summaryVelocity; summaryAcceleration` | category / % between snapshots / percentage-point difference; Derived comparison | `current_direction_display; velocity_display; acceleration_display` |
| Virality index | `summaryVirality` | bounded heuristic score /100; Heuristic, not probability | `results.YouTube.virality_score` |
| Opportunity score | `opportunityScoreBadge` | heuristic index /100; Heuristic / unavailable | `trend_intelligence.opportunity_score or result.opportunity_score` |
| Sentiment percentages | `dominantSentimentBadge; sentimentBreakdown; per-video sentiment bar` | % classified returned comments; Estimated/classifier output | `sentiment.*_score; videos[].sentiment` |
| Forecast and bounds | `forecastPanel; forecastGrid; forecastFallback` | estimated views per future day; Estimated projection | `trend_intelligence.forecast.projection_days` |
| Milestones and scan counts | `trendEventsList; trendBannerText` | count / timestamp; Observed app metadata / derived events | `trend_intelligence.events/scan_count/first_seen_at/last_seen_at` |
| Rank and displayed sample size | `pulseList; trendingListTitle` | rank / count; Derived ranking | `videos[].rank/trendScore; videos.length` |
| Per-video views/comments/duration/age | `pulseList row metadata` | counts / seconds / elapsed hours; Observed counters + calculated elapsed age | `videos[].views/comments/duration_sec/hoursAgo` |
| Per-video lifetime-average views/hour | `pulseList row velocity label` | estimated lifetime-average views/hour; Estimated rate, not observed acceleration | `videos[].estimated_views_per_hour` |
| Subscriber filter | `data-filter=under100k` | subscriber count threshold; Unavailable in ordinary feed | `videos[].subscriber_count/subscribers (not in normal video feed)` |
| Cached/fresh/stale state | `kpiTotalViewsDeltaText` | ISO UTC timestamp / state; Observed app metadata | `cached; is_stale; fetched_at; cache_served_at` |
| CSV summary and counters | `exportCsvBtn -> /api/export-csv/:id` | views / % / heuristic / counts; Observed + derived exports | `Trend/Metric rows` |
| PDF summary and sentiment | `exportPdfBtn -> /api/report/:id` | views / % / heuristic; Observed + derived exports | `Trend/Metric/Sentiment rows` |

## Source and policy review

The [official video resource](https://developers.google.com/youtube/data/reference/rest/v3/videos) defines public counters and duration/publication fields. Duration alone is not proof of a Shorts format or livestream. [Audience-retention metrics belong to YouTube Analytics](https://developers.google.com/youtube/analytics/metrics), rather than the public Data API fields used here.

The [YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies), III.E.4.h and III.L, restrict derived metrics and describe a conditional permission pathway for audited analytics use cases. III.E.4 also restricts storage of non-authorized statistical data beyond 30 days. **The owner cannot confirm applicable approval.** Derived calculations, historical comparisons, estimates and classifiers are therefore not marked policy-cleared in the matrix. Accurate labels are not a substitute for permission. Existing historical records were preserved; their retention/deletion compliance remains unverified and requires separately authorized work. No cleanup or migration was executed.

The model's categorical confidence, percentile ranking, virality and forecasts are own-product heuristics/estimates, not YouTube observations or calibrated success probabilities. Their equations remain documented in the existing engines; no claim is made that the absence of fabricated numbers resolves policy restrictions.

## Validation and evidence

| Check | Result |
|---|---|
| Baseline Python suite | 340 passed |
| Final Python/API/SEO/schema/security contracts | **351 passed**, one existing ReportLab warning; pytest 9.0.3 |
| Node unit suites | 4 passed; **19 new behavioral cases** |
| Trend Analyzer browser | **45 states**, five required widths; 62 interaction checks passed |
| Shared five-tool browser regression | **60 states**, 96 interaction checks passed |
| Geometry / axe / browser script errors | 0 failures in both browser suites |
| Separate settled visual captures | 5 after states passed; animations settled for final bar evidence |
| Ruff correctness selectors | Passed |
| Bandit high-severity gate | Passed; 2 existing medium findings |
| Runtime and dev pip-audit | No known vulnerabilities in either declared scope |
| Build/static | Frontend JS syntax, Python compile/import and actual browser assets/routes verified; no npm build pipeline |

The Python count increased by eleven: ten cases in the new hotfix file (including three publication-time cases) and one complete Flask cache/NULL/CSV pipeline case. A dev-only pytest advisory (duplicate reports of PYSEC-2026-1845) was fixed by upgrading 8.4.2 to 9.0.3. CI uses the same pin.

[Evidence manifest, geometry, functional assertions and source fingerprints](qa/trend-data-truth/evidence.json). All API calls in browser captures are deterministic fixtures. Full-page captures use the original source at `4a00f46` for before and the hotfix source for after. They are explicitly labelled; they do not certify live YouTube analytics. User-supplied desktop images contain personal browser chrome and were not republished.

| Width | Before | After |
|---|---|---|
| 320px | [PNG](qa/trend-data-truth/before/320.png) | [PNG](qa/trend-data-truth/after/320.png) |
| 390px | [PNG](qa/trend-data-truth/before/390.png) | [PNG](qa/trend-data-truth/after/390.png) |
| 768px | [PNG](qa/trend-data-truth/before/768.png) | [PNG](qa/trend-data-truth/after/768.png) |
| 1280px | [PNG](qa/trend-data-truth/before/1280.png) | [PNG](qa/trend-data-truth/after/1280.png) |
| 1440px | [PNG](qa/trend-data-truth/before/1440.png) | [PNG](qa/trend-data-truth/after/1440.png) |

Tests exercise missing growth vs real zero/negative growth, absent likes/comments/durations/publication times, missing category, unknown collection time, stale cache flags, no history/baseline/multi-point history, explicit changed-cohort suppression, zero denominators, raw chart values, hidden-counter NULL persistence, CSV values/labels, PDF table values, XSS escaping, visible mobile chart surfaces, keyboard traversal, drawer behavior, filters, workflow links and exports.

Changed test contracts are explicit: cache payload content stays equal while cache metadata must differ; a zero denominator is unavailable rather than fabricated 0%; the complete sentiment fixture explicitly supplies a zero negative class; raw observations replace a smoothed-dataset assertion. None of these tests was deleted or skipped to force a pass. New behavior assertions cover the corrected semantics. The desktop harness follows the approved prior topbar removal and checks actual tool inputs/directory links.

## Files and reproduction

- `.github/workflows/ci.yml`
- `backend/app.py`
- `backend/services/real_api.py`
- `backend/services/report_generator.py`
- `backend/services/trend_engine.py`
- `backend/services/trend_intelligence.py`
- `docs/TREND_ANALYZER_DATA_TRUTH_AUDIT.md`
- `docs/qa/trend-data-truth/`
- `frontend/css/trend-analyzer.css`
- `frontend/js/tools/trend-analyzer.js`
- `frontend/tools/trend-analyzer.html`
- `requirements-dev.txt`
- `tests/stitch-browser-qa.cjs`
- `tests/test_phase3_security.py`
- `tests/test_phase8_trend_intelligence.py`
- `tests/test_stitch_dual_chart_contracts.py`
- `tests/test_trend_data_truth_hotfix.py`
- `tests/trend-data-browser.cjs`
- `tests/trend-data-truth.cjs`
- `tests/trend-rendering.cjs`

Python validation uses the isolated Phase 0 Python 3.12 environment and advisory-fixed pytest 9.0.3, empty DATABASE_URL, mock provider keys and disposable local data. Browser tooling is isolated outside product dependencies: Playwright, axe-core, Chart.js 4.4.3 and local fonts. The existing Tailwind CDN runtime is cached for repeatability. `STITCH_QA_MODULES`, `STITCH_QA_TAILWIND`, and `STITCH_QA_BASE` point to isolated tooling, cached CDN JS and the local Flask server. Default browser is installed Edge 156.0.4314.42; no framework or design-system replacement was introduced.

```powershell
node tests/trend-rendering.cjs
node tests/analytics-hook.cjs
node tests/stitch-truth.cjs
node tests/trend-data-truth.cjs
node tests/trend-data-browser.cjs --output <absolute-evidence-directory>
node tests/stitch-browser-qa.cjs --output <absolute-shared-tools-directory>
..\.venv-phase0-validation\Scripts\python.exe -m pytest tests/ backend/test_seo_schema.py -q -p no:cacheprovider --basetemp=<fresh-directory>
```

The CI workflow now runs all four Node unit suites and includes backend SEO tests. The existing full Python suite includes API/schema/security/SEO contracts. No npm build exists; verification includes frontend JS syntax, Python compilation/import, actual browser assets and Flask routes.

## Remaining limits and release gate

- **Production NO-GO:** derived analytics/storage permission not confirmed; existing-record retention compliance not established. Obtain applicable approval or separately authorize compliant feature/storage changes before release.
- Real YouTube/Groq smoke is **UNVERIFIED**: no authorized live key or isolated database target supplied. Production analytics endpoints were not exercised because searches persist observations. Preview browser calls are mocked; HTML/assets are verified independently.
- Preview and GitHub CI evidence for the final branch is recorded in the draft PR and final delivery. A local fixture pass does not establish real-provider correctness.
- Tests use Edge headless, not physical devices or iOS Safari. Automated axe is not a full manual accessibility certification.
- Bandit's established high-severity gate passes; two pre-existing medium findings (temporary directory and development bind address) remain documented. One ReportLab deprecation warning remains. Runtime and development dependency scopes are reported separately.
- Existing unreadable ignored `pytest-cache-files-5s64s6s_/` was left untouched.

**Stop for owner review. No production merge/deploy authorization is implied.**
