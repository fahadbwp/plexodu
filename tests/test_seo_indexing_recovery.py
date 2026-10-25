"""
Tests for SEO Indexing Recovery & Search Console Optimization
Validates clean legal URLs, blog article delivery, 301 canonical redirects,
sitemap XML structure, and canonical tags.
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
SITEMAP_PATH = FRONTEND_DIR / "sitemap.xml"
VERCEL_PATH = REPO_ROOT / "vercel.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def get_flask_app():
    if "main_flask_app" in sys.modules:
        return sys.modules["main_flask_app"].app
    app_py_path = BACKEND_DIR / "app.py"
    spec = importlib.util.spec_from_file_location("main_flask_app", str(app_py_path))
    flask_module = importlib.util.module_from_spec(spec)
    sys.modules["main_flask_app"] = flask_module
    spec.loader.exec_module(flask_module)
    return flask_module.app


@pytest.fixture
def client():
    app = get_flask_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================
# 1. Legal Routing & 301 Redirects
# ============================================================================
def test_privacy_page_served_cleanly(client):
    res = client.get("/privacy")
    assert res.status_code == 200
    assert "Privacy Policy" in res.get_data(as_text=True)
    assert "<!DOCTYPE html>" in res.get_data(as_text=True)


def test_privacy_html_redirects_to_clean_url(client):
    res = client.get("/privacy.html")
    assert res.status_code == 301
    assert res.headers.get("Location") == "/privacy"


def test_terms_page_served_cleanly(client):
    res = client.get("/terms")
    assert res.status_code == 200
    assert "Terms of Service" in res.get_data(as_text=True)
    assert "<!DOCTYPE html>" in res.get_data(as_text=True)


def test_terms_html_redirects_to_clean_url(client):
    res = client.get("/terms.html")
    assert res.status_code == 301
    assert res.headers.get("Location") == "/terms"


# ============================================================================
# 2. Blog Index & Canonical Article Delivery
# ============================================================================
def test_blog_index_redirect_and_delivery(client):
    # Extensionless /blog redirects to /blog/
    res_redirect = client.get("/blog")
    assert res_redirect.status_code == 301
    assert res_redirect.headers.get("Location") == "/blog/"

    # Trailing slash /blog/ serves blog index
    res_index = client.get("/blog/")
    assert res_index.status_code == 200
    body = res_index.get_data(as_text=True)
    assert "Plexudo Blog" in body
    assert "/blog/how-to-write-high-ctr-youtube-titles/" in body
    assert "/blog/how-to-find-high-search-low-competition-youtube-keywords/" in body
    assert "/blog/youtube-competitor-channel-analysis-guide/" in body
    assert "/blog/google-gemini-student-offer-pakistan-2026/" in body


@pytest.mark.parametrize("article_slug", [
    "how-to-write-high-ctr-youtube-titles",
    "how-to-find-high-search-low-competition-youtube-keywords",
    "youtube-competitor-channel-analysis-guide",
    "google-gemini-student-offer-pakistan-2026",
])
def test_blog_articles_served_successfully(client, article_slug):
    # Trailing slash serves 200
    res = client.get(f"/blog/{article_slug}/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "<!DOCTYPE html>" in html
    assert f"https://plexudo.vercel.app/blog/{article_slug}/" in html

    # Slashless variant issues 301 redirect to canonical trailing slash
    res_slashless = client.get(f"/blog/{article_slug}")
    assert res_slashless.status_code == 301
    assert res_slashless.headers.get("Location") == f"/blog/{article_slug}/"


# ============================================================================
# 3. Legacy Aliases Redirect to Canonical URLs
# ============================================================================
@pytest.mark.parametrize("alias,expected_target", [
    ("competitor-analysis-guide", "/blog/youtube-competitor-channel-analysis-guide/"),
    ("trending-keywords-guide", "/blog/how-to-find-high-search-low-competition-youtube-keywords/"),
])
def test_legacy_blog_aliases_redirect_with_301(client, alias, expected_target):
    # Test slashless alias
    res1 = client.get(f"/blog/{alias}")
    assert res1.status_code == 301
    assert res1.headers.get("Location") == expected_target

    # Test trailing-slash alias
    res2 = client.get(f"/blog/{alias}/")
    assert res2.status_code == 301
    assert res2.headers.get("Location") == expected_target


# ============================================================================
# 4. Unknown Blog Slugs Return 404 (Never soft-404 homepage)
# ============================================================================
def test_unknown_blog_slug_returns_404(client):
    res = client.get("/blog/non-existent-super-random-guide-12345/")
    assert res.status_code == 404
    data = res.get_json()
    assert data is not None
    assert "error" in data


# ============================================================================
# 5. Sitemap XML Audit & Validation
# ============================================================================
def test_sitemap_xml_contains_only_canonical_urls():
    assert SITEMAP_PATH.is_file(), "sitemap.xml must exist in frontend/"
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = [elem.text.strip() for elem in root.findall("ns:url/ns:loc", namespace)]
    lastmods = [elem.text.strip() for elem in root.findall("ns:url/ns:lastmod", namespace)]

    # Expected exact 13 canonical URLs
    expected_canonicals = {
        "https://plexudo.vercel.app/",
        "https://plexudo.vercel.app/tools",
        "https://plexudo.vercel.app/tools/trend-analyzer",
        "https://plexudo.vercel.app/tools/video-analyzer",
        "https://plexudo.vercel.app/tools/competitor-audit",
        "https://plexudo.vercel.app/tools/ai-strategist",
        "https://plexudo.vercel.app/blog/",
        "https://plexudo.vercel.app/blog/google-gemini-student-offer-pakistan-2026/",
        "https://plexudo.vercel.app/blog/how-to-write-high-ctr-youtube-titles/",
        "https://plexudo.vercel.app/blog/how-to-find-high-search-low-competition-youtube-keywords/",
        "https://plexudo.vercel.app/blog/youtube-competitor-channel-analysis-guide/",
        "https://plexudo.vercel.app/privacy",
        "https://plexudo.vercel.app/terms",
    }

    assert len(urls) == 13, f"Expected 13 URLs in sitemap, found {len(urls)}"
    assert set(urls) == expected_canonicals

    # Disallowed non-canonical patterns
    for url in urls:
        assert not url.endswith(".html"), f"Sitemap URL must not have .html extension: {url}"
        assert "dashboard" not in url, f"Private dashboard must not be in sitemap: {url}"
        assert "keyword-tool" not in url, f"Redirected tool must not be in sitemap: {url}"

    # Verify lastmod format
    for lm in lastmods:
        parts = lm.split("-")
        assert len(parts) == 3 and len(parts[0]) == 4, f"Invalid lastmod date: {lm}"


# ============================================================================
# 6. Canonical Tags & Metadata Consistency Across All Pages
# ============================================================================
def test_canonical_tags_in_html_files():
    files_to_check = {
        "privacy.html": 'href="https://plexudo.vercel.app/privacy"',
        "terms.html": 'href="https://plexudo.vercel.app/terms"',
        "blog/index.html": 'href="https://plexudo.vercel.app/blog/"',
        "blog/google-gemini-student-offer-pakistan-2026/index.html": 'href="https://plexudo.vercel.app/blog/google-gemini-student-offer-pakistan-2026/"',
        "blog/how-to-write-high-ctr-youtube-titles/index.html": 'href="https://plexudo.vercel.app/blog/how-to-write-high-ctr-youtube-titles/"',
        "blog/how-to-find-high-search-low-competition-youtube-keywords/index.html": 'href="https://plexudo.vercel.app/blog/how-to-find-high-search-low-competition-youtube-keywords/"',
        "blog/youtube-competitor-channel-analysis-guide/index.html": 'href="https://plexudo.vercel.app/blog/youtube-competitor-channel-analysis-guide/"',
    }

    for rel_path, expected_canonical in files_to_check.items():
        full_path = FRONTEND_DIR / rel_path
        assert full_path.is_file(), f"File {rel_path} does not exist"
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert expected_canonical in content, f"Expected canonical {expected_canonical} not found in {rel_path}"


# ============================================================================
# 7. Vercel Configuration Redirects Audit
# ============================================================================
def test_vercel_json_redirects_configured():
    assert VERCEL_PATH.is_file()
    with open(VERCEL_PATH, "r", encoding="utf-8") as f:
        v = json.load(f)
    routes = v.get("routes", [])

    redirect_map = {r["src"]: (r.get("status"), r.get("headers", {}).get("Location")) for r in routes if "status" in r}

    assert redirect_map.get("/privacy.html") == (301, "/privacy")
    assert redirect_map.get("/terms.html") == (301, "/terms")
    assert redirect_map.get("/blog") == (301, "/blog/")
    assert redirect_map.get("/blog/competitor-analysis-guide/?") == (301, "/blog/youtube-competitor-channel-analysis-guide/")
    assert redirect_map.get("/blog/trending-keywords-guide/?") == (301, "/blog/how-to-find-high-search-low-competition-youtube-keywords/")
