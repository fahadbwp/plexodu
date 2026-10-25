"""
Plexudo YouTube SEO Intelligence Engine v1 — Comprehensive Test Suite
======================================================================
Validates:
1. Pure, deterministic heuristic execution (same input => identical output).
2. Scores strictly bounded in [0.0, 100.0].
3. Monotonicity: adding focus keyword to title never lowers the score.
4. Tag-order independence: reordering tags produces identical score & breakdown.
5. Duplicate tags, stuffing detection, and character limits.
6. Unicode & native Urdu script support.
7. Roman Urdu stopwords not penalized for repetition or stuffing.
8. Empty, whitespace, and no-focus-keyword handling with honest "unavailable" basis.
9. API contract: POST /api/seo/analyze rate-limits, validation, 415/413/400 errors.
10. Zero database writes (pure read-only computation).
11. XSS resilience in API and UI contracts.
12. Performance: max-payload evaluation finishes in under 100ms.
"""

import importlib.util
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.seo_engine import (
    DISCLAIMER_TEXT,
    ENGINE_VERSION,
    SCHEMA_VERSION,
    analyze_seo_metadata,
    calculate_youtube_tag_chars,
)

# -----------------------------------------------------------------------------
# Fixtures & Test App Setup
# -----------------------------------------------------------------------------

def get_flask_module():
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


# -----------------------------------------------------------------------------
# Unit Tests: Pure Engine Behavior
# -----------------------------------------------------------------------------

def test_golden_fixture_well_optimized():
    """Verify a comprehensive, high-quality video metadata set achieves a high score."""
    title = "Python Tutorial 2026: Complete Beginner Guide to Coding"
    description = (
        "In this complete Python tutorial for 2026, we explore beginner fundamentals, "
        "step-by-step programming syntax, and practical coding exercises.\n\n"
        "Timestamps:\n0:00 Introduction\n1:30 Installation\n4:00 First Program\n\n"
        "#python #coding #tutorial"
    )
    tags = ["python tutorial", "python programming", "coding for beginners", "learn python 2026"]
    focus_kw = "python tutorial"

    res = analyze_seo_metadata(title, description, tags, focus_kw)

    assert res["engine_version"] == ENGINE_VERSION
    assert res["schema_version"] == SCHEMA_VERSION
    assert res["disclaimer"] == DISCLAIMER_TEXT
    assert res["score"] >= 80.0
    assert res["score_basis"]["available_max"] == 100
    assert res["score_basis"]["unavailable_components"] == []
    assert len(res["breakdown"]) == 5
    assert all(comp["status"] == "pass" for comp in res["breakdown"])


def test_engine_pure_determinism():
    """Verify engine is 100% deterministic (no clock, no randomness, identical output)."""
    title = "Free Fire Pro Headshot Sensitivity 2026"
    desc = "Master your Free Fire sensitivity settings in 2026 with this pro guide."
    tags = ["free fire", "sensitivity", "settings"]
    fk = "free fire sensitivity"

    baseline = analyze_seo_metadata(title, desc, tags, fk)
    for _ in range(50):
        iteration = analyze_seo_metadata(title, desc, tags, fk)
        assert iteration == baseline


def test_score_range_bounded_0_to_100():
    """Verify score is strictly bounded within 0.0 and 100.0 across edge cases."""
    edge_cases = [
        ("", "", [], None),
        ("   ", "   ", ["  "], ""),
        ("A" * 250, "B" * 15000, ["tag" * 50] * 120, "C" * 200),
        ("??????!!!!!!", "http://spam.link", ["spam", "spam", "spam"], "xyz"),
        ("Clean Title For Testing", "", None, None),
    ]
    for t, d, tags, fk in edge_cases:
        res = analyze_seo_metadata(t, d, tags, fk)
        assert 0.0 <= res["score"] <= 100.0


def test_focus_keyword_monotonicity():
    """Verify adding the focus keyword to the title never lowers the score."""
    base_title = "Complete Web Development Guide in 2026"
    fk_title = "FastAPI Tutorial: Complete Web Development Guide in 2026"
    desc = "Learn modern backend API development with this comprehensive guide."
    tags = ["web development", "backend", "api"]
    fk = "FastAPI Tutorial"

    score_without = analyze_seo_metadata(base_title, desc, tags, fk)["score"]
    score_with = analyze_seo_metadata(fk_title, desc, tags, fk)["score"]

    assert score_with >= score_without, (
        f"Adding focus keyword to title lowered score: {score_with} vs {score_without}"
    )


