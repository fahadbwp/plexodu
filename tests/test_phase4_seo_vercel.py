import pytest
from pathlib import Path
import json
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"
INDEX_HTML = FRONTEND / "index.html"
BLOG_INDEX_HTML = FRONTEND / "blog" / "index.html"
BLOG_POST_HTML = FRONTEND / "blog" / "google-gemini-student-offer-pakistan-2026" / "index.html"
SITEMAP_XML = FRONTEND / "sitemap.xml"
ROBOTS_TXT = FRONTEND / "robots.txt"
VERCEL_JSON = REPO_ROOT / "vercel.json"
PRIVACY_HTML = FRONTEND / "privacy.html"
TERMS_HTML = FRONTEND / "terms.html"

def read(path):
    return path.read_text(encoding="utf-8")

class TestIndexHtml:
    def test_canonical_points_to_root(self):
        c = read(INDEX_HTML)
        assert '<link rel="canonical" href="https://plexudo.vercel.app/">' in c

    def test_adsense_tag_present(self):
        c = read(INDEX_HTML)
        assert 'ca-pub-3168330263525370' in c

    def test_og_url_is_root(self):
        c = read(INDEX_HTML)
        assert '<meta property="og:url" content="https://plexudo.vercel.app/">' in c

class TestBlogIndexHtml:
    def test_canonical_is_blog_not_root(self):
        c = read(BLOG_INDEX_HTML)
        assert '<link rel="canonical" href="https://plexudo.vercel.app/blog/">' in c
        assert '<link rel="canonical" href="https://plexudo.vercel.app/">' not in c

    def test_title_is_blog_specific(self):
        c = read(BLOG_INDEX_HTML)
        assert "<title>Plexudo Blog" in c

    def test_schema_is_collection_page(self):
        c = read(BLOG_INDEX_HTML)
        assert '"@type": "CollectionPage"' in c
        assert 'href="https://plexudo.vercel.app/blog/"' in c

    def test_no_software_application_schema(self):
        c = read(BLOG_INDEX_HTML)
        assert '"@type": "SoftwareApplication"' not in c

class TestBlogPostHtml:
    def test_canonical_is_article_url(self):
        c = read(BLOG_POST_HTML)
        expected = "https://plexudo.vercel.app/blog/google-gemini-student-offer-pakistan-2026/"
        assert f'<link rel="canonical" href="{expected}">' in c

    def test_canonical_not_root(self):
        c = read(BLOG_POST_HTML)
        assert '<link rel="canonical" href="https://plexudo.vercel.app/">' not in c

    def test_schema_is_article(self):
        c = read(BLOG_POST_HTML)
        assert '"@type": "Article"' in c

    def test_schema_webpage_id_is_article_url(self):
        c = read(BLOG_POST_HTML)
        expected_id = "https://plexudo.vercel.app/blog/google-gemini-student-offer-pakistan-2026/#webpage"
        assert expected_id in c

    def test_keywords_meta_is_article_relevant(self):
        c = read(BLOG_POST_HTML)
        assert 'content="Google Gemini student offer Pakistan 2026' in c

class TestSitemapXml:
    def test_includes_homepage(self):
        assert "https://plexudo.vercel.app/" in read(SITEMAP_XML)
    def test_includes_blog_index(self):
        assert "https://plexudo.vercel.app/blog/" in read(SITEMAP_XML)
    def test_includes_blog_post(self):
        assert "google-gemini-student-offer-pakistan-2026" in read(SITEMAP_XML)
    def test_includes_privacy_and_terms(self):
        c = read(SITEMAP_XML)
        assert "https://plexudo.vercel.app/privacy" in c
        assert "https://plexudo.vercel.app/terms" in c
    def test_valid_xml_structure(self):
        import xml.etree.ElementTree as ET
        tree = ET.parse(SITEMAP_XML)
        assert "urlset" in tree.getroot().tag

class TestRobotsTxt:
    def test_disallows_api(self):
        assert "Disallow: /api/" in read(ROBOTS_TXT)
    def test_disallows_dashboard(self):
        assert "Disallow: /dashboard" in read(ROBOTS_TXT)
    def test_disallows_dashboard_html(self):
        assert "Disallow: /dashboard.html" in read(ROBOTS_TXT)
    def test_has_sitemap_directive(self):
        assert "Sitemap: https://plexudo.vercel.app/sitemap.xml" in read(ROBOTS_TXT)

class TestVercelJson:
    def test_has_global_x_content_type_options(self):
        c = read(VERCEL_JSON)
        assert '"X-Content-Type-Options"' in c

    def test_has_global_referrer_policy(self):
        c = read(VERCEL_JSON)
        assert '"Referrer-Policy"' in c

    def test_has_global_x_frame_options(self):
        c = read(VERCEL_JSON)
        assert '"X-Frame-Options"' in c

    def test_tool_redirects_use_301(self):
        with open(VERCEL_JSON, encoding="utf-8") as f:
            v = json.load(f)
        for r in v.get("routes", []):
            if r.get("src") == "/tools/keyword-tool/?":
                assert r.get("status") == 301
                assert r.get("headers", {}).get("Location") == "/tools/trend-analyzer"

    def test_has_blog_index_dest(self):
        with open(VERCEL_JSON, encoding="utf-8") as f:
            v = json.load(f)
        routes = {r.get("src"): r.get("dest") for r in v.get("routes", []) if "dest" in r}
        assert routes.get("/blog/") == "/frontend/blog/index.html"

class TestPrivacyHtml:
    def test_adsense_advertising_disclosure(self):
        c = read(PRIVACY_HTML)
        assert "Google AdSense" in c

    def test_google_ads_opt_out_link(self):
        c = read(PRIVACY_HTML)
        assert "https://www.google.com/settings/ads" in c

    def test_groq_ai_disclosure(self):
        c = read(PRIVACY_HTML)
        assert "Groq" in c

class TestTermsHtml:
    def test_adsense_disclosure(self):
        c = read(TERMS_HTML)
        assert "Google AdSense" in c

    def test_groq_disclosure(self):
        c = read(TERMS_HTML)
        assert "Groq" in c
