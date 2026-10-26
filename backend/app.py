"""

Plexudo - YouTube Creator Analytics & Standalone Utilities

Main Flask Application (YouTube-Only + Groq AI Subsystem)

"""



import os

import sys

import re

import csv
from sqlalchemy import null

import io

import time

import secrets

import json

import uuid

import hashlib

from datetime import datetime, date, timedelta, timezone



from flask import Flask, request, jsonify, send_from_directory, send_file, Response, redirect

from sqlalchemy import create_engine, text

from sqlalchemy.pool import NullPool

from flask_cors import CORS

from werkzeug.middleware.proxy_fix import ProxyFix

from werkzeug.utils import secure_filename

from dotenv import load_dotenv



sys.path.append(os.path.dirname(__file__))

from app.core.config import settings

from app.core.database import database_engine_options, postgres_ssl_args



from models import db, User, Trend, Metric, Sentiment, Report, AuditLog

from services.real_api import fetch_youtube_data, audit_youtube_channel, analyze_youtube_video  # LIVE YouTube Data API v3

from services.nlp_engine import analyze_sentiment

from services.trend_engine import (

    calculate_growth_rate,

    calculate_virality_index,

    calculate_video_virality,

    calculate_engagement_rate,

    calculate_seo_score,

    classify_trend_stage,

    total_views,

)

from services.trend_intelligence import analyze_trend_intelligence

from services.report_generator import generate_pdf_report, generate_pdf_report_buffer

from services.groq_service import chat_with_groq          # Groq AI Service (Llama 3.3 70B)

from services.seo_engine import analyze_seo_metadata



from services.security_guard import (

    rate_limiter,

    ValidationError,

    validate_keyword_input,

    validate_youtube_url,

    validate_channel_identifier,

    API_LIMIT_PER_MIN,

    AI_LIMIT_PER_MIN,

    MAX_UPLOAD_SIZE,

)



import requests as _requests



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")



DATA_DIR = os.environ.get("DATA_DIR", "/tmp" if os.environ.get("VERCEL") else os.path.dirname(__file__))

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "smtas.db")



# Plexudo operates in 100% public/no-login mode. No user caches or token files needed.

def _log_action(action: str, details: str = ""):

    """Write an entry to the audit_logs table."""

    try:

        log = AuditLog(

            user_id=None,

            action=action,

            details=details,

            ip_address=request.remote_addr if request else "127.0.0.1",

        )

        db.session.add(log)

        db.session.commit()

    except Exception:

        pass







app = Flask(__name__, static_folder=None)



# ProxyFix for secure reverse-proxy deployments (e.g. Vercel, Nginx, Render)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)



# Database Configuration (PostgreSQL with pooling when DATABASE_URL is set, SQLite fallback)

database_uri = settings.DATABASE_URL if settings.DATABASE_URL else f"sqlite:///{DB_PATH}"

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = database_engine_options(

    database_uri, production=settings.IS_PRODUCTION or bool(os.environ.get("VERCEL"))

)



app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

app.secret_key = settings.SECRET_KEY

IS_PRODUCTION = settings.IS_PRODUCTION

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION





_CORS_ORIGINS = [o.strip() for o in os.environ.get(

    "CORS_ALLOWED_ORIGINS",

    "https://plexudo.vercel.app,http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173"

).split(",") if o.strip()]

CORS(app, supports_credentials=False, origins=_CORS_ORIGINS)

db.init_app(app)



from services.title_intelligence import generate_context_aware_titles





@app.after_request

def add_security_and_robots_headers(response):

    # Send X-Robots-Tag for private API routes

    if request.path.startswith("/api/"):

        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"

    return response



def _health_database_status():

    """Probe with a separate bounded connection; never expose driver errors."""

    if IS_PRODUCTION and not settings.DATABASE_URL:

        return "error"

    engine = None

    try:

        url = db.engine.url

        if url.get_backend_name() == "postgresql":

            connect_args = {"connect_timeout": 2, "options": "-c statement_timeout=2000"}

            if IS_PRODUCTION:

                connect_args.update(postgres_ssl_args(url))

        elif url.get_backend_name() == "sqlite":

            connect_args = {"timeout": 2}

        else:

            return "error"

        # NullPool avoids waiting on the application's connection pool.

        engine = create_engine(url, poolclass=NullPool, connect_args=connect_args)

        with engine.connect() as connection:

            connection.execute(text("SELECT 1"))

        return "ok"

    except Exception:

        return "error"

    finally:

        if engine is not None:

            engine.dispose()





@app.get("/api/health")

def health():

    # Independent of the YouTube and Groq rate-limit buckets and upstream APIs.

    db_status = _health_database_status()

    response = jsonify({

        "status": "ok" if db_status == "ok" else "degraded",

        "db": db_status,

        "version": os.environ.get("VERCEL_GIT_COMMIT_SHA", "")[:7] or "dev",

        "time": datetime.now(timezone.utc).isoformat(),

    })

    response.headers["Cache-Control"] = "no-store"

    return response





MAX_LOGIN_ATTEMPTS = 5

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()





# --------------------------------------------------------------------------

# Global Safe Error Handlers (Zero Information Leakage)

# --------------------------------------------------------------------------

@app.errorhandler(ValidationError)

def handle_validation_error(e):

    return jsonify({"error": e.message, "field": e.field}), 400





