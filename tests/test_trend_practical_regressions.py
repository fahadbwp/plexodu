"""Practical release: regressions for real-data correctness and error handling."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
import pytest
from test_phase8_trend_intelligence import DummyTrend, get_flask_module
from services.trend_intelligence import analyze_trend_intelligence, compute_historical_window_change
from services import real_api
from services.nlp_engine import analyze_sentiment


def test_refreshes_cannot_manufacture_confidence_or_forecast():
    now = datetime.now(timezone.utc)
    past = [DummyTrend(i, 1000, now - timedelta(seconds=60-i)) for i in range(40)]
    result = analyze_trend_intelligence('topic', 'YouTube', 1100, 2, {}, past, now)
    assert result['status'] == 'baseline'
    assert result['current_confidence'] == 'Low'
    assert result['velocity'] is None
    assert not result['forecast']['available']


def test_old_observation_is_not_a_one_day_baseline():
    now = datetime.now(timezone.utc)
    observations = [{'timestamp': now-timedelta(days=90), 'views': 100}, {'timestamp': now, 'views': 200}]
    assert compute_historical_window_change(observations, 200, now, 1)['status'] == 'insufficient_history'


@pytest.mark.parametrize('payload', [[1], {'keyword': 12}, {'timeframe': 'forever'}, {'region': []}])
def test_invalid_feed_inputs_return_400(payload):
    mod = get_flask_module()
    assert mod.app.test_client().post('/api/trending-feed', json=payload).status_code == 400


@pytest.mark.parametrize('status', [429, 502, 504])
def test_feed_propagates_upstream_error(status):
    mod = get_flask_module()
    with patch.object(mod, 'fetch_youtube_data', return_value={'status': status, 'error': 'Service unavailable'}):
        response = mod.app.test_client().get('/api/trending-feed?q=errors')
    assert response.status_code == status
    assert response.json['error']
    assert 'videos' not in response.json


def test_filters_and_cohorts_have_separate_history():
    mod = get_flask_module()
    raw = {'status': 200, 'title': 'Demo', 'comments': [], 'related_keywords': [],
           'daily_metrics': [{'date': '2026-10-11', 'views': 100, 'likes': 2, 'comments_count': 0, 'shares': 0}],
           'top_videos': [{'id': 'cohort-one'}]}
    keyword = 'regression-isolation'
    with mod.app.app_context():
        with patch.object(mod, 'fetch_youtube_data', return_value=raw):
            client = mod.app.test_client()
            for region in ['Pakistan', 'India']:
                assert client.post('/api/search', json={'keyword': keyword, 'region': region}).status_code == 200
            raw['top_videos'] = [{'id': 'cohort-two'}]
            assert client.post('/api/search', json={'keyword': keyword, 'region': 'Pakistan'}).status_code == 200
        rows = mod.Trend.query.filter_by(keyword=keyword).order_by(mod.Trend.trend_id.desc()).limit(3).all()
        assert len({row.observation_key for row in rows}) == 3
        assert all(row.current_confidence == 'Low' for row in rows)


@pytest.mark.parametrize('timeframe,days', [('24h', 1), ('7d', 7), ('30d', 30)])
def test_real_api_filters_aggregates_and_never_fills_empty_buckets(timeframe, days):
    captured = []
    now = datetime.now(timezone.utc)
    def get(url, **kwargs):
        params = kwargs.get('params', {})
        captured.append((url, params))
        if url == real_api.SEARCH_URL:
            return Mock(status_code=200, json=lambda: {'items': [{'id': {'videoId': 'aaa'}}, {'id': {'videoId': 'bbb'}}]})
        if url == real_api.VIDEOS_URL:
            items = [{'id': vid, 'snippet': {'title': vid, 'publishedAt': (now-timedelta(hours=3)).isoformat(), 'categoryId': '20'},
                      'statistics': {'viewCount': str(views), 'likeCount': '10', 'commentCount': '2'}} for vid, views in [('aaa', 100), ('bbb', 200)]]
            return Mock(status_code=200, json=lambda: {'items': items})
        return Mock(status_code=200, json=lambda: {'items': []})
    real_api._YT_CACHE.clear()
    with patch.object(real_api, 'get_yt_api_key', return_value='mock'), patch.object(real_api.requests, 'get', side_effect=get), patch.object(real_api, '_fetch_related_keywords', return_value=[]):
        result = real_api.fetch_youtube_data('demo', region='Global', timeframe=timeframe)
    params = next(params for url, params in captured if url == real_api.SEARCH_URL)
    cutoff = datetime.fromisoformat(params['publishedAfter'].replace('Z', '+00:00'))
    assert abs((now-cutoff).total_seconds()-days*86400) < 5
    assert 'regionCode' not in params
    assert result['daily_metrics'][0]['views'] == 300
    assert sum(point['views'] for point in result['time_series']) == 300
    assert any(point['views'] == 0 for point in result['time_series'])


def test_missing_comments_are_unavailable_not_neutral_or_positive():
    for comments in [[], ['😊😊']]:
        result = analyze_sentiment(comments)
        assert result['dominant_sentiment'] == 'unavailable'
        assert result['positive_score'] == result['neutral_score'] == 0


def test_generic_feed_has_no_unrelated_titles_and_specific_topic_is_fast():
    mod = get_flask_module()
    raw = {'status': 200, 'title': 'Test', 'comments': [], 'related_keywords': [],
           'daily_metrics': [{'date': '2026-10-11', 'views': 100, 'likes': 2, 'comments_count': 0, 'shares': 0}]}
    with patch.object(mod, 'fetch_youtube_data', return_value=raw), patch.object(mod, 'generate_context_aware_titles', side_effect=AssertionError('No AI dependency in main search')):
        client = mod.app.test_client()
        general = client.get('/api/trending-feed').json['results']['YouTube']
        assert general['seo_title_ideas'] == []
        topic = client.post('/api/search', json={'keyword': 'Minecraft'}).json['results']['YouTube']
        assert len(topic['seo_title_ideas']) == 4
        assert all('Minecraft' in title for title in topic['seo_title_ideas'])
        assert topic['youtube_tags'][0] == 'Minecraft'
        csv = client.get(f"/api/export-csv/{topic['trend_id']}")
        assert csv.status_code == 200
        assert 'Pending' in csv.text and 'BASELINE' in csv.text
        pdf = client.get(f"/api/report/{topic['trend_id']}")
        assert pdf.status_code == 200 and pdf.data.startswith(b'%PDF')


def test_pdf_keyword_is_literal_text_not_reportlab_markup():
    from services.report_generator import generate_pdf_report_buffer
    filename, content = generate_pdf_report_buffer(
        {'keyword': '<broken & topic>', 'platform': 'YouTube', 'total_views': 100},
        {'positive_score': 0, 'negative_score': 0, 'neutral_score': 0, 'dominant_sentiment': 'unavailable'},
        None, 20, 'BASELINE', 'Anonymous User')
    assert content.read(4) == b'%PDF'
    assert '<' not in filename


def test_momentum_percentile_scoring_and_no_saturation():
    """Verify Task 1.1: relative percentile scoring across cohort and no +950 cap."""
    now = datetime.now(timezone.utc)
    def mock_get(url, **kwargs):
        if url == real_api.SEARCH_URL:
            return Mock(status_code=200, json=lambda: {'items': [{'id': {'videoId': f'vid-{i}'}} for i in range(4)]})
        if url == real_api.VIDEOS_URL:
            # vid-0: 100k views in 1 hour (extreme velocity)
            # vid-1: 10k views in 2 hours (5k/hr)
            # vid-2: 2k views in 2 hours (1k/hr)
            # vid-3: 100 views in 10 hours (10/hr)
            items = [
                {'id': 'vid-0', 'snippet': {'title': 'Viral', 'publishedAt': (now - timedelta(hours=1)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '100000', 'likeCount': '5000', 'commentCount': '500'}},
                {'id': 'vid-1', 'snippet': {'title': 'Fast', 'publishedAt': (now - timedelta(hours=2)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '10000', 'likeCount': '500', 'commentCount': '50'}},
                {'id': 'vid-2', 'snippet': {'title': 'Medium', 'publishedAt': (now - timedelta(hours=2)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '2000', 'likeCount': '100', 'commentCount': '10'}},
                {'id': 'vid-3', 'snippet': {'title': 'Slow', 'publishedAt': (now - timedelta(hours=10)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '100', 'likeCount': '5', 'commentCount': '1'}},
            ]
            return Mock(status_code=200, json=lambda: {'items': items})
        return Mock(status_code=200, json=lambda: {'items': []})

    real_api._YT_CACHE.clear()
    with patch.object(real_api, 'get_yt_api_key', return_value='mock'), \
         patch.object(real_api.requests, 'get', side_effect=mock_get), \
         patch.object(real_api, '_fetch_related_keywords', return_value=[]):
        res = real_api.fetch_youtube_data('viral-test', region='Global', timeframe='24h')

    assert res['status'] == 200
    videos = res['top_videos']
    assert len(videos) == 4
    # The top video with 100k views/hr should be rank 1 and have high percentile
    top_v = videos[0]
    assert top_v['id'] == 'vid-0'
    assert top_v['estimated_views_per_hour'] == 100000.0
    assert top_v['momentumScore'] == 88  # (3 + 0.5)/4 * 100 = 87.5 -> 88
    assert top_v['momentum_percentile'] == 87.5
    assert top_v['momentumScore'] != 950  # Saturation cap removed!
    assert top_v['trendScore'] > 1000  # Not artificially suppressed by cap


def test_hidden_likes_treated_as_unavailable_not_zero():
    """Verify Task 1.2: missing likeCount is represented as None/unavailable, not 0."""
    now = datetime.now(timezone.utc)
    def mock_get(url, **kwargs):
        if url == real_api.SEARCH_URL:
            return Mock(status_code=200, json=lambda: {'items': [{'id': {'videoId': 'vid-hidden'}}, {'id': {'videoId': 'vid-normal'}}]})
        if url == real_api.VIDEOS_URL:
            items = [
                # vid-hidden has likes disabled / missing from statistics
                {'id': 'vid-hidden', 'snippet': {'title': 'Hidden Likes', 'publishedAt': (now - timedelta(hours=2)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '1000', 'commentCount': '50'}},
                # vid-normal has normal likes
                {'id': 'vid-normal', 'snippet': {'title': 'Normal Likes', 'publishedAt': (now - timedelta(hours=2)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '1000', 'likeCount': '200', 'commentCount': '50'}},
            ]
            return Mock(status_code=200, json=lambda: {'items': items})
        return Mock(status_code=200, json=lambda: {'items': []})

    real_api._YT_CACHE.clear()
    with patch.object(real_api, 'get_yt_api_key', return_value='mock'), \
         patch.object(real_api.requests, 'get', side_effect=mock_get), \
         patch.object(real_api, '_fetch_related_keywords', return_value=[]):
        res = real_api.fetch_youtube_data('hidden-test', region='Global', timeframe='24h')

    assert res['status'] == 200
    videos = {v['id']: v for v in res['top_videos']}
    hidden_v = videos['vid-hidden']
    normal_v = videos['vid-normal']

    assert hidden_v['likes'] is None
    assert hidden_v['likes_available'] is False
    assert hidden_v['engagement'] is None

    assert normal_v['likes'] == 200
    assert normal_v['likes_available'] is True
    assert normal_v['engagement'] == 25.0  # (200 + 50) / 1000 * 100

    # Cohort avgEngagement must only average videos with available likes
    assert res['kpis']['avgEngagement'] == 25.0
    assert res['kpis']['totalLikes'] == 200


def test_regional_trending_uses_most_popular_and_defaults_to_pk():
    """Verify Task 1.3: default trending uses videos.list?chart=mostPopular with PK region."""
    now = datetime.now(timezone.utc)
    captured = []
    def mock_get(url, **kwargs):
        params = kwargs.get('params', {})
        captured.append((url, params))
        if url == real_api.VIDEOS_URL and params.get('chart') == 'mostPopular':
            items = [
                {'id': 'pop-1', 'snippet': {'title': 'PK Trend 1', 'publishedAt': (now - timedelta(hours=3)).isoformat(), 'categoryId': '20'},
                 'statistics': {'viewCount': '5000', 'likeCount': '200', 'commentCount': '50'}},
            ]
            return Mock(status_code=200, json=lambda: {'items': items})
        return Mock(status_code=200, json=lambda: {'items': []})

    real_api._YT_CACHE.clear()
    with patch.object(real_api, 'get_yt_api_key', return_value='mock'), \
         patch.object(real_api.requests, 'get', side_effect=mock_get), \
         patch.object(real_api, '_fetch_related_keywords', return_value=[]):
        # Default trending call (no keyword)
        res = real_api.fetch_youtube_data('')

    assert res['status'] == 200
    assert len(res['top_videos']) == 1
    assert res['top_videos'][0]['id'] == 'pop-1'

    # Check captured params for mostPopular call
    pop_call = next(params for url, params in captured if url == real_api.VIDEOS_URL and params.get('chart') == 'mostPopular')
    assert pop_call['chart'] == 'mostPopular'
    assert pop_call['regionCode'] == 'PK'
