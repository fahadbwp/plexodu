"""Data absence, cache provenance, preserved observation times and export semantics."""
import sys
import pytest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from services import real_api
from services.trend_intelligence import analyze_trend_intelligence
from services.report_generator import _build_pdf_elements


def test_cache_preserves_collection_time_without_mutating_fresh_result():
    data = {"status": 200, "top_videos": []}
    real_api._save_to_cache("truth-hotfix-test", data)
    try:
        cached = real_api._get_from_cache("truth-hotfix-test")
        assert cached["cached"] is True
        assert data["cached"] is False
        assert cached["fetched_at"] == data["fetched_at"]
        assert datetime.fromisoformat(cached["fetched_at"]).tzinfo is not None
        assert datetime.fromisoformat(cached["cache_served_at"]) >= datetime.fromisoformat(cached["fetched_at"])
    finally:
        real_api._YT_CACHE.pop("truth-hotfix-test", None)


def test_missing_comments_do_not_create_engagement_or_zero_comment_count():
    response = Mock(status_code=200)
    response.json.return_value = {"items": [{
        "id": "truthVideo1",
        "snippet": {"title": "Truth fixture", "categoryId": "20", "publishedAt": "2026-10-25T00:00:00Z"},
        "statistics": {"viewCount": "100", "likeCount": "0"},
        "contentDetails": {"duration": "PT2M"},
    }]}
    with patch.object(real_api, "get_yt_api_key", return_value="mock"), \
         patch.object(real_api, "_get_from_cache", return_value=None), \
         patch.object(real_api.requests, "get", return_value=response), \
         patch.object(real_api, "_fetch_related_keywords", return_value=[]):
        data = real_api.fetch_youtube_data("Trending")
    assert data["top_videos"][0]["comments"] is None
    assert data["top_videos"][0]["engagement"] is None
    assert data["kpis"]["avgEngagement"] is None


def test_public_snapshot_does_not_invent_share_count():
    snap = real_api._build_authentic_snapshot(100, None, 0, "2026-10-25")[0]
    assert snap["likes"] is None
    assert snap["shares"] is None
    assert snap["comments_count"] == 0


def test_missing_legacy_timestamp_is_not_fabricated_as_now():
    old = SimpleNamespace(timestamp=None, last_seen_at=None)
    intel = analyze_trend_intelligence("fixture", "YouTube", 0, 0, {}, [old], now=datetime(2026, 10, 26, tzinfo=timezone.utc))
    assert intel["status"] == "baseline"
    assert len(intel["timeline"]) == 1
    assert intel["timeline"][0]["date"] == "2026-10-26 00:00"
    assert intel["timeline"][0]["views"] == 0


def test_pdf_discloses_heuristic_score_and_pending_observed_change():
    elements = _build_pdf_elements(
        {"keyword": "<b>fixture</b>", "platform": "YouTube", "total_views": 0},
        {"positive_score": 0, "negative_score": 0, "neutral_score": 0, "dominant_sentiment": "unavailable"},
        None, None, "BASELINE", "QA",
    )
    table = next(e for e in elements if hasattr(e, "_cellvalues"))
    assert ["Observed Change", "Pending"] in table._cellvalues
    assert ["Virality Index (Heuristic)", "Unavailable"] in table._cellvalues
    assert "&lt;b&gt;fixture&lt;/b&gt;" in elements[0].text


def test_csv_unavailable_and_lifetime_snapshot_labels():
    # HTTP ownership/formula-injection behavior remains covered by the full API suite.
    source = (Path(__file__).resolve().parents[1] / "backend/app.py").read_text(encoding="utf-8")
    assert 'writer.writerow(["Recorded Snapshots (Lifetime Counters)"])' in source
    assert '"Unavailable" if m.shares is None else m.shares' in source


def test_zero_previous_counter_is_not_zero_percent_growth():
    prior = SimpleNamespace(timestamp=datetime(2026, 10, 24, tzinfo=timezone.utc), last_seen_at=None,
                            total_views=0, trend_id=1, current_velocity=None, current_acceleration=None,
                            current_trend_score=None, current_direction="BASELINE", current_confidence="Low")
    intel = analyze_trend_intelligence("fixture", "YouTube", 100, 0, {}, [prior], now=datetime(2026, 10, 26, tzinfo=timezone.utc))
    assert intel["velocity"] is None
    assert intel["velocity_display"] == "Unavailable"
    assert [p["views"] for p in intel["timeline"]] == [0, 100]
    assert intel["forecast"]["available"] is False


@pytest.mark.parametrize("published", [None, "invalid", "2999-01-01T00:00:00Z"])
def test_missing_publication_time_does_not_invent_age_or_momentum(published):
    response = Mock(status_code=200)
    response.json.return_value = {"items": [{"id": "truth_age", "snippet": {"title": "Age fixture", "publishedAt": published},
                                           "statistics": {"viewCount": "0", "likeCount": "0", "commentCount": "0"}}]}
    with patch.object(real_api, "get_yt_api_key", return_value="mock"), \
         patch.object(real_api, "_get_from_cache", return_value=None), \
         patch.object(real_api, "_save_to_cache"), \
         patch.object(real_api.requests, "get", return_value=response), \
         patch.object(real_api, "_fetch_related_keywords", return_value=[]):
        data = real_api.fetch_youtube_data("Trending")
    assert data["top_videos"][0]["views"] == 0
    assert data["top_videos"][0]["hoursAgo"] is None
    assert data["top_videos"][0]["momentumScore"] is None
    assert data["top_videos"][0]["category"] == "Unavailable"
    assert data["time_series"] == []
    assert data["kpis"]["topCategory"] is None