@app.errorhandler(400)

def handle_bad_request(e):

    msg = getattr(e, "description", "Malformed request payload")

    return jsonify({"error": msg}), 400





@app.errorhandler(405)

def handle_method_not_allowed(e):

    return jsonify({"error": "Method not allowed"}), 405





@app.errorhandler(413)

def handle_large_file(e):

    return jsonify({"error": "File size exceeds the 5 MB limit."}), 413





@app.errorhandler(429)

def handle_rate_limit(e):

    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429





@app.errorhandler(404)

def handle_not_found(e):

    if request.path.startswith("/api/"):

        return jsonify({"error": "Requested API resource not found"}), 404

    path = request.path.lstrip("/").lower()

    public_seo_routes = {"blog", "privacy", "terms"}

    if path in public_seo_routes or path.startswith("blog/"):

        return send_from_directory(FRONTEND_DIR, "index.html")

    return jsonify({"error": "Requested resource not found"}), 404





@app.errorhandler(Exception)

def handle_generic_exception(e):

    import traceback

    # Full traceback logged securely on server only

    app.logger.error(f"Internal Server Error: {str(e)}\n{traceback.format_exc()}")

    # Client receives generic safe message

    return jsonify({"error": "An internal system error occurred. Please try again later."}), 500





# --------------------------------------------------------------------------

# Cache Policy

# --------------------------------------------------------------------------

@app.after_request

def apply_cache_control(response):

    # Dynamic API responses should not be cached in ways that leak or cross-contaminate

    if request.path.startswith("/api/"):

        response.headers["Cache-Control"] = (

            "no-store" if request.path == "/api/health"

            else "no-store, no-cache, must-revalidate"

        )

        response.headers["Pragma"]        = "no-cache"

        response.headers["Expires"]       = "0"

    return response





# --------------------------------------------------------------------------

# Static frontend and public SEO route serving

# --------------------------------------------------------------------------

@app.route("/")

def serve_landing():

    return send_from_directory(FRONTEND_DIR, "index.html")





@app.route("/tools")

@app.route("/tools/")

def serve_tools_index():

    return send_from_directory(os.path.join(FRONTEND_DIR, "tools"), "index.html")





@app.route("/tools/<path:tool_name>")

def serve_standalone_tool(tool_name):

    clean_name = tool_name.replace(".html", "")

    target = os.path.join(FRONTEND_DIR, "tools", f"{clean_name}.html")

    if os.path.isfile(target):

        return send_from_directory(os.path.join(FRONTEND_DIR, "tools"), f"{clean_name}.html")

    return jsonify({"error": "Tool not found"}), 404





BLOG_DIR = os.path.join(FRONTEND_DIR, "blog")



BLOG_ALIASES = {

    "competitor-analysis-guide": "youtube-competitor-channel-analysis-guide",

    "trending-keywords-guide": "how-to-find-high-search-low-competition-youtube-keywords",

}





@app.route("/privacy")

@app.route("/privacy/")

def serve_privacy_page():

    return send_from_directory(FRONTEND_DIR, "privacy.html")





@app.route("/privacy.html")

def redirect_privacy_html():

    return redirect("/privacy", code=301)





@app.route("/terms")

@app.route("/terms/")

def serve_terms_page():

    return send_from_directory(FRONTEND_DIR, "terms.html")





@app.route("/terms.html")

def redirect_terms_html():

    return redirect("/terms", code=301)





@app.route("/blog")

def redirect_blog_index():

    return redirect("/blog/", code=301)





@app.route("/blog/")

def serve_blog_index():

    return send_from_directory(BLOG_DIR, "index.html")





@app.route("/blog/<path:slug>")

def serve_blog_article(slug):

    raw_slug = slug.strip("/")

    if raw_slug in BLOG_ALIASES:

        canonical_target = BLOG_ALIASES[raw_slug]

        return redirect(f"/blog/{canonical_target}/", code=301)



    article_dir = os.path.join(BLOG_DIR, raw_slug)

    article_file = os.path.join(article_dir, "index.html")

    if os.path.isfile(article_file):

        if not slug.endswith("/"):

            return redirect(f"/blog/{raw_slug}/", code=301)

        return send_from_directory(article_dir, "index.html")



    return jsonify({"error": "Blog article not found"}), 404





@app.route("/favicon.ico")

def serve_favicon_ico():

    return send_from_directory(FRONTEND_DIR, "favicon.ico", mimetype="image/x-icon")





@app.route("/favicon.svg")

def serve_favicon_svg():

    return send_from_directory(FRONTEND_DIR, "favicon.svg", mimetype="image/svg+xml")





@app.route("/favicon.png")

@app.route("/apple-touch-icon.png")

def serve_favicon_png():

    return send_from_directory(FRONTEND_DIR, "favicon.png", mimetype="image/png")





@app.route("/<path:path>")

