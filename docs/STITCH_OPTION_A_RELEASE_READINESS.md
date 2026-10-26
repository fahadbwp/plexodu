# Stitch Option A: final mobile clipping and data truth audit

Date: October 26, 2026 (Asia/Karachi)

## Decision and repository identity

**PASS for the scoped local fixture audit; ready for owner review. Live API and physical-device checks remain unverified. No merge or deployment approval is implied.**

- Actual repository: `C:\Users\Fahad Saleem\Documents\plexodu-main\plexodu-phase0`.
- Branch: `feat/stitch-option-a-ui`.
- Requested baseline: `45d16454741384e15c17044774ff4b7346b3871a`.
- Follow-up parent: `77c7e829e30f5a44cfecf31b8e71fd6524bb3d42`. Another process committed the overlapping stabilization and dual-chart work during this audit. At the owner's instruction, that commit is preserved intact; this audit is a separate follow-up, with no amend, reset, or cherry-pick.
- Gate B remains `feat/gate-b-quota-guard` at `8cc12d2977daceae84d12f91db5f9daa148d9ad3`. No Gate B, production backend, database, CI, credentials, merge, push, or deployment changes.
- The parent folder is a separate stale snapshot, not this Git root. An existing unreadable `pytest-cache-files-5s64s6s_/` directory is left untouched.

This report supersedes the earlier blanket responsive/GO claims. Document width alone is insufficient: a parent with `overflow:hidden` can conceal content while `document.scrollWidth` remains equal to viewport width.

## Supplied screenshot review and provenance

All 17 `qa_v2` PNGs were visually inspected from the supplied Antigravity capture directory: Trend Analyzer, Video Analyzer, Competitor Audit, AI Strategist and Tools Hub at 320, 390 and 1440, plus Trend Analyzer's 320 error and empty states.

The mobile PNGs visibly crop headings, intro text, controls, cards and chat. The capture's original DOM, asset/cache state and response recording were not supplied. Replaying exact commit `45d1645` did **not** reproduce every idle heading crop identically. Consequently, no DOM rectangle is invented for a PNG, and no unsupported assertion is made that all supplied crops came from the same cause. The measured before results below come from a controlled replay of that commit, with populated forms and long/unbroken content; its actual component clipping is independently reproducible.

The 72.5M/5.4% figures in the supplied PNGs cannot be certified as live observations from an image. Production HTML/JS does not hardcode those numeric metrics. They are API-response bindings; our repeatable QA explicitly injects these values as labelled fixtures. The original screenshot capture's numeric provenance remains unverified.

## Measurement method and fixes

`tests/stitch-browser-qa.cjs` uses local Flask on `127.0.0.1:5067`, real locally installed web fonts/Chart.js, Edge headless, device scale 1, and widths 320, 390 and 1440. Every API request is fulfilled with deterministic fixtures; external traffic is blocked or fulfilled locally. Every evidence screenshot carries a fixture banner.

It records element rectangles and computed overflow, width/min/max-width, white-space, transform, flex/grid and padding; text ranges are measured separately. H1/H2/H3, paragraphs, searches, FAQ content, cards, badges, chat, links and buttons are inspected against clipping ancestors and the horizontal viewport. The final audit checks **both horizontal and vertical ancestor clipping**, not just document overflow. Before totals reflect the earlier horizontal measurement pass and are not represented as a vertical baseline.

Intentional scroll regions (chat history, long descriptions, upload tables) are recorded separately. A clipped 1px absolute screen-reader table with computed `clip:rect(0px,0px,0px,0px)` is recorded as assistive-only, not visible content; the exemption requires those exact computed characteristics and does not suppress arbitrary hidden content. Axe still checks these accessible tables.

