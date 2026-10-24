"""Offline checks for deterministic driver selection and lossless URL handling."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from backend.app.core.config import normalize_database_url, Settings


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg2"])
def test_postgres_normalization_preserves_encoded_url_and_components(scheme):
    suffix = "example_user:example%40p%3Ass%2F%25@db.example.invalid:6543/example_db?sslmode=verify-full&application_name=plexudo%20test"
    original = f"{scheme}://{suffix}"
    normalized = normalize_database_url(original)
    assert normalized == "postgresql+psycopg2://" + suffix
    before, after = make_url(original), make_url(normalized)
    for name in ("username", "password", "host", "port", "database", "query"):
        assert getattr(before, name) == getattr(after, name)


@pytest.mark.parametrize("url", ["", "sqlite:///:memory:", "sqlite:///local.db"])
def test_normalization_preserves_non_postgres_urls(url):
    assert normalize_database_url(url) == url


def test_settings_selects_installed_psycopg2_driver_without_connection(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://example:example@db.example.invalid:6543/example")
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    try:
        assert engine.dialect.driver == "psycopg2"
        assert engine.dialect.loaded_dbapi.__name__ == "psycopg2"
    finally:
        engine.dispose()