def serve_static_or_public(path):

    clean_path = path.strip("/").lower()



    if clean_path in ("privacy.html", "privacy"):

        if clean_path == "privacy.html":

            return redirect("/privacy", code=301)

        return send_from_directory(FRONTEND_DIR, "privacy.html")



    if clean_path in ("terms.html", "terms"):

        if clean_path == "terms.html":

            return redirect("/terms", code=301)

        return send_from_directory(FRONTEND_DIR, "terms.html")



    if clean_path == "blog":

        return redirect("/blog/", code=301)



    if clean_path.startswith("blog/"):

        sub_slug = clean_path[len("blog/"):]

        return serve_blog_article(sub_slug)



    file_path = os.path.join(FRONTEND_DIR, path)

    if os.path.isfile(file_path):

        return send_from_directory(FRONTEND_DIR, path)



    clean_path = path.strip("/").lower()

    if clean_path == "tools":

        return send_from_directory(os.path.join(FRONTEND_DIR, "tools"), "index.html")

    if clean_path.startswith("tools/"):

        tool_sub = clean_path[len("tools/"):].replace(".html", "")

        tool_file = os.path.join(FRONTEND_DIR, "tools", f"{tool_sub}.html")

        if os.path.isfile(tool_file):

            return send_from_directory(os.path.join(FRONTEND_DIR, "tools"), f"{tool_sub}.html")



    return jsonify({"error": "Requested resource not found"}), 404







# --------------------------------------------------------------------------

# YouTube Data Acquisition + Sentiment + Scoring

# --------------------------------------------------------------------------

def validate_trend_filters(data):

    if not isinstance(data, dict) and not hasattr(data, "to_dict"):

        raise ValidationError("Payload must be a JSON object")

    allowed = {

        "region": {"Global", "United States", "India", "Pakistan", "United Kingdom"},

        "category": {"All", "Music", "Gaming", "Comedy", "Tech", "Education", "Sports", "News", "Lifestyle"},

        "timeframe": {"24h", "7d", "30d"},

    }

    for key, values in allowed.items():

        value = data.get(key, {"region": "Global", "category": "All", "timeframe": "7d"}[key])

        if not isinstance(value, str) or value not in values:

            raise ValidationError(f"Unsupported {key}", key)





def trend_error_response(result):

    status = result.get("status")

    status = status if isinstance(status, int) and 400 <= status <= 599 else 502

    return jsonify({"error": result.get("message", "YouTube data is unavailable. Please retry."),

                    "quota_exceeded": bool(result.get("quota_exceeded"))}), status





@app.route("/api/search", methods=["POST"])

def search_trend():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"search_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    data = request.get_json(force=True)

    if not data:

        return jsonify({"error": "Missing payload"}), 400



    validate_trend_filters(data)

    raw_kw = data.get("keyword")

    region = data.get("region") or "Pakistan"

    category = data.get("category", "All")

    timeframe = data.get("timeframe", "7d")



    if raw_kw is not None:

        keyword = validate_keyword_input(raw_kw)

    else:

        keyword = category if category != "All" else "Trending"



    results = {}

    search_result = _process_platform(

        keyword, "YouTube", fetch_youtube_data,

        region=region, category=category, timeframe=timeframe

    )

    results["YouTube"] = search_result



    if search_result.get("error"):

        return trend_error_response(search_result)



    _log_action("SEARCH", f"keyword={keyword} platform=YouTube")

    return jsonify({"keyword": keyword, "results": results})





@app.route("/api/trending-feed", methods=["GET", "POST"])

@app.route("/api/trending", methods=["GET", "POST"])

def get_trending_feed():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"search_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    if request.method == "POST":

        data = request.get_json(force=True) or {}

    else:

        data = request.args



    validate_trend_filters(data)

    raw_kw = data.get("keyword") or data.get("q") or ""

    if not isinstance(raw_kw, str):

        raise ValidationError("Keyword must be a string", "keyword")

    raw_kw = raw_kw.strip()

    region = data.get("region", "Global")

    category = data.get("category", "All")

    timeframe = data.get("timeframe", "7d")



    if raw_kw:

        keyword = validate_keyword_input(raw_kw)

    else:

        keyword = category if category != "All" else "Trending"



    results = {}

    search_result = _process_platform(

        keyword, "YouTube", fetch_youtube_data,

        region=region, category=category, timeframe=timeframe

    )

    results["YouTube"] = search_result



    if search_result.get("error"):

        return trend_error_response(search_result)



    kpis = search_result.get("kpis", {})

    if "topCategory" in kpis and "fastestCategory" not in kpis:

        kpis["fastestCategory"] = kpis["topCategory"]



    return jsonify({

        "status": 200,

        "keyword": keyword,

        "results": results,

        "videos": search_result.get("top_videos", []),

        "kpis": kpis,

        "catBreakdown": search_result.get("cat_breakdown", []),

        "timeSeries": search_result.get("time_series", []),

        "cached": bool(search_result.get("cached", False)),

        "is_stale": bool(search_result.get("is_stale", False)),

        "fetched_at": search_result.get("fetched_at"),

        "cache_served_at": search_result.get("cache_served_at"),

    })





