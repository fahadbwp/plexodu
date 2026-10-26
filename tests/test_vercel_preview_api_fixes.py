"""
Tests for Critical Vercel Preview API Fixes & Schema Resilience
=============================================================
Validates:
1. Bug 1 Regression Guard: Informative diagnostic error when YOUTUBE_API_KEY is unset in Preview
2. Bug 2 Regression Guard: AI Strategist frontend/backend rejection of raw boolean 'true' as chat content
3. API Contracts: /api/video-analysis, /api/audit-channel, /api/seo/analyze schemas
4. Cache-busting parameter consistency across all 5 tool HTML pages (v=28.4)
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
AI_STRATEGIST_JS = FRONTEND_DIR / "js" / "tools" / "ai-strategist.js"

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


# ── Bug 1: Trend Analyzer API Key Diagnostic ─────────────────────────────────
def test_trending_feed_missing_youtube_key_diagnostics(app_client):
    """When YOUTUBE_API_KEY is not configured, /api/trending-feed must return an explicit diagnostic error."""
    with patch("services.real_api.get_yt_api_key", return_value=""):
        res = app_client.get("/api/trending-feed?region=Pakistan&timeframe=7d")
        assert res.status_code == 500
        data = json.loads(res.data)
        assert "error" in data
        assert "YouTube data" in data["error"]
        assert "YOUTUBE_API_KEY is not configured" in data["error"]
        # Ensure no private secrets or file traces are leaked
        assert "traceback" not in json.dumps(data).lower()


# ── Bug 2: AI Strategist Boolean & Schema Rejection ─────────────────────────
def test_ai_chat_missing_groq_key_returns_structured_diagnostic(app_client):
    """When GROQ_API_KEY is not configured, /api/chat must return a structured message, not a bare boolean."""
    with patch("services.groq_service.os.environ.get", return_value=""), \
         patch("app.core.config.settings.GROQ_API_KEY", ""):
        res = app_client.post(
            "/api/chat",
            data=json.dumps({"message": "⚡ 3 High-CTR Title & Hook Ideas for my channel"}),
            content_type="application/json"
        )
        data = json.loads(res.data)
        assert "reply" in data
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 10
        assert "GROQ_API_KEY" in data["reply"]
        assert data.get("error") is not True  # Must not be raw boolean True


def test_ai_strategist_frontend_rejects_boolean_content():
    """Verify ai-strategist.js strictly rejects boolean or non-string values as advice."""
    js = AI_STRATEGIST_JS.read_text(encoding="utf-8")
    
    # Check safe string extractor function
    assert "extractText" in js
    assert "typeof val === \"string\"" in js
    
    # Check that appendBubble has safety guard against non-string content
    assert "safeContent" in js
    assert "typeof content === \"string\"" in js


# ── Tool Contracts Verification ──────────────────────────────────────────────
def test_video_analysis_contract_with_url(app_client):
    """Verify /api/video-analysis parses valid video URL."""
    mock_video_data = {
        "video_id": "dQw4w9WgXcQ",
        "title": "Build in 2026",
        "channel_name": "Creator Lab",
        "view_count": 100000,
        "like_count": 5000,
        "comment_count": 120,
        "upload_date": "2026-01-01",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "tags": ["tech", "guide"],
        "comments": ["Awesome!"],
        "daily_metrics": [{"date": "2026-01-01", "views": 100000, "likes": 5000, "shares": 0, "comments_count": 120}],
    }
    mock_sentiment = {
        "dominant_sentiment": "positive",
        "positive_score": 80,
        "negative_score": 5,
        "neutral_score": 15,
        "sample_comment": "Awesome!",
    }
    mod = get_flask_module()
    with patch.object(mod, "analyze_youtube_video", return_value=mock_video_data), \
         patch.object(mod, "analyze_sentiment", return_value=mock_sentiment):
        res = app_client.post(
            "/api/video-analysis",
            data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
            content_type="application/json"
        )
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data.get("success") is True
        assert data.get("title") == "Build in 2026"
        assert data.get("channel_title") == "Creator Lab"
        assert "seo_quality" in data


def test_audit_channel_contract(app_client):
    """Verify /api/audit-channel parses valid handle."""
    mock_channel_data = {
        "channel_name": "MKBHD",
        "subscriber_count": 18000000,
        "total_views": 4000000000,
        "age_years": 16.5,
        "earn_min_monthly": 1000,
        "earn_max_monthly": 4000,
        "avatar_url": "https://example.com/avatar.jpg",
        "top_videos": []
    }
    mod = get_flask_module()
    with patch.object(mod, "audit_youtube_channel", return_value=mock_channel_data):
        res = app_client.post(
            "/api/audit-channel",
            data=json.dumps({"identifier": "@mkbhd"}),
            content_type="application/json"
        )
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data.get("title") == "MKBHD"
        assert data.get("subscribers") == 18000000


def test_seo_analyze_contract(app_client):
    """Verify /api/seo/analyze returns complete breakdown."""
    payload = {
        "title": "How to Build a YouTube Channel in 2026",
        "description": "Complete guide for 2026 creators."
    }
    res = app_client.post(
        "/api/seo/analyze",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "score" in data
    assert "breakdown" in data
    assert len(data["breakdown"]) > 0


# ── Cache Busting Consistency ────────────────────────────────────────────────
def test_all_tools_cache_busting_v28_4():
    """Verify all 5 tool pages use v=28.4 query parameters."""
    for html_file in TOOLS_DIR.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")
        assert "style.css?v=28.4" in content, f"{html_file.name} missing style.css?v=28.4"
        assert "common.js?v=28.4" in content, f"{html_file.name} missing common.js?v=28.4"
