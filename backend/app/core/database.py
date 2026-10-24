"""Connection configuration only: no connections, DDL or credential logging."""
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool


def postgres_ssl_args(url):
    """Require encryption in production; never downgrade certificate validation."""
    mode = make_url(url).query.get("sslmode")
    return {"sslmode": mode if mode in ("require", "verify-ca", "verify-full") else "require"}


def database_engine_options(database_uri: str, production: bool) -> dict:
    if make_url(database_uri).get_backend_name() != "postgresql":
        return {"pool_pre_ping": True}
    if production:
        return {
            "poolclass": NullPool,
            "connect_args": {"connect_timeout": 5, **postgres_ssl_args(database_uri)},
        }
    # Retain the existing local PostgreSQL QueuePool behavior.
    return {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
