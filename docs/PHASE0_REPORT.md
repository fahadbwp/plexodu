# Phase 0 verification evidence

Baseline: c04cd5fc9d6c7a969550dea7d3a70f022736696a; Python 3.14.7; pytest 9.1.1; Node v24.21.0.
Python baseline: 226 passed, one pytest cache permission warning. Node: both regression groups passed.

## 0.1 deletion references

Command for each candidate: `git grep -n -I -F -e <filename> -e <module-stem> -- .` (all tracked code, tests, configuration and documentation).

### backend/services/mock_api.py
```text
backend/services/mock_api.py:19:    from services.mock_api import fetch_youtube_data, fetch_tiktok_data
tests/test_phase3_security.py:61:    with patch("requests.get", return_value=mock_resp), patch("services.real_api.get_yt_api_key", return_value="test_mock_api_key"):
tests/test_phase3_security.py:67:        assert "test_mock_api_key" not in res.get("error", "")
```

### backend/services/gemini_service.py
```text
(no references)
```

### backend/audit_runner.py
```text
(no references)
```

### backend/qa_test_suite.py
```text
(no references)
```

### render.yaml
```text
.agents/skills/vibe-coding-guardian/SKILL.md:27:Always test mental rendering across 4 core viewports:
.agents/skills/vibe-coding-guardian/SKILL.md:53:  - This guarantees the user's browser renders the changes instantly on reload without stale cache.
.github/workflows/ci.yml:91:      - name: Trend Analyzer rendering regressions
.github/workflows/ci.yml:92:        run: node tests/trend-rendering.cjs
README.md:101:Do not place secrets in `vercel.json`, `render.yaml`, source code or frontend JavaScript.
README.md:114:- XSS-safe DOM rendering in standalone tool interfaces.
docs/production-qa-report.md:47:| **BUG-01** | P1 | YouTube SEO Studio | Blank iframe rendered | Broken `localhost:5173` iframe embed | Replaced with native 2-column SEO Studio UI | **FIXED** |
docs/production-qa-report.md:80:- Strips `<think>...</think>` internal tags for clean client rendering.
docs/trend-analyzer-practical.md:31:226 automated tests passed locally using mock keys and external HTTP blocked; JavaScript syntax and git diff whitespace checks passed. Updated three legacy tests whose fixtures/assertions relied on swallowed API errors or future-dated scans. Added 16 regression cases plus a Node-based DOM rendering check.
docs/trend-analyzer-practical.md:33:PDF export was rendered and inspected; PDF/CSV response and baseline contents were tested. Targeted frontend DOM rendering checks passed for momentum, escaping, tags, titles, sentiment and forecast text. Browser layout could not be verified because Chromium download failed. No real YouTube/Groq credentials, production database or Vercel deployment were validated in this environment. Distributed quota protection, AI Strategist fallback redesign, and wider app hardening are outside this focused release.
frontend/js/tools/competitor-audit.js:63:    renderAuditResults(data);
frontend/js/tools/competitor-audit.js:72:function renderAuditResults(data) {
frontend/js/tools/trend-analyzer.js:189:  renderTrendingList(filtered, q);
frontend/js/tools/trend-analyzer.js:216:    renderKpis(data.kpis || {});
frontend/js/tools/trend-analyzer.js:217:    renderViewsChart(data.timeSeries || [], activeCategory);
frontend/js/tools/trend-analyzer.js:218:    renderCategoryChart(data.catBreakdown || []);
frontend/js/tools/trend-analyzer.js:219:    renderTrendingList(currentVideos, activeQuery);
frontend/js/tools/trend-analyzer.js:223:      renderDeepIntelligence(ytData);
frontend/js/tools/trend-analyzer.js:237:    renderKpis({});
frontend/js/tools/trend-analyzer.js:238:    renderViewsChart([], activeCategory);
frontend/js/tools/trend-analyzer.js:239:    renderCategoryChart([]);
frontend/js/tools/trend-analyzer.js:258:function renderKpis(kpis) {
frontend/js/tools/trend-analyzer.js:307:function renderViewsChart(timeSeries, categoryName) {
frontend/js/tools/trend-analyzer.js:402:function renderCategoryChart(catBreakdown) {
frontend/js/tools/trend-analyzer.js:472:function renderTrendingList(videos, query) {
frontend/js/tools/trend-analyzer.js:564:function renderDeepIntelligence(ytData) {
frontend/js/tools/trend-analyzer.js:829:  renderLowerChart(filtered, range);
frontend/js/tools/trend-analyzer.js:833:function renderLowerChart(dataPoints, range = "all") {
frontend/js/tools/video-analyzer.js:123:    renderVideoResults(data);
frontend/js/tools/video-analyzer.js:132:function renderVideoResults(data) {
netlify.toml:11:# Replace https://smtas-backend.onrender.com with your actual backend URL after deploying backend
netlify.toml:14:  to = "https://smtas-backend.onrender.com/api/:splat"
tests/test_production_hardening.py:22:def test_tool_renderers_do_not_use_inline_event_handlers():
tests/test_tool_contracts.py:436:        "videoDescription must use textContent for safe plain-text rendering with zero XSS"
tests/trend-rendering.cjs:1:// Run: node tests/trend-rendering.cjs. Targeted DOM rendering, not layout tests.
tests/trend-rendering.cjs:12:context.renderTrendingList([video],'');
tests/trend-rendering.cjs:17:context.renderTrendingList([video],'');
tests/trend-rendering.cjs:20:context.renderDeepIntelligence({keyword:'Minecraft',youtube_tags:['Minecraft'],seo_title_ideas:['Minecraft: A Guide'],sentiment:{positive_score:0.5,neutral_score:99.5},trend_intelligence:{status:'baseline',forecast:{available:false,reason:'Need history'}}});
tests/trend-rendering.cjs:26:console.log('PASS: momentum/missing values, attribute escaping, tags, titles, sentiment, baseline rendering');
tests/trend-rendering.cjs:30:context.renderDeepIntelligence({trend_intelligence:{historical_context:{'1d':{status:'available',change_pct:5}},forecast:{available:false}}});
tests/trend-rendering.cjs:39:context.renderLowerChart([{date:'2026-10-11 06:00',views:100}]);
```

### netlify.toml
```text
backend/test_seo_schema.py:95:            self.assertNotIn("smtas-trend.netlify.app", text, f"Staging URL found in {fpath}")
```

### frontend/_redirects
```text
tests/test_phase4_seo_vercel.py:130:    def test_tool_redirects_use_301(self):
```

- `ads.txt` byte comparison: identical=True. Public URL references resolve through Vercel to frontend copies; retained conservatively because root URL references exist.
- `favicon.ico` byte comparison: identical=True. Public URL references resolve through Vercel to frontend copies; retained conservatively because root URL references exist.
- `favicon.png` byte comparison: identical=True. Public URL references resolve through Vercel to frontend copies; retained conservatively because root URL references exist.
- `apple-touch-icon.png` byte comparison: identical=True. Public URL references resolve through Vercel to frontend copies; retained conservatively because root URL references exist.

Email service retained: its dedicated source-existence security test is outside the explicit test-import deletion allowance. No tests removed.
AUTH_RATE_LIMIT_PER_MIN retained: backend/services/security_guard.py still reads it.
Special checks: test_phase3_security.py contains only mock API key literals; test_phase4_seo_vercel.py checks Vercel redirects, not frontend/_redirects.

## Credentials discovery
Current tracked files and last 50 commits: credential patterns found only README.md:76, a confirmed generic local Postgres example. No real values reproduced.
GEMINI.md and .agents contain design instructions; retained. Public AdSense publisher identifier retained.
