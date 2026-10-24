"""Health monitoring must be bounded, anonymous and safe to disclose."""
import importlib
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch


def module():
    if "main_flask_app" not in sys.modules:
        importlib.import_module("api.index")
    return sys.modules["main_flask_app"]


def test_health_local_fallback_is_healthy_and_does_not_use_upstream_quotas(monkeypatch):
    mod = module()
    monkeypatch.setattr(mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(mod.settings, "DATABASE_URL", "")
    with patch.object(mod.rate_limiter, "is_allowed", side_effect=AssertionError("quota used")):
        response = mod.app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert set(response.json) == {"status", "db", "version", "time"}
    assert response.json["status"] == response.json["db"] == "ok"
    assert datetime.fromisoformat(response.json["time"]).utcoffset().total_seconds() == 0


def test_health_database_failure_never_discloses_secrets(monkeypatch):
    mod = module()
    values = ["health-secret-key-unique", "health-youtube-key-unique", "health-groq-key-unique",
              "postgresql://fake:fake@invalid.example/health"]
    for name, value in zip(["SECRET_KEY", "YOUTUBE_API_KEY", "GROQ_API_KEY", "DATABASE_URL"], values):
        monkeypatch.setenv(name, value)
    with patch.object(mod, "create_engine", side_effect=RuntimeError(" ".join(values))):
        response = mod.app.test_client().get("/api/health")
    assert response.status_code == 200
    assert response.json["db"] == "error"
    assert response.json["status"] == "degraded"
    assert all(value not in response.get_data(as_text=True) for value in values)


def test_health_unconfigured_production_does_not_probe_local_database(monkeypatch):
    mod = module()
    monkeypatch.setattr(mod, "IS_PRODUCTION", True)
    monkeypatch.setattr(mod.settings, "DATABASE_URL", "")
    with patch.object(mod, "create_engine") as factory:
        response = mod.app.test_client().get("/api/health")
    factory.assert_not_called()
    assert response.json["status"] == "degraded"
    assert response.json["db"] == "error"


def test_health_postgres_uses_driver_connection_and_statement_timeouts(monkeypatch):
    mod = module()
    fake_db = MagicMock()
    fake_db.engine.url.get_backend_name.return_value = "postgresql"
    engine = MagicMock()
    monkeypatch.setattr(mod, "db", fake_db)
    monkeypatch.setattr(mod, "IS_PRODUCTION", False)
    with patch.object(mod, "create_engine", return_value=engine) as factory:
        assert mod._health_database_status() == "ok"
    assert factory.call_args.kwargs["connect_args"] == {
        "connect_timeout": 2, "options": "-c statement_timeout=2000"}
    engine.dispose.assert_called_once()


def test_health_version_uses_short_commit_or_dev(monkeypatch):
    mod = module()
    with patch.object(mod, "_health_database_status", return_value="ok"):
        monkeypatch.delenv("VERCEL_GIT_COMMIT_SHA", raising=False)
        assert mod.app.test_client().get("/api/health").json["version"] == "dev"
        monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "abcdef0123456789")
        assert mod.app.test_client().get("/api/health").json["version"] == "abcdef0"