def _process_platform(keyword, platform_name, fetch_fn, region="Global", category="All", timeframe="7d"):

    try:

        raw = fetch_fn(keyword, region=region, category=category, timeframe=timeframe)

    except Exception as e:

        app.logger.error(f"Error fetching {platform_name} data: {e}")

        if "YOUTUBE_API_KEY" in str(e) or "API key is not set" in str(e):
            return {
                "error": True,
                "message": "YouTube data is unavailable because YOUTUBE_API_KEY is not configured for this deployment environment. Please configure YOUTUBE_API_KEY in Vercel project settings.",
                "status": 500,
                "quota_exceeded": False,
            }
        return {"error": True, "message": f"Could not fetch {platform_name} data. Please try again later.", "status": 500}



    if raw.get("status") != 200:

        return {

            "error": True,

            "message": raw.get("error", f"{platform_name} API request failed."),

            "status": raw.get("status"),

            "quota_exceeded": raw.get("quota_exceeded", False)

        }



    growth_rate = calculate_growth_rate(raw["daily_metrics"])

    virality = calculate_virality_index(raw["daily_metrics"])

    engagement = calculate_engagement_rate(raw["daily_metrics"])

    if engagement is None:
        virality = None

    seo_analysis = calculate_seo_score(raw["daily_metrics"], keyword)

    stage = classify_trend_stage(growth_rate)

    views_sum = total_views(raw["daily_metrics"])



    sentiment_result = analyze_sentiment(raw["comments"])



    # Generate YouTube Tags & Context-Aware Title Ideas

    related_list = raw.get("related_keywords", [])

    youtube_tags = [keyword] + [r for r in related_list if r.lower() != keyword.lower()]

    hashtag_list = [f"#{t.replace(' ', '')}" for t in youtube_tags[:6]]



    top_v_title = raw.get("title", "")

    top_video_titles = [top_v_title] if top_v_title else []



    # Keep optional writing assistance deterministic and off the critical API path.

    # A general feed does not identify a single subject for meaningful titles/tags.

    general_feed = keyword.lower().strip() in {"trending", "all", "pulsecheck"}

    if general_feed:

        youtube_tags, hashtag_list, seo_title_ideas = [], [], []

    else:

        seo_title_ideas = [

            f"{keyword}: A Beginner's Guide",

            f"{keyword}: Key Questions Answered",

            f"Understanding {keyword}: A Step-by-Step Overview",

            f"{keyword}: What to Know Before You Start",

        ]



    # Only compare the same filters AND video cohort. Legacy rows have no key.

    cohort = sorted(v["id"] for v in raw.get("top_videos", []) if v.get("id"))

    observation_key = hashlib.sha256(json.dumps(

        [keyword.lower().strip(), platform_name, region, category, timeframe, cohort]

    ).encode()).hexdigest()



    # Phase 8 — Trend Intelligence multi-scan analysis

    past_trends = (

        Trend.query.filter(

            db.func.lower(Trend.keyword) == keyword.lower().strip(),

            Trend.platform == platform_name,

            Trend.observation_key == observation_key,

        )

        .order_by(Trend.timestamp.asc())

        .all()

    )



    collection_time = None
    if raw.get("fetched_at"):
        try:
            collection_time = datetime.fromisoformat(raw["fetched_at"])
            if collection_time.tzinfo is None or collection_time > datetime.now(timezone.utc):
                collection_time = None
        except (ValueError, TypeError):
            collection_time = None

    trend_intel = analyze_trend_intelligence(

        keyword=keyword,

        platform_name=platform_name,

        current_views=views_sum,

        current_engagement=engagement,

        sentiment_result=sentiment_result,

        past_trends=past_trends,

        now=collection_time,

    )



    stage = trend_intel["current_direction"]
    trend_intel["cohort_comparable"] = True
    trend_intel["observation_key"] = observation_key

    # Clean topic-appropriate fallback for sample comment if empty

    if not sentiment_result.get("sample_comment"):

        sentiment_result["sample_comment"] = "No recent audience comments available for this topic."



    trend = Trend(

        keyword=keyword,

        platform=platform_name,

        observation_key=observation_key,

        timestamp=datetime.fromisoformat(trend_intel["last_seen_at"]),

        total_views=views_sum,

        growth_rate=trend_intel["velocity"] if trend_intel["velocity"] is not None else null(),

        virality_score=virality if virality is not None else null(),

        peak_date=datetime.now(timezone.utc),

        created_by=None,

        first_seen_at=datetime.fromisoformat(trend_intel["first_seen_at"]),

        last_seen_at=datetime.fromisoformat(trend_intel["last_seen_at"]),

        scan_count=trend_intel["scan_count"],

        current_trend_score=trend_intel["current_trend_score"] if trend_intel["current_trend_score"] is not None else null(),

        current_direction=trend_intel["current_direction"],

        current_confidence=trend_intel["current_confidence"],

        current_velocity=trend_intel["velocity"] if trend_intel["velocity"] is not None else null(),

        current_acceleration=trend_intel["acceleration"] if trend_intel["acceleration"] is not None else null(),

    )

    db.session.add(trend)

    db.session.flush()



    for day in raw["daily_metrics"]:

        db.session.add(Metric(

            trend_id=trend.trend_id,

            views=day["views"],

            likes=day["likes"] if day["likes"] is not None else null(),

            shares=day["shares"] if day["shares"] is not None else null(),

            comments_count=day["comments_count"] if day["comments_count"] is not None else null(),

            recorded_date=datetime.strptime(day["date"], "%Y-%m-%d").date(),

            engagement_rate=engagement,

            source="youtube_api",

        ))



    db.session.add(Sentiment(

        trend_id=trend.trend_id,

        positive_score=sentiment_result["positive_score"],

        negative_score=sentiment_result["negative_score"],

        neutral_score=sentiment_result["neutral_score"],

        dominant_sentiment=sentiment_result["dominant_sentiment"],

        sample_comment=sentiment_result["sample_comment"],

    ))

    db.session.commit()



    return {

        "trend_id": trend.trend_id,

        "keyword": keyword,

        "platform": platform_name,

        "total_views": views_sum,

        "growth_rate": trend_intel["velocity"],

        "virality_score": virality,

        "engagement_rate": raw.get("kpis", {}).get("avgEngagement", engagement) if "avgEngagement" in raw.get("kpis", {}) else engagement,

        "seo_analysis": seo_analysis,

        "stage": stage,

        "daily_metrics": raw["daily_metrics"],

        "sentiment": sentiment_result,

        "related_keywords": related_list,

        "youtube_tags": youtube_tags[:10],

        "youtube_hashtags": hashtag_list,

        "seo_title_ideas": seo_title_ideas,

        # Phase 8 Intelligence keys

        "trend_intelligence": trend_intel,

        "status": trend_intel["status"],

        "scan_count": trend_intel["scan_count"],

        "snapshot_count": trend_intel["scan_count"],

        "first_seen_at": trend_intel["first_seen_at"],

        "last_seen_at": trend_intel["last_seen_at"],

        "current_trend_score": trend_intel["current_trend_score"],

        "current_trend_score_display": trend_intel["current_trend_score_display"],

        "current_direction": trend_intel["current_direction"],

        "current_direction_display": trend_intel["current_direction_display"],

        "current_confidence": trend_intel["current_confidence"],

        "velocity": trend_intel["velocity"],

        "velocity_display": trend_intel["velocity_display"],

        "acceleration": trend_intel["acceleration"],

        "acceleration_display": trend_intel["acceleration_display"],

        "educational_banner": trend_intel["educational_banner"],

        "historical_context": trend_intel["historical_context"],

        "timeline": trend_intel["timeline"],

        "events": trend_intel["events"],

        "forecast": trend_intel["forecast"],

        # Rich trending set & charts breakdown

        "top_videos": raw.get("top_videos", []),

        "kpis": raw.get("kpis", {}),

        "cat_breakdown": raw.get("cat_breakdown", []),

        "time_series": raw.get("time_series", []),

        "cached": bool(raw.get("cached", False)),
        "is_stale": bool(raw.get("is_stale", False)),
        "fetched_at": raw.get("fetched_at"),
        "cache_served_at": raw.get("cache_served_at"),

        "region": region,

        "category": category,

        "timeframe": timeframe,

    }