| Component / reproduced root cause | Fix | Functional/visual verification |
|---|---|---|
| Ranked trend titles: line clamp/hidden overflow plus 160px minimum child width; parent panel also masked overflow | Remove title clamp/mask; allow wrapping; `min-width:0`; mobile rows use `minmax(0,1fr)` and put metrics below the title | Long titles and metrics remain readable; filters and search update rows |
| Video/channel headings and tags: intrinsic width of unbroken API content exceeded flex allocation | Container/heading minimums removed; `overflow-wrap:anywhere`; video tags wrap | Long response titles/tags visible at both mobile widths |
| Channel status badge: flex shrink compressed its text into a vertical stack | Header flex row wraps; badge does not shrink; mobile alignment retained | Badge wraps onto its own row; misleading static “Verified” replaced with “Public snapshot” |
| Dynamic chat used legacy wrapper classes; wide bubbles were hidden by chat viewport | Consistent responsive row/avatar/bubble wrappers, shrinking flex children, wrapping code/text and response actions | Long text, apostrophes, quick prompts, clear, copy, script/tag actions and composer exercised |
| KPI headers, search/filter controls and tool CTAs: nowrap/flex/grid constraints | Responsive wrapping, zero minimums, bounded controls, wrapping category chips and CTA labels | Search, every timeframe/category, hub launch links and workflow CTAs exercised |
| Drawer: hidden links remained focusable; focus could escape the open panel | `inert` closed drawer/background, dialog semantics, forward/reverse Tab trap, Escape/close restoration | Every mobile drawer exercised at 320 and 390 |
| Search-looking topbar had no useful search behavior | Native focus action jumps to real tool input; hub opens Trend Analyzer; Ctrl+K works | All desktop topbar actions and shortcuts exercised |
| Copy chips were clickable spans; reply text interpolated into inline handlers | Native buttons and event listeners capture reply text safely | Keyboard activation and quoted reply copy exercised |
| Error, empty and draft-success text failed contrast; empty-history tabs were faded despite remaining interactive | Existing readable tokens for feedback; semantic empty-state classes; no opacity reduction on interactive history tabs | Axe runs on every captured state, including no-history and request failures |

The inherited fixes in `77c7e82` are retained; this follow-up adds the remaining badge/contrast/keyboard/data-copy corrections. Asset versions for the five tool pages advance to `28.3`. All original page IDs remain present; duplicate attributes and duplicate IDs are absent.

### Example measured rectangles at 320px

Full precision, vertical coordinates, styles and ancestors are in the committed JSON. Horizontal coordinates below are rounded to two decimal places.

| Element | Before left / right / width (px) | Visible clipping ancestor before | After left / right / width (px) |
|---|---|---|---|
| `#videoTitle` text fragment / wrapped heading | 19 / 1703.08 / 1684.08 | `.stitch-app-shell`, 0–320, `overflow-x:hidden` | 19 / 301 / 282 |
| `#channelName` | 19 / 1703.08 / 1684.08 | `.stitch-app-shell`, 0–320, `overflow-x:hidden` | 19 / 301 / 282 |
| User chat bubble | -829.64 / 15.33 / 844.97 | `#chatMessages`, 19–301, `overflow-x:hidden` | 23 / 297 / 274 |
| Assistant chat bubble | 71 / 917.47 / 846.47 | `#chatMessages`, 19–301, `overflow-x:hidden` | 69 / 297 / 228 |

Chat history intentionally scrolls vertically; older messages need not all be visible simultaneously. The horizontal text remains within the history viewport and the composer stays outside that scroll region. The newly captured ten mobile before images contain 49 both-axis clipping observations; their corresponding ten after images have zero. This subset is separate from the 54-state horizontal baseline (119 observations) and 60-state final audit.

## Data truth findings

| Display | Actual source / classification | Correct behavior |
|---|---|---|
| 72.5M views | `data.kpis.totalViews`; backend sums returned videos' public lifetime view counts. Original PNG provenance unverified; explicitly mocked in this audit | “Views in Returned Sample”; lifetime totals, not views earned during selected window |
| 5.4% engagement | `data.kpis.avgEngagement`; arithmetic mean of available video `(likes + comments) / views * 100` ratios, rounded to one decimal | Sample ratio, not private YouTube Studio audience analytics. Missing likes/metric is unavailable, while an actual zero remains zero |
| “Live YouTube RSS” / live-source badges | Unsupported source/freshness claims; implemented feed uses YouTube Data API v3, not RSS. The exact RSS text is absent from baseline source; a screenshot is not a freshness record | API snapshot; freshness unavailable. Explicit cached/stale flags are labelled when provided. Service cache TTL is 900 seconds; current response does not prove a collection timestamp |
| Shorts 55%, Longform 30%, Live 15% | Static HTML decoration, no response binding or measured format breakdown | Removed, explicitly unavailable |
| KPI sparkline and radial virality arc | Static decorative shapes without observation data | Removed, not presented as analytics |
| Momentum and rising cohort | Midpoint percentile of estimated lifetime views/hour within current sample; count is number above index 40 | Neutral `score / 100 idx`, actual returned denominator; not growth %, acceleration or probability. Removed fabricated fallback of 18 |
| Category totals | Sum of lifetime views in each category of returned sample | Labelled sample totals, not global category market share |
| Upload-age chart | API `timeSeries` buckets lifetime totals by publication age | Bars retain exact response labels/values, including duplicate labels. No invented historical dates, velocities or synthetic historical curve |
| Historical chart | Saved `trend_intelligence.timeline` observations; smoothed series is explicitly labelled and raw observations retained when different | Empty, one-observation baseline and multiple-observation cases exercised; authentic timestamps retained; a single baseline has no invented line |
| FAQ momentum/sentiment | Previous copy falsely described channel baseline/acceleration inputs and transformers | Describes actual percentile calculation and TextBlob plus Urdu/Hindi lexicon rules on up to 50 requested comments from leading video; limited sample, not whole audience |
| Missing deep-summary metrics | Previously fell back to “Emerging”/“Normal” without evidence | “Unavailable” |