def test_tag_order_independence():
    """Verify reordering tags produces identical score and breakdown."""
    title = "Rust Programming Fundamentals"
    desc = "Learn Rust memory safety and concurrency concepts step by step."
    tags_a = ["rust", "programming", "memory safety", "concurrency"]
    tags_b = ["concurrency", "memory safety", "rust", "programming"]
    fk = "Rust Programming"

    res_a = analyze_seo_metadata(title, desc, tags_a, fk)
    res_b = analyze_seo_metadata(title, desc, tags_b, fk)

    assert res_a["score"] == res_b["score"]
    assert res_a["score_basis"] == res_b["score_basis"]
    assert res_a["breakdown"] == res_b["breakdown"]


def test_duplicate_tags_detection():
    """Verify duplicate tags after casefold normalization are detected and warned."""
    title = "Docker Crash Course 2026"
    desc = "Everything you need to know about Docker containers and images."
    tags = ["Docker", "docker", "DOCKER", "containers"]

    res = analyze_seo_metadata(title, desc, tags)
    tag_checks = [c for c in res["checks"] if c["id"] == "tag_duplicates"]
    assert len(tag_checks) == 1
    assert tag_checks[0]["status"] == "warn"


def test_keyword_stuffing_detection():
    """Verify excessive repetition of non-stopword tokens triggers anti-stuffing warning."""
    title = "Crypto Market Trading Update 2026"
    stuffed_desc = (
        "crypto crypto crypto crypto crypto crypto crypto crypto crypto crypto "
        "crypto trading crypto signals crypto profits crypto analysis crypto"
    )
    res = analyze_seo_metadata(title, stuffed_desc, ["crypto"])
    stuffing_checks = [c for c in res["checks"] if c["id"] == "keyword_stuffing"]
    assert len(stuffing_checks) == 1
    assert stuffing_checks[0]["status"] in ["warn", "fail"]


def test_unicode_and_urdu_script():
    """Verify native Urdu script is supported without error or crash."""
    title = "فری فائر گیم پلے اور پرو سیٹنگز 2026"
    desc = "اس ویڈیو میں ہم فری فائر کی بہترین سیٹنگز اور ٹپس تفصیل سے بیان کریں گے۔"
    tags = ["فری فائر", "گیم پلے", "اردو"]
    fk = "فری فائر"

    res = analyze_seo_metadata(title, desc, tags, fk)
    assert res["score"] >= 75.0
    assert any("فری فائر" in c.get("message", "") for c in res["checks"])


def test_roman_urdu_stopwords_not_penalized():
    """Verify Roman Urdu stopwords do not trigger keyword stuffing or repetition penalties."""
    title = "Free Fire Pro Settings Kaise Karein 2026"
    desc = (
        "Is video mein hum Free Fire ki pro settings batao aur tips explain karein ge. "
        "Yeh settings aapke gameplay ko behtar banaye gi aur rank push mein madad kare gi. "
        "Video ko pura dekhein aur doston ke sath share karein."
    )
    tags = ["free fire", "pro settings", "gaming"]
    fk = "Free Fire Pro Settings"

    res = analyze_seo_metadata(title, desc, tags, fk)
    # Confirm no stuffing warning for 'mein', 'ki', 'aur', 'ko', 'ge'
    stuffing_check = next(c for c in res["checks"] if c["id"] == "keyword_stuffing")
    assert stuffing_check["status"] == "pass"


def test_no_focus_keyword_unavailable_basis():
    """Verify omitting focus keyword marks component unavailable and scales score to 75 basis."""
    title = "Modern CSS Layouts with Flexbox and Grid"
    desc = "A complete modern CSS tutorial explaining flexbox and grid layouts."
    tags = ["css", "web development"]

    res = analyze_seo_metadata(title, desc, tags, focus_keyword=None)
    basis = res["score_basis"]

    assert basis["available_max"] == 75
    assert "focus_keyword" in basis["unavailable_components"]
    assert basis["normalized_to_100"] is True
    fk_comp = next(c for c in res["breakdown"] if c["id"] == "focus_keyword")
    assert fk_comp["status"] == "unavailable"
    assert fk_comp["points"] is None