# --------------------------------------------------------------------------

# History / Listing

# --------------------------------------------------------------------------

@app.route("/api/trends", methods=["GET"])

def list_trends():

    trends = Trend.query.order_by(Trend.timestamp.desc()).limit(50).all()



    output = []

    for t in trends:

        sentiment = Sentiment.query.filter_by(trend_id=t.trend_id).first()

        growth = t.growth_rate

        output.append({

            "trend_id": t.trend_id,

            "keyword": t.keyword,

            "platform": t.platform,

            "total_views": t.total_views,

            "growth_rate": growth,

            "virality_score": t.virality_score,

            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M"),

            "dominant_sentiment": sentiment.dominant_sentiment if sentiment else "n/a",

        })

    return jsonify({"trends": output})





# --------------------------------------------------------------------------

# Keyword Comparison Endpoint (Compares multiple YouTube searches)

# --------------------------------------------------------------------------

@app.route("/api/compare-keywords", methods=["GET", "POST"])

def compare_keywords():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"compare_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    ids = []

    if request.method == "POST" and request.is_json:

        data = request.get_json(silent=True) or {}

        raw_ids = data.get("ids", [])

        if isinstance(raw_ids, list):

            for i in raw_ids:

                try:

                    ids.append(int(i))

                except (ValueError, TypeError):

                    pass



    ids_param = request.args.get("ids", "")

    if ids_param:

        try:

            ids.extend([int(i) for i in ids_param.split(",") if i.strip()])

        except ValueError:

            pass



    if ids:

        trends = Trend.query.filter(Trend.trend_id.in_(ids)).all()

    else:

        # Default: latest 6 unique keywords

        trends = Trend.query.order_by(Trend.timestamp.desc()).limit(6).all()



    comparison_data = []

    for t in trends:

        metrics = Metric.query.filter_by(trend_id=t.trend_id).order_by(Metric.recorded_date).all()

        sentiment = Sentiment.query.filter_by(trend_id=t.trend_id).first()



        growth = t.growth_rate

        virality = t.virality_score

        if metrics and len(metrics) >= 2:

            d_metrics = [{"views": m.views, "likes": m.likes, "shares": m.shares, "comments_count": m.comments_count} for m in metrics]

            growth = calculate_growth_rate(d_metrics)

            virality = calculate_virality_index(d_metrics)



        comparison_data.append({

            "trend_id": t.trend_id,

            "keyword": t.keyword,

            "total_views": t.total_views,

            "growth_rate": growth,

            "virality_score": virality,

            "stage": classify_trend_stage(growth),

            "dominant_sentiment": sentiment.dominant_sentiment if sentiment else "n/a",

            "daily_metrics": [{"date": m.recorded_date.strftime("%Y-%m-%d"), "views": m.views} for m in metrics]

        })



    return jsonify({"comparison": comparison_data})





# --------------------------------------------------------------------------

# Report Generators — PDF & CSV

# --------------------------------------------------------------------------

@app.route("/api/report/<int:trend_id>", methods=["GET", "POST"])