No production fixture response or fallback numeric sample was introduced. Fixtures exist only in the local browser test harness. API failures/empty/quota responses clear previous deep results and show unavailable metrics instead of stale success values.

## Follow-up changed files

- `frontend/css/style.css`: readable feedback, empty states and no-history tabs; channel heading/badge wrapping.
- `frontend/js/tools/{trend-analyzer,video-analyzer,competitor-audit}.js`: unavailable summaries, keyboard copy chips and semantic empty states.
- `frontend/tools/{trend-analyzer,video-analyzer,competitor-audit,ai-strategist,index}.html`: asset version 28.3; accurate trend FAQ/metadata and channel snapshot label.
- `tests/stitch-browser-qa.cjs`: both-axis measurement, separately recorded assistive-only clipping, all-state axe checks, chart observation cases, keyboard copy checks and non-obscuring full-page fixture notice.
- `tests/stitch-truth.cjs` and `tests/test_stitch_option_a_critical_fixes.py`: unavailable-summary regressions and updated asset-version contract.
- This report and `docs/qa/stitch-final-audit/`: committed measurements, source fingerprints and 20 before/after mobile PNGs.

The inherited `tests/test_stitch_dual_chart_contracts.py`, Google verification page and all other concurrent work are unchanged by this follow-up.

## Functional, accessibility and regression results

| Check | Final result |
|---|---|
| Browser states at 320 / 390 / 1440 | **60 passed**; 0 horizontal or vertical clipping failures |
| Interactive assertions | **96 passed**, 0 failed |
| Axe WCAG A/AA + 2.1 rules | 0 violations in all 60 captured states |
| Browser script errors | 0 |
| Full Python, SEO, frontend/security/schema contracts | **329 passed**, one existing ReportLab deprecation warning |
| Node rendering / analytics hook / data truth regressions | All three suites passed |
| Ruff CI correctness selectors | Passed |
| Bandit high-severity CI gate | Passed; two existing medium findings remain |
| Runtime `pip-audit -r requirements.txt` | No known vulnerabilities found |
| Build/static verification | All frontend JS syntax, Python compile/import, unique attributes/IDs, original IDs retained, local Flask routes passed |

Raw before replay: **119 horizontal clipping observations across 54 states**. Final after: **0 on either axis across 60 states**. All ten final mobile viewport previews were visually reviewed in addition to per-element measurement; full-page evidence is retained below.

Test-count reconciliation: baseline `45d1645` collected 317 tests under `tests/` plus five in `backend/test_seo_schema.py` = 322. The initial run had 320 passes and two failures: a stale missing-key mock patched an unused module variable, and a sitemap assertion expected retired `.html` legal URLs. The retained corrections target `services.real_api.get_yt_api_key` and actual clean canonical routes; no test was removed, skipped, or weakened to conceal product failures. The concurrent commit adds seven dual-chart tests: 324 + 5 = **329**. The asset-version contract now expects `28.3` consistently.

The fixture tests submit each tool rather than merely loading it. They cover empty/error/success, Trend Analyzer quota/stale/missing/changed data, history absent/baseline/multi-point, sample buttons, copy/draft controls, chart labels and values, quick prompts, reply actions, clear, workflow/launch links, all category/timeframe controls, drawer open/close/Escape, focus restoration and forward/reverse keyboard traversal. Each visible local navigation destination is checked through Flask. PDFs/CSVs are mocked downloads: this verifies the UI download action, not real export generation (covered separately by Python regressions).

## Before / after evidence

[Evidential summary, selected rectangles, source hashes and original screenshot inventory](qa/stitch-final-audit/evidence.json). Full per-state rectangles/styles, ancestor records, axe findings, API-request paths and functional assertions remain in the linked local raw evidence directory recorded there. Counts are observations, not counts of distinct bugs.

