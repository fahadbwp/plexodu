"""
Tests for Google Stitch Option A Critical Fixes & Release Gate
==============================================================
Covers:
1. No duplicate HTML class attributes
2. Planned Feature non-interactive preview in sidebar/drawer
3. Mobile 320px layout safety (min-width, flex safety, iOS auto-zoom)
4. Trend Analyzer explicit UI state machine and non-misleading placeholders
5. Upstream API error handling
6. Quota limited handling (429)
7. Stale cached response handling
8. AI Strategist chat layout and word-break wrapping
9. Sidebar drawer accessible focus management
10. Cache-busting parameter consistency (v=28.2)
"""

import os
import sys
import json
import re
import glob
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"
TOOLS_DIR = FRONTEND_DIR / "tools"
CSS_PATH = FRONTEND_DIR / "css" / "style.css"
COMMON_JS_PATH = FRONTEND_DIR / "js" / "tools" / "common.js"
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
def flask_mod():
    return get_flask_module()


@pytest.fixture(scope="module")
def client(flask_mod):
    app = flask_mod.app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_no_duplicate_class_attributes_in_tool_pages():
    """Verify that no HTML tag in any tool page contains multiple class="..." attributes."""
    tool_files = list(TOOLS_DIR.glob("*.html"))
    assert len(tool_files) >= 5, "All tool HTML files must be present"

    violations = []
    for tf in tool_files:
        with open(tf, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            tags = re.findall(r'<[a-zA-Z0-9\-]+(\s+[^>]+)>', line)
            for t in tags:
                classes = re.findall(r'class\s*=\s*"[^"]*"', t)
                if len(classes) > 1:
                    violations.append(f"{tf.name}:{idx+1} has {len(classes)} class attributes")

    assert len(violations) == 0, f"Duplicate class attributes detected: {violations}"


def test_pro_preview_is_planned_feature_non_interactive():
    """Verify sidebar and drawer footer cards use a non-interactive 'Planned Feature' preview pill with no dead links or login claims."""
    tool_files = list(TOOLS_DIR.glob("*.html"))
    for tf in tool_files:
        content = tf.read_text(encoding="utf-8")
        assert "stitch-footer-card-pill" in content, f"Missing stitch-footer-card-pill in {tf.name}"
        assert "Planned Feature" in content, f"Missing 'Planned Feature' label in {tf.name}"
        # Ensure dead button or login/billing CTA is not present
        assert 'href="/#faq" class="stitch-footer-card-btn"' not in content, f"Dead CTA link found in {tf.name}"
        assert "stitch-footer-card-btn" not in content, f"Clickable button found in {tf.name}"


def test_mobile_viewport_320_responsive_safety():
    """Verify that CSS contains fine-grained rules for <=374px, <=480px, and prevents iOS auto-zoom."""
    css = CSS_PATH.read_text(encoding="utf-8")

    # Min-width overrides for mobile
    assert ".stitch-hero-info" in css
    assert "min-width: 0" in css

    # Breakpoint <= 374px exists for small mobile
    assert "@media (max-width: 374px)" in css

    # Reduced motion exists
    assert "@media (prefers-reduced-motion: reduce)" in css

    # iOS auto-zoom prevention: font-size 16px on inputs
    assert "font-size: 16px !important;" in css


def test_trend_analyzer_explicit_state_machine_in_js():
    """Verify trend-analyzer.js implements non-misleading placeholders and state badge updates."""
    js = TREND_JS_PATH.read_text(encoding="utf-8")

    assert "updateKpiBadges" in js, "Missing updateKpiBadges state function"
    assert "Cached Snapshot" in js, "Missing Cached Snapshot badge state"
    assert "Unavailable" in js, "Missing Unavailable badge state"
    assert "QUOTA_LIMITED" in js, "Missing QUOTA_LIMITED state handler"

    # Verify placeholder logic does not default to 0 on invalid/error state
    assert 'totalViewsVal.textContent = "—"' in js
    assert 'avgEngVal.textContent = "—"' in js
    assert 'topCatDeltaText.textContent = "Unavailable"' in js


def test_ai_strategist_mobile_chat_safety():
    """Verify AI strategist styles and markup protect against chat bubble and chip clipping."""
    css = CSS_PATH.read_text(encoding="utf-8")

    assert "word-break: break-word;" in css
    assert "overflow-wrap: break-word;" in css
    assert ".stitch-chat-bubble" in css
    assert ".stitch-chips-wrap" in css

    html = (TOOLS_DIR / "ai-strategist.html").read_text(encoding="utf-8")
    assert "stitch-chat-bubble-wrap" in html
    assert "stitch-chat-bubble" in html


def test_sidebar_drawer_accessible_focus_management():
    """Verify common.js captures and restores activeElement on mobile drawer open/close."""
    js = COMMON_JS_PATH.read_text(encoding="utf-8")

    assert "drawerLastFocusedElement" in js
    assert "openSidebarDrawer" in js
    assert "closeSidebarDrawer" in js
    assert "drawerLastFocusedElement.focus()" in js
    assert "Escape" in js


def test_all_tools_cache_busting_version_consistency():
    """Verify all 5 tool pages use the latest cache-busting version v=28.2."""
    tool_files = list(TOOLS_DIR.glob("*.html"))
    for tf in tool_files:
        content = tf.read_text(encoding="utf-8")
        assert "style.css?v=28.2" in content, f"{tf.name} must use style.css?v=28.2"
        assert "common.js?v=28.2" in content, f"{tf.name} must use common.js?v=28.2"


def test_trending_feed_returns_safe_error_on_missing_api_key(client, flask_mod):
    """Verify /api/trending-feed returns safe 500 when YOUTUBE_API_KEY is unset without leaking internals."""
    with patch("services.real_api.get_yt_api_key", return_value=""):
        res = client.get("/api/trending-feed?region=Pakistan&timeframe=7d")
        assert res.status_code == 500
        data = res.get_json()
        assert "error" in data
        assert "YouTube data" in data["error"]


def test_trending_feed_successful_mock_response_schema(client, flask_mod):
    """Verify /api/trending-feed contract conforms to frontend state machine requirements."""
    mock_yt_data = {
        "status": 200,
        "keyword": "Trending",
        "platform": "YouTube",
        "total_views": 9500000,
        "daily_metrics": [{"date": "2026-10-25", "views": 9500000, "likes": 300000, "shares": 0, "comments_count": 5000}],
        "comments": ["Awesome trend tutorial!"],
        "related_keywords": ["trending topic", "growth hacks"],
        "top_videos": [{"id": "v1", "title": "Top Viral Video", "views": 9500000}],
        "kpis": {"totalViews": 9500000, "avgEngagement": 3.2, "fastestCategory": "Entertainment"}
    }
    with patch.object(flask_mod, "fetch_youtube_data", return_value=mock_yt_data), \
         patch.object(flask_mod, "YOUTUBE_API_KEY", "fake-key"):
        res = client.get("/api/trending-feed?region=Pakistan&timeframe=7d")
        assert res.status_code == 200
        data = res.get_json()
        assert "results" in data
        assert "YouTube" in data["results"]
        assert "videos" in data
        assert "kpis" in data


def test_trending_feed_quota_rate_limit_429(client, flask_mod):
    """Verify rate limiter triggers 429 when quota/rate limit is exhausted."""
    with patch.object(flask_mod.rate_limiter, "is_allowed", return_value=(False, 45)):
        res = client.get("/api/trending-feed?region=Pakistan&timeframe=7d")
        assert res.status_code == 429
        data = res.get_json()
        assert "error" in data
        assert "Rate limit exceeded" in data["error"]
