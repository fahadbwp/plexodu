"""Pool selection is an environment decision, never proof inferred from a port."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from backend.app.core.database import database_engine_options


@pytest.mark.parametrize("port", [5432, 6543])
def test_production_postgres_uses_nullpool_and_bounded_encrypted_connections(port):
    uri = f"postgresql+psycopg2://example:example@db.example.invalid:{port}/example"
    options = database_engine_options(uri, production=True)
    assert options["poolclass"] is NullPool
    assert options["connect_args"] == {"connect_timeout": 5, "sslmode": "require"}
    assert not {"pool_size", "max_overflow", "pool_timeout", "pool_recycle"} & options.keys()
    engine = create_engine(uri, **options)
    try:
        assert isinstance(engine.pool, NullPool)
    finally:
        engine.dispose()


@pytest.mark.parametrize("mode,expected", [
    ("disable", "require"), ("prefer", "require"), ("allow", "require"),
    ("require", "require"), ("verify-ca", "verify-ca"), ("verify-full", "verify-full"),
])
def test_production_ssl_minimum_and_stronger_certificate_validation(mode, expected):
    uri = "postgresql+psycopg2://example:example@db.example.invalid/example?sslmode=" + mode
    assert database_engine_options(uri, True)["connect_args"]["sslmode"] == expected


def test_local_port_does_not_select_production_strategy():
    uri = "postgresql+psycopg2://example:example@localhost:6543/example"
    assert database_engine_options(uri, False) == {
        "pool_size": 10, "max_overflow": 20, "pool_timeout": 30,
        "pool_recycle": 1800, "pool_pre_ping": True,
    }


def test_local_sqlite_configuration_is_unchanged():
    assert database_engine_options("sqlite:///:memory:", False) == {"pool_pre_ping": True}
