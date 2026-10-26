"""
Unit and regression tests verifying truthful Trend Analyzer data and frontend functionality.
"""
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.real_api import fetch_youtube_data, _parse_duration


def test_parse_duration():
    assert _parse_duration("PT1H2M3S") == 3723
    assert _parse_duration("PT5M30S") == 330
    assert _parse_duration("PT45S") == 45
    assert _parse_duration("PT0S") == 0
    assert _parse_duration("") == 0


def test_real_api_requests_content_details_and_includes_duration(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "mock-test-key")
    captured_urls = []

    def mock_get(url, params=None, timeout=None):
        captured_urls.append((url, params or {}))
        if "videos" in url:
            items = [
                {
                    "id": "vid123",
                    "snippet": {
                        "title": "Shorts viral clip #shorts",
                        "channelTitle": "Cool Creator",
                        "categoryId": "20",
                        "publishedAt": "2026-10-15T12:00:00Z",
                        "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/vid123/hqdefault.jpg"}},
                    },
                    "statistics": {
                        "viewCount": "120000",
                        "likeCount": "8500",
                        "commentCount": "420",
                    },
                    "contentDetails": {
                        "duration": "PT45S",
                    },
                }
            ]
            m = Mock()
            m.status_code = 200
            m.json.return_value = {"items": items}
            return m
        m = Mock()
        m.status_code = 200
        m.json.return_value = {"items": []}
        return m

    with patch("services.real_api.requests.get", side_effect=mock_get):
        result = fetch_youtube_data("trending", region="Pakistan", category="All")

    # Verify videos.list requested snippet,statistics,contentDetails
    video_calls = [p for u, p in captured_urls if "videos" in u]
    assert len(video_calls) >= 1
    assert "contentDetails" in video_calls[0].get("part", "")

    # Verify top_videos includes duration and duration_sec and thumbnail
    top_vids = result.get("top_videos", [])
    assert len(top_vids) == 1
    v0 = top_vids[0]
    assert v0["duration_sec"] == 45
    assert v0["duration"] == "00:45"
    assert "https://i.ytimg.com/vi/vid123/hqdefault.jpg" in v0["thumbnail"]


def test_trend_analyzer_html_has_no_fabricated_metrics():
    html_path = Path(__file__).resolve().parent.parent / "frontend" / "tools" / "trend-analyzer.html"
    html = html_path.read_text(encoding="utf-8")

    # 1. No hardcoded hold rate values or claims
    assert "30-Second Hold Rate 64.5%" not in html
    assert "Above Average" not in html
    assert "+16.5% Advantage" not in html
    assert "Category Benchmark: 48%" not in html

    # 2. No hardcoded Format Breakdown velocity
    assert "+68% velocity" not in html

    # 3. No static Opportunity Score: 92/100
    assert "Opportunity Score: 92/100" not in html
    assert 'id="opportunityScoreBadge"' in html

    # 4. No 0 (Stagnant)
    assert "0 (Stagnant)" not in html
    assert "Scale: 0–100" in html

    # 5. Required element IDs are present
    assert 'id="viewsTrendCatBadge"' in html
    assert 'id="chartBaselineNote"' in html
    assert 'id="hashtagsList"' in html
    assert 'id="ctaStrategistBtn"' in html
    assert 'id="ctaCompetitorBtn"' in html
    assert 'id="videoFilterTabs"' in html


def test_trend_analyzer_js_has_no_fake_constants():
    js_path = Path(__file__).resolve().parent.parent / "frontend" / "js" / "tools" / "trend-analyzer.js"
    js = js_path.read_text(encoding="utf-8")

    # No hardcoded 84% Positive
    assert "84% Positive" not in js

    # No 08:24 fallback duration
    assert '"08:24"' not in js

    # filterVideoTab function is present
    assert "function filterVideoTab" in js or "filterVideoTab = function" in js

    # computeFormatBreakdown is defined and used
    assert "function computeFormatBreakdown" in js