def generate_report(trend_id):

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"report_ip_{client_ip}", 30, 60)

    if not allowed:

        return jsonify({"error": f"Report rate limit exceeded. Please wait {retry_after} seconds."}), 429



    trend = Trend.query.filter_by(trend_id=trend_id).first()

    if not trend:

        return jsonify({"error": "Trend report not found"}), 404



    try:

        sentiment = Sentiment.query.filter_by(trend_id=trend_id).first()

        sentiment_dict = {

            "positive_score": sentiment.positive_score,

            "negative_score": sentiment.negative_score,

            "neutral_score": sentiment.neutral_score,

            "dominant_sentiment": sentiment.dominant_sentiment,

        } if sentiment else {"positive_score": 0, "negative_score": 0, "neutral_score": 0, "dominant_sentiment": "n/a"}



        trend_dict = {

            "keyword": trend.keyword,

            "platform": trend.platform,

            "total_views": trend.total_views,

        }

        stage = trend.current_direction or "BASELINE"



        user_email = "Anonymous User"



        filename, buffer = generate_pdf_report_buffer(

            trend_dict, sentiment_dict, None if stage == "BASELINE" else trend.growth_rate, trend.virality_score, stage, user_email

        )



        report = Report(trend_id=trend_id, generated_by=None, format="PDF", file_path=f"memory://{filename}")

        db.session.add(report)

        db.session.commit()

        _log_action("EXPORT_PDF", f"trend_id={trend_id} keyword={trend.keyword}")



        return send_file(

            buffer,

            mimetype="application/pdf",

            as_attachment=True,

            download_name=filename,

        )

    except Exception as e:

        app.logger.error(f"Failed to generate PDF report: {e}")

        return jsonify({"error": "Failed to generate report"}), 500





@app.route("/api/export-csv/<int:trend_id>", methods=["GET"])

def export_csv(trend_id):

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"export_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Export rate limit exceeded. Please wait {retry_after} seconds."}), 429



    trend = Trend.query.filter_by(trend_id=trend_id).first()

    if not trend:

        return jsonify({"error": "Trend report not found"}), 404



    sentiment = Sentiment.query.filter_by(trend_id=trend_id).first()

    metrics = Metric.query.filter_by(trend_id=trend_id).order_by(Metric.recorded_date).all()



    output = io.StringIO()

    writer = csv.writer(output)



    writer.writerow(["Plexudo - YouTube Trend Analysis CSV Export"])

    writer.writerow(["Generated By", "Anonymous User"])

    writer.writerow(["Generated On", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")])

    writer.writerow([])



    writer.writerow(["Keyword", "Platform", "Total Views", "Observed Change (%)", "Virality Index (Heuristic)", "Trend Stage", "Timestamp"])

    stage = trend.current_direction or "BASELINE"

    safe_keyword = "'" + trend.keyword if trend.keyword.lstrip().startswith(("=", "+", "-", "@")) else trend.keyword

    writer.writerow([

        safe_keyword, trend.platform, trend.total_views,

        "Pending" if stage == "BASELINE" else ("Unavailable" if trend.growth_rate is None else trend.growth_rate), "Unavailable" if trend.virality_score is None else trend.virality_score, stage,

        trend.timestamp.strftime("%Y-%m-%d %H:%M")

    ])

    writer.writerow([])



    if sentiment:

        classified_sentiment = sum(v or 0 for v in (sentiment.positive_score, sentiment.negative_score, sentiment.neutral_score)) > 0 and (sentiment.dominant_sentiment or "").lower() != "unavailable"

        writer.writerow(["Sentiment Analysis"])

        writer.writerow(["Positive (%)", "Negative (%)", "Neutral (%)", "Dominant"])

        writer.writerow([

            sentiment.positive_score if classified_sentiment else "Unavailable", sentiment.negative_score if classified_sentiment else "Unavailable",

            sentiment.neutral_score if classified_sentiment else "Unavailable", sentiment.dominant_sentiment

        ])

        writer.writerow([])



    writer.writerow(["Recorded Snapshots (Lifetime Counters)"])

    writer.writerow(["Date", "Views", "Likes", "Shares", "Comments"])

    for m in metrics:

        likes_val = m.likes if m.likes is not None else "Unavailable"

        writer.writerow([m.recorded_date, m.views, likes_val, "Unavailable" if m.shares is None else m.shares, "Unavailable" if m.comments_count is None else m.comments_count])



    csv_data = output.getvalue()

    output.close()



    _log_action("EXPORT_CSV", f"trend_id={trend_id} keyword={trend.keyword}")



    filename = f"plexudo_{secure_filename(trend.keyword) or 'topic'}_YouTube.csv"

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={"Content-Disposition": f"attachment; filename={filename}"}

    )





# --------------------------------------------------------------------------

# Groq AI Chat

# --------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])

def ai_chat():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"ai_ip_{client_ip}", AI_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"AI request limit reached. Please wait {retry_after} seconds."}), 429



    data = request.get_json(force=True)

    if not data:

        return jsonify({"error": "Message payload is required"}), 400



    message = data.get("message", "").strip()

    trend_context = data.get("context") or data.get("trend_context", None)

    history = data.get("history", [])

    if not isinstance(history, list):

        history = []



    if not message:

        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 1000:

        return jsonify({"error": "Message exceeds maximum length (1,000 characters)"}), 400



    if not trend_context:

        topic_match = re.search(r'(?:trending topic|topic):\s*["\']([^"\']+)["\']', message, re.IGNORECASE)

        if topic_match:

            detected_topic = topic_match.group(1).strip()

            trend_context = {"keyword": detected_topic}



    if trend_context and isinstance(trend_context, dict) and "keyword" in trend_context and "related_keywords" not in trend_context:

        try:

            from backend.services.real_api import _fetch_related_keywords

            rel = _fetch_related_keywords(str(trend_context["keyword"]).strip())

            if rel:

                trend_context["related_keywords"] = rel[:5]

        except Exception:

            pass



    result = chat_with_groq(message, trend_context, history=history)

    _log_action("CHAT", f"msg_preview={message[:80]}")

    return jsonify(result)