| Screen | 320 before | 320 after | 390 before | 390 after |
|---|---|---|---|---|
| Trend Analyzer | [PNG](qa/stitch-final-audit/before/trend-analyzer-320.png) | [PNG](qa/stitch-final-audit/after/trend-analyzer-320.png) | [PNG](qa/stitch-final-audit/before/trend-analyzer-390.png) | [PNG](qa/stitch-final-audit/after/trend-analyzer-390.png) |
| Video Analyzer | [PNG](qa/stitch-final-audit/before/video-analyzer-320.png) | [PNG](qa/stitch-final-audit/after/video-analyzer-320.png) | [PNG](qa/stitch-final-audit/before/video-analyzer-390.png) | [PNG](qa/stitch-final-audit/after/video-analyzer-390.png) |
| Competitor Audit | [PNG](qa/stitch-final-audit/before/competitor-audit-320.png) | [PNG](qa/stitch-final-audit/after/competitor-audit-320.png) | [PNG](qa/stitch-final-audit/before/competitor-audit-390.png) | [PNG](qa/stitch-final-audit/after/competitor-audit-390.png) |
| AI Strategist | [PNG](qa/stitch-final-audit/before/ai-strategist-320.png) | [PNG](qa/stitch-final-audit/after/ai-strategist-320.png) | [PNG](qa/stitch-final-audit/before/ai-strategist-390.png) | [PNG](qa/stitch-final-audit/after/ai-strategist-390.png) |
| Tools Hub | [PNG](qa/stitch-final-audit/before/tools-hub-320.png) | [PNG](qa/stitch-final-audit/after/tools-hub-320.png) | [PNG](qa/stitch-final-audit/before/tools-hub-390.png) | [PNG](qa/stitch-final-audit/after/tools-hub-390.png) |

After the 60-state run, a separate ten-case mobile capture pass also passed both-axis geometry and axe. The fixture notice is placed after the footer for full-page screenshots so it does not obscure product content.

All PNGs above are full-page captures with exactly the stated image width, not cropped previews. They use the same labelled fixture dataset. Desktop and every additional state are retained in the raw evidence directory. Intentionally long API strings are wrapping stress tests, not proposed product copy.

## Reproduction and limitations

Use the isolated Phase 0 Python environment (`..\.venv-phase0-validation\Scripts\python.exe`, Python 3.12). Start local Flask with development/test mock keys or production-mode import smoke settings, **empty `DATABASE_URL`**, `VERCEL=1` and `DATA_DIR` pointing to a disposable QA directory; never load production credentials. Serve `api.index:app` on `127.0.0.1:5067` without debugger/reloader.

The browser harness requires an isolated `STITCH_QA_MODULES` directory containing Playwright, axe-core, Chart.js 4.4.3, `@fontsource-variable/plus-jakarta-sans`, `@fontsource-variable/inter` and `@fontsource/material-symbols-outlined`. Dependencies were installed outside this repository, not added to product dependencies. It defaults to installed Edge; `STITCH_QA_BROWSER` can select a separately installed browser.

```powershell
node tests/stitch-browser-qa.cjs --output <absolute-QA-directory>
# Full-width mobile success images only, with fixture notice below content:
node tests/stitch-browser-qa.cjs --screens-only --output <absolute-mobile-evidence-directory>
# Historical replay; diagnostic failures are expected:
node tests/stitch-browser-qa.cjs --before --output <absolute-before-directory>
node tests/trend-rendering.cjs
node tests/analytics-hook.cjs
node tests/stitch-truth.cjs
..\.venv-phase0-validation\Scripts\python.exe -m pytest tests/ backend/test_seo_schema.py -q -p no:cacheprovider --basetemp=<fresh-disposable-directory>
```

- **Real YouTube/Groq smoke: UNVERIFIED.** No authorized live key was supplied. No production credentials were used. Fixture values do not constitute real-world analytics proof.
- Tested browser: Edge 156.0.4314.42 headless on Windows, emulated widths with real local fonts. Physical devices, iOS Safari, Firefox, manual screen-reader operation, touch interaction and device zoom remain unverified. Automated axe plus keyboard checks are not a claim of complete WCAG conformance.
- No npm/package build pipeline exists in this Flask/static repository. Build verification means Python compilation/import, syntax checking all frontend JS, HTML attribute/ID contracts, asset-backed browser rendering and local Flask routes; no deployment artifact was generated.
- Ruff uses the repository CI selector `E9,F63,F7,F82`. Bandit's CI high-severity gate passes; existing medium-confidence findings B108 (`backend/app.py:125`, temporary directory) and B104 (`backend/app.py:2329`, development bind address) remain unchanged. No broad “zero security findings” claim.
- `pip-audit` result is scoped to declared runtime `requirements.txt`; it does not certify all developer/browser tooling. Gitleaks is unavailable locally; its GitHub Actions job was not executed here.
- One existing ReportLab `ast.NameConstant` deprecation warning remains. The ignored/unreadable cache directory was not changed.

**Stop for owner approval. Do not merge, push, deploy or alter Gate B as part of this audit.**
