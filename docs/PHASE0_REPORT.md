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

## 0.2 requirements and compatibility
Fresh CPython 3.12.15 environment installed requirements-dev.txt; 226 tests pass. The pre-existing dependency-contract test now checks pytest in requirements-dev.txt and psycopg2-binary in runtime requirements. Production smoke job still installs runtime only. Vercel @vercel/python uses root requirements.txt; no deployment build override was added.

## 0.3 secrets review
Pattern and high-entropy scans covered 50 main commits / 268 unique blobs, including tooling files. Zero high-entropy candidates. Only credential-pattern candidate was the generic README.md:76 local database example. No credentials or personal details found in GEMINI.md or .agents. This local discovery is not a claim of a completed GitHub Gitleaks run.

## 0.4 scanner discovery
Bandit: B108 at backend/app.py:59 (Vercel ephemeral DATA_DIR default), B104 at backend/app.py:975 (development server interface). Both medium, retained/report-only; no nosec suppression. High-severity gate passes with no exclusions. Full scan metrics also include low findings.

Runtime advisory remediation (all dependency changes verified with 226 Python tests, Node regressions and entrypoint import):
- flask 3.0.3 -> 3.1.3: PYSEC-2026-2151.
- flask-cors 4.0.1 -> 6.0.0: PYSEC-2024-71, PYSEC-2026-1383, PYSEC-2026-1384, PYSEC-2026-1385.
- werkzeug 3.0.3 -> 3.1.9: PYSEC-2026-1860, PYSEC-2026-2044, PYSEC-2026-2045, PYSEC-2026-2046, PYSEC-2026-2320, PYSEC-2026-3417, PYSEC-2026-4312.
- requests 2.32.3 -> 2.33.0: PYSEC-2026-1872, PYSEC-2026-2275.
- python-dotenv 1.0.1 -> 1.2.2: PYSEC-2026-2270.

## Task status

| Task | Status | Commit | Notes |
| --- | --- | --- | --- |
| 0.0 baseline | done | c04cd5f (base) | Clean fresh GitHub main clone; new branch; 226 tests + Node pass. Remote SHA rechecked after implementation. |
| 0.1 cleanup | done | 376f526 | Seven verified stale files removed; email service/root assets retained under safer skip rule; no tests deleted. |
| 0.2 requirements | done | 75c42da | Runtime/dev split, all pytest jobs updated, fresh CPython 3.12.15 install and 226 tests pass. |
| 0.3 secrets | done | none, verification only | Current tracked files and last 50 main commits reviewed; no likely genuine credential detected. |
| 0.4 CI | done | 0992264 | Ruff/high Bandit/pip-audit block; release-gate/Gitleaks retained; five vulnerable runtime pins patched and verified. |
| 0.5 health | done | cf49a1f | Five health tests; independent bounded probe; no secrets or upstream quota usage. |
| 0.6 environment | done | 3b4ca90 | Presence-only checker; production PostgreSQL docs; no SQLite default in example. |
| 0.7 analytics/SEO | done | 5979896 | Disabled consent-gated hook on all 10 pages, disclosure, Node tests; canonicals already matched. |
| 0.8 documentation | done | this documentation commit | README, environment guide, technical debt and this evidence report. |

## Final verification

- Fresh CPython 3.12.15 environment with `requirements-dev.txt` installed. Initial baseline used host Python 3.14.7; both ran the original 226 tests successfully.
- `python -m pytest tests/ -q -p no:cacheprovider`: **231 passed**, one upstream ReportLab deprecation warning. Cache provider disabled after baseline encountered Windows cache permissions.
- `python -m pytest tests/ backend/test_seo_schema.py -q -p no:cacheprovider`: **236 passed**. The extra five are the existing schema suite; the repository count increased only by the five new health tests. No existing test was deleted.
- Targeted SEO/schema verification: **36 passed**.
- `node tests/trend-rendering.cjs`: both existing regression groups pass (Node v24.21.0).
- `node tests/analytics-hook.cjs`: placeholder makes zero requests, consent required, privacy signals respected, delayed consent and load-once checks pass. Also included in CI.
- `ruff check backend --select E9,F63,F7,F82`: passed.
- `bandit -r backend --severity-level high --confidence-level medium`: passed; no high findings or rule exclusions. Medium findings remain visible in the separate CI report step.
- `pip-audit -r requirements.txt --format=json --output=...`: **no known vulnerabilities found**, exit 0 after remediation; no ignores. The 27 discovery entries include duplicate advisory IDs; affected packages and unique IDs are listed above.
- `python -c "import api.index"`: passed with mock CI environment.
- `git diff --check`: passed.
- All 10 canonical URLs match sitemap entries exactly; robots.txt has the Sitemap line. Existing Vercel rewrite/redirect and trailing-slash rules support these entries, including privacy.html and terms.html. No sitemap edits were needed.
- Protected services, database models/schema, GEMINI.md and .agents have no diff against main. HTML diffs contain only the new hook tags and authorized privacy paragraph; no CSS/layout edits.

### Remaining limits and skipped subitems