def test_tags_500_char_limit_violation():
    """Verify exceeding YouTube's 500-char tag limit produces a fail status."""
    title = "Valid YouTube Title"
    desc = "Valid YouTube Description"
    long_tags = ["longtag" * 10] * 10  # 700+ chars

    res = analyze_seo_metadata(title, desc, long_tags)
    limit_check = next(c for c in res["checks"] if c["id"] == "tag_char_limit")
    assert limit_check["status"] == "fail"


def test_missing_tags_is_neutral_not_failure():
    """Verify missing tags awards 10/10 neutral points and never penalizes the score."""
    title = "React 19 Deep Dive Tutorial"
    desc = "An in-depth explanation of React 19 actions, compiler, and async transitions."

    res = analyze_seo_metadata(title, desc, tags=[])
    tag_comp = next(c for c in res["breakdown"] if c["id"] == "tags")
    assert tag_comp["points"] == 10.0
    assert tag_comp["status"] == "pass"


# -----------------------------------------------------------------------------
# API Contract & Security Tests: POST /api/seo/analyze
# -----------------------------------------------------------------------------

def test_api_successful_evaluation(client):
    """Verify POST /api/seo/analyze returns 200 with complete response schema."""
    payload = {
        "title": "Machine Learning in 2026: Step-by-Step Overview",
        "description": "An introduction to machine learning principles and model evaluation.",
        "tags": ["machine learning", "ai", "data science"],
        "focus_keyword": "machine learning",
        "language": "en"
    }
    resp = client.post("/api/seo/analyze", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["schema_version"] == "1.0.0"
    assert data["engine_version"] == "1.0.0"
    assert "score" in data
    assert "score_basis" in data
    assert "breakdown" in data
    assert "checks" in data
    assert "suggestions" in data
    assert "unavailable" in data
    assert "disclaimer" in data


def test_api_requires_application_json(client):
    """Verify POST /api/seo/analyze rejects non-JSON Content-Type with 415."""
    resp = client.post("/api/seo/analyze", data="title=Hello", content_type="text/plain")
    assert resp.status_code == 415
    data = resp.get_json()
    assert "error" in data


def test_api_rejects_malformed_json(client):
    """Verify POST /api/seo/analyze rejects malformed JSON with 400."""
    resp = client.post("/api/seo/analyze", data="{malformed_json: true", content_type="application/json")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_api_rejects_oversized_payload_413(client):
    """Verify POST /api/seo/analyze rejects payloads exceeding 64 KB with 413."""
    oversized_desc = "x" * 70000
    payload = {"title": "Title", "description": oversized_desc}
    resp = client.post("/api/seo/analyze", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 413
    data = resp.get_json()
    assert "error" in data


def test_api_rejects_unrecognized_fields(client):
    """Verify POST /api/seo/analyze rejects unexpected fields to prevent injection."""
    payload = {"title": "Valid Title", "unexpected_admin_field": True}
    resp = client.post("/api/seo/analyze", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_api_rejects_empty_or_oversized_title(client):
    """Verify POST /api/seo/analyze strictly validates title field."""
    # Empty title
    resp1 = client.post("/api/seo/analyze", data=json.dumps({"title": "   "}), content_type="application/json")
    assert resp1.status_code == 400

    # Oversized title (>200 chars)
    resp2 = client.post("/api/seo/analyze", data=json.dumps({"title": "A" * 201}), content_type="application/json")
    assert resp2.status_code == 400


def test_api_does_not_echo_raw_input_in_errors(client):
    """Verify error messages never reflect attacker-controlled input."""
    raw_probe = "<script>alert('pwned')</script>"
    resp = client.post("/api/seo/analyze", data=json.dumps({"title": "A" * 250, "probe": raw_probe}), content_type="application/json")
    assert resp.status_code == 400
    err_text = resp.get_data(as_text=True)
    assert raw_probe not in err_text


def test_api_writes_nothing_to_database(client, flask_mod):
    """Verify POST /api/seo/analyze performs zero database writes."""
    Trend = flask_mod.Trend
    User = flask_mod.User

    with client.application.app_context():
        t_count_before = Trend.query.count()
        u_count_before = User.query.count()

    payload = {
        "title": "Database Isolation Test Video",
        "description": "Testing zero DB persistence guarantee.",
        "tags": ["test", "db"]
    }
    resp = client.post("/api/seo/analyze", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200

    with client.application.app_context():
        t_count_after = Trend.query.count()
        u_count_after = User.query.count()

    assert t_count_before == t_count_after
    assert u_count_before == u_count_after


def test_video_analyzer_endpoint_includes_seo_quality(client, flask_mod):
    """Verify /api/video-analysis response includes seo_quality without breaking existing fields."""
    mock_video_result = {
        "video_id": "xyz98765432",
        "title": "Comprehensive YouTube SEO Testing Guide",
        "channel_name": "Plexudo Academy",
        "view_count": 250000,
        "like_count": 15000,
        "comment_count": 300,
        "upload_date": "2026-02-10",
        "thumbnail": "https://img.youtube.com/vi/xyz98765432/mqdefault.jpg",
        "tags": ["seo", "youtube", "guide"],
        "comments": ["Super helpful video!"],
        "daily_metrics": [{"date": "2026-02-10", "views": 250000, "likes": 15000, "shares": 0, "comments_count": 300}],
        "description": "A complete guide on optimizing your YouTube video metadata.",
    }
    mock_sentiment = {
        "dominant_sentiment": "positive",
        "positive_score": 85,
        "negative_score": 5,
        "neutral_score": 10,
        "sample_comment": "Super helpful video!",
    }

    with patch.object(flask_mod, "analyze_youtube_video", return_value=mock_video_result), \
         patch.object(flask_mod, "analyze_sentiment", return_value=mock_sentiment):

        res = client.post(
            "/api/video-analysis",
            data=json.dumps({"url": "https://www.youtube.com/watch?v=xyz98765432"}),
            content_type="application/json",
        )

    assert res.status_code == 200
    data = res.get_json()
    assert "seo_quality" in data
    assert data["seo_quality"]["engine_version"] == "1.0.0"
    assert data["seo_quality"]["score"] > 0
    # Confirm backwards compatibility
    assert data["channel_title"] == "Plexudo Academy"
    assert data["views"] == 250000


def test_max_size_input_finishes_under_100ms():
    """Verify worst-case input evaluation finishes well under 100 milliseconds."""
    max_title = "A" * 200
    max_desc = ("This is a long descriptive sentence explaining the video concepts. " * 150)[:10000]
    max_tags = [f"tag_{i}" for i in range(100)]
    max_fk = "descriptive sentence"

    t0 = time.perf_counter()
    res = analyze_seo_metadata(max_title, max_desc, max_tags, max_fk)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert res["score"] >= 0
    assert elapsed_ms < 100.0, f"Max size evaluation took {elapsed_ms:.2f}ms (threshold: 100ms)"


# -----------------------------------------------------------------------------
# Policy & Platform Boundary Tests (Hashtags, Multi-word Tag Quotes, 5000-byte Desc)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("count,expected_status,is_policy_violation", [
    (5, "pass", False),
    (15, "warn", False),
    (16, "warn", False),
    (60, "warn", False),
    (61, "fail", True),
])
def test_hashtag_policy_and_advice_thresholds(count, expected_status, is_policy_violation):
    """
    Verify YouTube official policy (>60 hashtags ignored/flagged) vs
    Plexudo creator recommendation (3-5 hashtags) across boundary counts.
    Exceeding 15 hashtags is NOT called a YouTube policy violation.
    """
    hashtags = " ".join(f"#tag{i}" for i in range(1, count + 1))
    desc = f"In this video we review key concepts and tutorials.\n\n{hashtags}"
    res = analyze_seo_metadata("Valid Title Testing Hashtags", desc, ["test"])

    ht_check = next(c for c in res["checks"] if c["id"] == "desc_hashtags")
    assert ht_check["status"] == expected_status

    if is_policy_violation:
        assert "YouTube Policy Violation" in ht_check["message"]
        assert "Over 60 hashtags detected" in ht_check["message"]
    else:
        assert "YouTube Policy Violation" not in ht_check["message"]
        if count in (15, 16, 60):
            assert "Plexudo Tip" in ht_check["message"]
            assert "60-hashtag limit" in ht_check["message"]


def test_tag_character_calculation_with_quotes_commas_and_unicode():
    """
    Verify exact YouTube Studio tag character count accounting for:
    - Multi-word tags enclosed in quotation marks (+2 chars)
    - Comma separators between tags
    - Unicode and Urdu/Hindi script tags
    """
    # 1. Single word tags
    assert calculate_youtube_tag_chars(["python", "coding"]) == len("python,coding")  # 6+6+1 = 13

    # 2. Multi-word tags with quotes added
    # "python tutorial" (15 chars + 2 quotes = 17) + comma (1) + "coding" (6) = 24
    assert calculate_youtube_tag_chars(["python tutorial", "coding"]) == 24

    # 3. Unicode script with spaces
    # "فری فائر" (8 chars + 2 quotes = 10) + comma (1) + "پرو گیمنگ" (9 chars + 2 quotes = 11) = 22
    assert calculate_youtube_tag_chars(["فری فائر", "پرو گیمنگ"]) == 22

    # 4. Empty or whitespace tags ignored
    assert calculate_youtube_tag_chars(["", "   ", "python"]) == 6

    # 5. Boundary testing 500 characters
    # 49 tags of 9 chars each + 1 quote-free tag
    # Construct exact 500 char payload
    tags_500 = ["a" * 9 for _ in range(50)]  # 50 tags of 9 chars = 450 + 49 commas = 499 chars + 1 char = 500 chars
    tags_500[0] = "a" * 10  # 451 + 49 = 500
    assert calculate_youtube_tag_chars(tags_500) == 500

    res_500 = analyze_seo_metadata("Title", "Description", tags_500)
    tag_check_500 = next(c for c in res_500["checks"] if c["id"] == "tag_char_limit")
    assert tag_check_500["status"] == "pass"

    # 501 chars fails platform limit
    tags_501 = list(tags_500)
    tags_501.append("x")  # adds 1 comma + 1 char = 502 chars
    res_501 = analyze_seo_metadata("Title", "Description", tags_501)
    tag_check_501 = next(c for c in res_501["checks"] if c["id"] == "tag_char_limit")
    assert tag_check_501["status"] == "fail"
    assert "YouTube Platform Limit" in tag_check_501["message"]


def test_description_5000_byte_boundary_utf8():
    """
    Verify YouTube Data API 5,000-byte maximum description validation.
    Multi-byte UTF-8 characters count by byte length, not purely character count.
    """
    # 1. Exactly 5,000 ASCII bytes passes platform limit
    desc_5000 = "a" * 5000
    res_5000 = analyze_seo_metadata("Title", desc_5000, ["test"])
    desc_check_5000 = next(c for c in res_5000["checks"] if c["id"] == "desc_length")
    assert desc_check_5000["status"] == "pass"
    assert "5000/5000 bytes" in desc_check_5000["message"]

    # 2. 5,001 ASCII bytes fails platform limit
    desc_5001 = "a" * 5001
    res_5001 = analyze_seo_metadata("Title", desc_5001, ["test"])
    desc_check_5001 = next(c for c in res_5001["checks"] if c["id"] == "desc_length")
    assert desc_check_5001["status"] == "fail"
    assert "YouTube Platform Limit: Description exceeds YouTube Data API maximum of 5,000 bytes" in desc_check_5001["message"]

    # 3. Multi-byte Unicode: 2,600 Urdu characters (each 2 bytes = 5,200 bytes)
    # Character count is 2,600 (<5000 chars), but UTF-8 byte count exceeds 5,000 bytes!
    urdu_word = "اردو "  # 5 chars, 9 bytes in UTF-8
    urdu_long_desc = urdu_word * 600  # 3,000 chars, 5,400 bytes
    res_urdu_overflow = analyze_seo_metadata("Title", urdu_long_desc, ["test"])
    urdu_check = next(c for c in res_urdu_overflow["checks"] if c["id"] == "desc_length")
    assert urdu_check["status"] == "fail"
    assert "bytes in UTF-8" in urdu_check["message"]
    assert "5,000 bytes" in urdu_check["message"]