# --------------------------------------------------------------------------

# YouTube Keyword Suggestions (Autocomplete)

# --------------------------------------------------------------------------

_SUGGEST_CACHE = {}

_SUGGEST_CACHE_TTL = 900  # 15 minutes





@app.route("/api/suggest", methods=["GET"])

def keyword_suggest():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"suggest_ip_{client_ip}", API_LIMIT_PER_MIN * 2, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds.", "suggestions": []}), 429



    query = request.args.get("q", "").strip()

    if not query or len(query) < 2 or len(query) > 100:

        return jsonify({"suggestions": []})



    # Reject invalid control characters

    if re.search(r'[\x00-\x1F<>]', query):

        return jsonify({"suggestions": []})



    cache_key = query.lower()

    cached = _SUGGEST_CACHE.get(cache_key)

    if cached:

        ts, data = cached

        if time.time() - ts < _SUGGEST_CACHE_TTL:

            return jsonify({"suggestions": data})



    suggestions = []



    if YOUTUBE_API_KEY:

        try:

            res = _requests.get(

                "https://www.googleapis.com/youtube/v3/search",

                params={

                    "part": "snippet",

                    "q": query,

                    "type": "video",

                    "maxResults": 8,

                    "order": "viewCount",

                    "key": YOUTUBE_API_KEY,

                },

                timeout=5,

            )

            if res.status_code == 200:

                items = res.json().get("items", [])

                seen = set()

                for item in items:

                    title = item["snippet"].get("title", "")

                    words = title.split()

                    phrase = " ".join(words[:4]).strip()

                    if phrase and phrase.lower() not in seen and query.lower() in phrase.lower():

                        suggestions.append(phrase)

                        seen.add(phrase.lower())

                    if len(title) <= 50 and title.lower() not in seen:

                        suggestions.append(title)

                        seen.add(title.lower())

        except Exception:

            pass



    if len(suggestions) < 5:

        try:

            gs_res = _requests.get(

                "https://suggestqueries.google.com/complete/search",

                params={"client": "firefox", "ds": "yt", "q": query},

                timeout=5,

            )

            if gs_res.status_code == 200:

                raw = gs_res.json()

                google_suggs = raw[1] if len(raw) > 1 else []

                for s in google_suggs[:8]:

                    if s not in suggestions:

                        suggestions.append(s)

        except Exception:

            pass



    final_suggestions = suggestions[:10]

    _SUGGEST_CACHE[cache_key] = (time.time(), final_suggestions)

    return jsonify({"suggestions": final_suggestions})





# --------------------------------------------------------------------------

# Channel / URL Audit Endpoint

# --------------------------------------------------------------------------

@app.route("/api/audit-channel", methods=["POST"])

def audit_channel():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"audit_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    data = request.get_json(force=True)

    if not data:

        return jsonify({"error": "Missing payload"}), 400



    raw_identifier = data.get("identifier", "")

    identifier = validate_channel_identifier(raw_identifier)



    is_handle = identifier.startswith("@") or ("/" not in identifier and not identifier.startswith("http"))

    result    = audit_youtube_channel(identifier, is_handle=is_handle)



    _log_action("AUDIT_CHANNEL", f"identifier={identifier}")

    # Normalize response keys for frontend compatibility

    result["title"] = result.get("title") or result.get("channel_name", "")

    result["subscribers"] = result.get("subscribers") or result.get("subscriber_count", 0)

    result["channel_age_years"] = result.get("channel_age_years") if result.get("channel_age_years") is not None else result.get("age_years", 0)

    result["est_monthly_earnings_min"] = result.get("est_monthly_earnings_min") if result.get("est_monthly_earnings_min") is not None else result.get("earn_min_monthly", 0)

    result["est_monthly_earnings_max"] = result.get("est_monthly_earnings_max") if result.get("est_monthly_earnings_max") is not None else result.get("earn_max_monthly", 0)

    return jsonify(result)





# --------------------------------------------------------------------------

# YouTube Video Analysis Endpoint

# --------------------------------------------------------------------------

@app.route("/api/video-analysis", methods=["POST"])