- Email service and both dedicated tests retained conservatively; root asset copies retained. Byte comparisons and references are recorded above. SMTP/EMAIL configuration remains only in the retained legacy service; the public example/config already contained no such settings. AUTH_RATE_LIMIT_PER_MIN remains read by security_guard.py.
- No real PostgreSQL, YouTube or Groq calls were made. PostgreSQL driver timeout configuration and failures are mocked; local health uses SQLite. Existing database bootstrap can still fail before health is served, as documented in TECH_DEBT.md.
- No browser/device visual testing or production Vercel deployment was performed. HTML edits are narrowly limited and Node/SEO checks passed.
- Gitleaks remains blocking in GitHub Actions but was not executed locally. Local credential discovery is evidence of the stated patterns/history review, not a complete security guarantee.
- All four medium Bandit findings (including lower-confidence findings) are listed below for review. None was suppressed; existing product logic is preserved.
- Analytics is inactive. Consent requirements must be reviewed before any future activation and consent UI integration; Phase 0 creates neither active tracking nor a real measurement ID.
- Nothing was pushed, merged, deployed or published. No GitHub Actions run is claimed. No unresolved high-severity scanner finding remains in local results.

### Full medium Bandit discovery (all confidence levels)

- `backend\app.py:61` B108, severity MEDIUM, confidence MEDIUM: Probable insecure usage of temp file/directory.
- `backend\app.py:1019` B104, severity MEDIUM, confidence MEDIUM: Possible binding to all interfaces.
- `backend\migrate_db.py:124` B608, severity MEDIUM, confidence LOW: Possible SQL injection vector through string-based query construction.
- `backend\migrate_db.py:143` B608, severity MEDIUM, confidence LOW: Possible SQL injection vector through string-based query construction.

### Baseline installed dependency versions (host Python 3.14.7)

```text
beautifulsoup4==4.15.0
blinker==1.9.0
certifi==2026.7.22
charset-normalizer==3.5.2
click==8.5.0
cloudpickle==3.1.2
colorama==0.4.6
defusedxml==0.7.1
Flask==3.1.3
flask-cors==6.0.5
Flask-SQLAlchemy==3.1.1
git-filter-repo==2.47.0
idna==3.20
iniconfig==2.3.1
itsdangerous==2.2.0
Jinja2==3.1.6
joblib==1.6.0
lxml==6.1.3
MarkupSafe==3.0.4
nltk==3.10.3
packaging==26.3
pillow==12.3.0
pip==26.2.1
pluggy==1.6.0
Pygments==2.21.0
pymupdf==1.28.2
pytest==9.1.1
python-dotenv==1.2.4
regex==2026.9.29
reportlab==5.0.1
requests==2.34.2
soupsieve==3.0.4
SQLAlchemy==2.1.4
textblob==0.20.1
tqdm==4.70.1
typing_extensions==4.16.0
urllib3==2.8.0
uv==0.13.1
Werkzeug==3.1.9
yt-dlp==2026.8.19
```

### Final isolated environment versions (Python 3.12.15)

```text
CacheControl==0.14.4
Flask-SQLAlchemy==3.1.1
Flask==3.1.3
Jinja2==3.1.6
MarkupSafe==3.0.4
PyYAML==6.0.3
Pygments==2.21.0
SQLAlchemy==2.1.6
TextBlob==0.18.0
Werkzeug==3.1.9
bandit==1.9.4
blinker==1.9.0
boolean.py==5.0
certifi==2026.10.23
chardet==7.7.0
charset-normalizer==3.5.2
click==8.5.0
cloudpickle==3.1.2
colorama==0.4.6
cyclonedx-python-lib==11.12.0
defusedxml==0.7.1
filelock==4.2.4
flask-cors==6.0.0
gunicorn==22.0.0
idna==3.20
iniconfig==2.3.1
itsdangerous==2.2.0
joblib==1.6.0
license-expression==30.4.4
markdown-it-py==4.2.0
mdurl==0.1.2
msgpack==1.2.3
nltk==3.10.4
packageurl-python==0.17.6
packaging==26.3
pillow==13.0.0
pip-requirements-parser==32.0.1
pip==26.2.2
pip_api==0.0.35
pip_audit==2.10.1
platformdirs==4.13.5
pluggy==1.7.0
psycopg2-binary==2.9.10
py-serializable==2.1.0
pyparsing==3.3.3
pytest==8.4.2
python-dotenv==1.2.2
regex==2026.9.29
reportlab==4.2.2
requests==2.33.0
rich==15.0.0
ruff==0.17.2
sortedcontainers==2.4.0
stevedore==5.9.1
tomli==2.5.0
tomli_w==1.2.0
tqdm==4.70.1
typing_extensions==4.16.0
urllib3==2.8.0
```

## Manual push and pull request

Run from the fresh clone, after reviewing these commits:

```powershell
Set-Location 'C:\Users\Fahad Saleem\Documents\plexodu-main\plexodu-phase0'
git push -u origin chore/phase0-cleanup
gh pr create --repo fahadbwp/plexodu --base main --head chore/phase0-cleanup --title "chore: Phase 0 cleanup and setup" --body-file docs/PHASE0_REPORT.md
```

Inspect history with `git log --oneline main..HEAD` and changes with `git diff --stat main...HEAD`. The final response records the documentation commit SHA and final diff summary without making a self-referential commit hash in this file.
