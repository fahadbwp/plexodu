"""
Tests for Stitch Option A Dual-Chart Contracts & Data Integrity
==============================================================
Validates:
1. Chart A: Lifetime Views by Upload Age (Accumulated cross-sectional cohort views)
2. Chart B: Time-Series View Trajectory (Longitudinal multi-scan audited observations)
3. Accessible Table Fallbacks (.sr-only #viewsChartA11y and #viewsTrajectoryA11y)
4. Screen Reader CSS utility (.sr-only in style.css)
5. Zero semantic conflation (Upload age is NEVER labeled as velocity, views/hr, or surge)
6. Baseline observation integrity (Single point: showLine=false, real date, no invented ranges)
7. Multi-scan trajectory delta and honest unavailable states
8. Backend API preservation of timeSeries and category breakdown
"""

import os
import sys
import json
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"
TOOLS_DIR = FRONTEND_DIR / "tools"
CSS_PATH = FRONTEND_DIR / "css" / "style.css"
TREND_HTML_PATH = TOOLS_DIR / "trend-analyzer.html"
TREND_JS_PATH = FRONTEND_DIR / "js" / "tools" / "trend-analyzer.js"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def get_flask_module():
    import importlib.util
    if "main_flask_app" in sys.modules:
        return sys.modules["main_flask_app"]
    app_py_path = BACKEND_DIR / "app.py"
    spec = importlib.util.spec_from_file_location("main_flask_app", str(app_py_path))
    flask_module = importlib.util.module_from_spec(spec)
    sys.modules["main_flask_app"] = flask_module
    spec.loader.exec_module(flask_module)
    return flask_module


@pytest.fixture(scope="module")
def app_client():
    os.environ["GROQ_API_KEY"] = "gsk_mock_test_key"
    mod = get_flask_module()
    app = mod.app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ── Test 1: Chart A DOM & Accessibility Markup ──────────────────────────────
def test_chart_a_dom_and_a11y_markup():
    """Verify Chart A has proper heading, subtitle, badge, canvas, and accessible table container."""
    html = TREND_HTML_PATH.read_text(encoding="utf-8")
    
    assert 'id="pulseViewsChart"' in html, "Chart A canvas #pulseViewsChart missing"
    assert 'id="viewsChartA11y"' in html, "Accessible container #viewsChartA11y missing"
    assert 'class="sr-only"' in html, "sr-only class missing from accessible container"
    assert 'aria-live="polite"' in html, "aria-live polite missing from accessible container"
    
    # Subtitle and badge verification
    assert "Lifetime views by upload age" in html
    assert "Accumulated lifetime views across video age buckets in the current sampled cohort" in html
    assert "Sampled Age Brackets" in html


# ── Test 2: Chart B DOM & Accessibility Markup ──────────────────────────────
def test_chart_b_dom_and_a11y_markup():
    """Verify Chart B has proper heading, subtitle, timeframe tabs, and accessible container."""
    html = TREND_HTML_PATH.read_text(encoding="utf-8")
    
    assert 'id="viewsChart"' in html, "Chart B canvas #viewsChart missing"
    assert 'id="viewsChartEmpty"' in html, "Chart B empty placeholder missing"
    assert 'id="viewsTrajectoryA11y"' in html, "Accessible container #viewsTrajectoryA11y missing"
    assert "Time-Series View Trajectory" in html
    assert "Audited view changes across repeated observations of this topic over time" in html
    
    # Check all 5 timeframe tabs
    for timeframe in ["all", "1d", "7d", "30d", "90d"]:
        assert f'data-range="{timeframe}"' in html, f"Timeframe tab {timeframe} missing"


# ── Test 3: Screen Reader .sr-only CSS Utility ──────────────────────────────
def test_sr_only_accessibility_css():
    """Ensure style.css defines standard WCAG screen reader hidden styles."""
    css = CSS_PATH.read_text(encoding="utf-8")
    
    assert ".sr-only" in css, ".sr-only utility missing from style.css"
    match = re.search(r"\.sr-only\s*\{([^}]+)\}", css)
    assert match is not None, ".sr-only definition block not found"
    rule_body = match.group(1)
    
    assert "position: absolute" in rule_body
    assert "width: 1px" in rule_body
    assert "height: 1px" in rule_body
    assert "overflow: hidden" in rule_body
    assert "clip: rect(0, 0, 0, 0)" in rule_body or "clip: rect(0 0 0 0)" in rule_body