def video_analysis():

    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"video_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    data = request.get_json(force=True)

    if not data:

        return jsonify({"error": "Missing payload"}), 400



    raw_url = data.get("url", "").strip()

    url = validate_youtube_url(raw_url)



    result = analyze_youtube_video(url)





    if result.get("error"):

        _log_action("VIDEO_ANALYSIS_ERROR", f"url={url} err={result.get('message','')}")

        return jsonify(result), 400



    # Run NLP sentiment

    sentiment = analyze_sentiment(result["comments"])



    # Virality & growth scores

    growth_rate   = calculate_growth_rate(result["daily_metrics"])

    virality      = calculate_video_virality(

        result.get("view_count", 0),

        result.get("like_count", 0),

        result.get("comment_count", 0),

        result.get("upload_date", "")

    )

    engagement    = calculate_engagement_rate(result["daily_metrics"])

    stage         = classify_trend_stage(growth_rate)



    _log_action("VIDEO_ANALYSIS", f"video_id={result['video_id']} title={result['title'][:60]}")



    return jsonify({

        **result,

        "success":       True,

        "sentiment":     sentiment,

        "growth_rate":   growth_rate,

        "virality_score": virality,

        "engagement_rate": engagement,

        "stage":         stage,

        "channel_title": result.get("channel_title") or result.get("channel_name", ""),

        "views":         result.get("views") or result.get("view_count", 0),

        "published_at":  result.get("published_at") or result.get("upload_date", ""),

        "description":   result.get("description", ""),

        "seo_quality":   analyze_seo_metadata(

            title=result.get("title", ""),

            description=result.get("description", ""),

            tags=result.get("tags", []),

        ),

    })





# --------------------------------------------------------------------------

# YouTube SEO Intelligence Endpoint (Metadata Quality & Optimization)

# --------------------------------------------------------------------------

@app.route("/api/seo/analyze", methods=["POST"])

def analyze_seo():

    # Enforce 64 KB route-specific body limit

    raw_body = request.get_data()

    if len(raw_body) > 65536:

        return jsonify({"error": "Payload exceeds 64 KB limit"}), 413



    if not request.is_json:

        return jsonify({"error": "Content-Type must be application/json"}), 415



    client_ip = request.remote_addr or "127.0.0.1"

    allowed, retry_after = rate_limiter.is_allowed(f"seo_ip_{client_ip}", API_LIMIT_PER_MIN, 60)

    if not allowed:

        return jsonify({"error": f"Rate limit exceeded. Please wait {retry_after} seconds."}), 429



    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):

        return jsonify({"error": "Malformed or invalid JSON payload"}), 400



    allowed_keys = {"title", "description", "tags", "focus_keyword", "language"}

    extra_keys = set(data.keys()) - allowed_keys

    if extra_keys:

        return jsonify({"error": "Payload contains unrecognized fields"}), 400



    if "title" not in data or not isinstance(data["title"], str):

        return jsonify({"error": "Field 'title' is required and must be a string"}), 400



    raw_title = data["title"]

    if len(raw_title) > 200:

        return jsonify({"error": "Field 'title' exceeds maximum length of 200 characters"}), 400



    title = raw_title.strip()

    if not title:

        return jsonify({"error": "Field 'title' cannot be empty"}), 400



    description = data.get("description", "")

    if description is not None and not isinstance(description, str):

        return jsonify({"error": "Field 'description' must be a string"}), 400

    if description and len(description) > 10000:

        return jsonify({"error": "Field 'description' exceeds maximum length of 10,000 characters"}), 400



    tags = data.get("tags", [])

    if tags is not None:

        if not isinstance(tags, list):

            return jsonify({"error": "Field 'tags' must be a list of strings"}), 400

        if len(tags) > 100:

            return jsonify({"error": "Field 'tags' exceeds maximum limit of 100 items"}), 400

        for t in tags:

            if not isinstance(t, str):

                return jsonify({"error": "All items in 'tags' must be strings"}), 400

            if len(t) > 100:

                return jsonify({"error": "Individual tag exceeds maximum length of 100 characters"}), 400



    focus_keyword = data.get("focus_keyword")

    if focus_keyword is not None and not isinstance(focus_keyword, str):

        return jsonify({"error": "Field 'focus_keyword' must be a string"}), 400

    if focus_keyword and len(focus_keyword) > 100:

        return jsonify({"error": "Field 'focus_keyword' exceeds maximum length of 100 characters"}), 400



    language = data.get("language", "auto")

    if language is not None and not isinstance(language, str):

        return jsonify({"error": "Field 'language' must be a string"}), 400



    result = analyze_seo_metadata(

        title=title,

        description=description or "",

        tags=tags or [],

        focus_keyword=focus_keyword,

        language=language or "auto",

    )

    return jsonify(result), 200





# /api/audit-log has been removed from the public API.

# Internal audit logs are not exposed to anonymous visitors.







# --------------------------------------------------------------------------

# App bootstrap

# --------------------------------------------------------------------------

def create_tables():

    # Production schemas are initialized only through a separately reviewed,

    # explicitly authorized procedure. Never migrate during a cold start.

    if settings.IS_PRODUCTION or os.environ.get("VERCEL"):

        return

    with app.app_context():

        db.create_all()

        try:

            from migrate_db import run_migration

            run_migration(db.engine)

        except Exception as e:

            app.logger.warning(f"Database migration notice: {e}")

        # NOTE: No default accounts are seeded. All user accounts must be

        # created through the normal registration flow or via environment

        # variable-controlled seed scripts in controlled deployment pipelines.





create_tables()





if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    print(f"Plexudo YouTube backend running at http://127.0.0.1:{port}")

    app.run(debug=debug_mode, host="0.0.0.0", port=port, threaded=True)