# ── Test 4: Chart A Data Contract & Semantic Integrity ──────────────────────
def test_chart_a_data_contract_and_tooltips():
    """Verify Chart A tooltips state upload age & accumulated views, never velocity/growth."""
    js = TREND_JS_PATH.read_text(encoding="utf-8")
    
    # Ensure renderViewsChart function exists
    assert "function renderViewsChart(timeSeries, categoryName)" in js
    
    # Tooltip must explicitly identify upload age
    assert "Upload Age:" in js
    assert "Accumulated views:" in js
    
    # Must NOT conflate with velocity or surge
    chart_a_match = re.search(r"function renderViewsChart\(timeSeries, categoryName\)\s*\{(.*?)\nfunction ", js, re.DOTALL)
    assert chart_a_match is not None
    chart_a_code = chart_a_match.group(1)
    
    assert "views/hr" not in chart_a_code
    assert "velocity" not in chart_a_code.lower()
    assert "growth rate" not in chart_a_code.lower()
    assert "surge" not in chart_a_code.lower()
    
    # Verifies dynamic population of #viewsChartA11y table
    assert "viewsChartA11y" in chart_a_code
    assert "<table" in chart_a_code
    assert "<caption" in chart_a_code
    assert "Upload Age Bucket" in chart_a_code
    assert "Accumulated Views" in chart_a_code


# ── Test 5: Chart B State Machine & Baseline Integrity ──────────────────────
def test_chart_b_state_machine_and_baseline_integrity():
    """Verify Chart B handles empty, baseline (single point), and multi-point curves correctly."""
    js = TREND_JS_PATH.read_text(encoding="utf-8")
    
    assert "function renderLowerChart(dataPoints, range" in js
    
    chart_b_match = re.search(r"function renderLowerChart\(dataPoints, range[^{]*\{(.*?)\nfunction [a-zA-Z]", js, re.DOTALL)
    assert chart_b_match is not None
    chart_b_code = chart_b_match.group(1)
    
    # State A: Empty history
    assert "Historical data unavailable" in chart_b_code
    
    # State B: Single observation baseline
    assert "showLine: false" in chart_b_code
    assert "Recorded Observation" in chart_b_code
    assert "One observation recorded" in chart_b_code
    
    # State C: Multi-point trajectory
    assert "Smoothed Trajectory" in chart_b_code
    assert "Raw Observations" in chart_b_code
    
    # Accessible table container
    assert "viewsTrajectoryA11y" in chart_b_code
    assert "Audited view trajectory over time" in chart_b_code


# ── Test 6: Zero Fabricated Metrics & Synthetic Curves ──────────────────────
def test_zero_fabricated_metrics_and_synthetic_curves():
    """Verify neither static mock curves nor synthetic points are injected."""
    html = TREND_HTML_PATH.read_text(encoding="utf-8")
    js = TREND_JS_PATH.read_text(encoding="utf-8")
    
    # No hardcoded fake data points in HTML
    for forbidden in ["Shorts 55%", "Longform 30%", "Live 15%", "100 Peak Viral"]:
        assert forbidden not in html
        assert forbidden not in js
        
    # No imaginary past time generator functions
    assert "buildSpreadLabels" not in js


# ── Test 7: Backend API Preserves timeSeries Buckets ────────────────────────
def test_backend_trending_feed_contract(app_client):
    """Verify backend /api/trending-feed outputs valid timeSeries and catBreakdown."""
    mock_yt = {
        "status": 200,
        "daily_metrics": [{"date": "2026-10-25", "views": 450000, "likes": 25000, "comments_count": 1200, "shares": 0}],
        "engagement_rate": 5.8,
        "virality_score": 82,
        "sentiment": {"positive_score": 60, "neutral_score": 30, "negative_score": 10},
        "comments": ["Great video!"],
        "top_videos": [
            {
                "id": "vid123",
                "title": "Quantum Computing Breakthrough",
                "channel": "Tech Frontier",
                "category": "Science & Technology",
                "views": 450000,
                "likes": 25000,
                "comments": 1200,
                "engagement": 5.8,
                "momentumScore": 82,
                "hoursAgo": 6
            }
        ],
        "kpis": {
            "totalViews": 450000,
            "avgEngagement": 5.8,
            "fastestCategory": "Science & Technology",
            "topCategoryViews": 450000,
            "risingCount": 1,
            "totalTracked": 1
        },
        "time_series": [
            {"label": "0–2h old", "views": 0},
            {"label": "2–4h old", "views": 0},
            {"label": "4–8h old", "views": 450000},
            {"label": "8–12h old", "views": 0},
            {"label": "12–24h old", "views": 0},
            {"label": "1–2d old", "views": 0},
            {"label": "2–7d old", "views": 0}
        ],
        "cat_breakdown": [
            {"name": "Science & Technology", "value": 450000, "hue": "#4F46E5"}
        ]
    }
    
    with patch("main_flask_app.fetch_youtube_data", return_value=mock_yt):
        res = app_client.get("/api/trending-feed?category=All")
        assert res.status_code == 200
        data = json.loads(res.data)
        
        assert "timeSeries" in data
        assert len(data["timeSeries"]) > 0
        assert data["timeSeries"][2]["label"] == "4–8h old"
        assert data["timeSeries"][2]["views"] == 450000
        assert "catBreakdown" in data
        assert data["catBreakdown"][0]["name"] == "Science & Technology"
