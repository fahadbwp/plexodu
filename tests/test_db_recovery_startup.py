"""Simulate fresh Vercel/production processes with every database operation trapped."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("flask_env,vercel,configured", [
    ("production", "", True),
    ("development", "1", True),
    ("production", "1", True),
    ("production", "1", False),
])
def test_cold_start_and_first_request_do_not_connect_migrate_or_seed(tmp_path, flask_env, vercel, configured):
    env = os.environ.copy()
    env.update({
        "FLASK_ENV": flask_env, "VERCEL": vercel,
        "DATABASE_URL": "postgres://example:example@db.example.invalid:6543/example?sslmode=verify-full" if configured else "",
        "SECRET_KEY": "ci-test-secret-key-minimum-32-characters-long",
        "GROQ_API_KEY": "mock-groq-key-for-ci", "YOUTUBE_API_KEY": "mock-youtube-key-for-ci",
        "DATA_DIR": str(tmp_path),
    })
    script = r'''
import sys
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
sys.path.insert(0, str(Path('backend').resolve()))

with ExitStack() as stack:
    traps = []
    for target in (
        'psycopg2.connect', 'sqlite3.connect',
        'flask_sqlalchemy.SQLAlchemy.create_all', 'flask_sqlalchemy.SQLAlchemy.drop_all',
        'sqlalchemy.engine.Connection.execute', 'sqlalchemy.orm.Session.commit',
        'migrate_db.run_migration', 'requests.get', 'requests.post',
    ):
        traps.append(stack.enter_context(patch(target, side_effect=AssertionError('Unexpected I/O'))))
    import api.index
    mod = api.index.flask_module
    # Also protect against callers directly invoking the bootstrap helper.
    mod.create_tables()
    assert mod.app.test_client().get('/').status_code == 200
    with mod.app.app_context():
        engine = mod.db.engine
        if mod.settings.DATABASE_URL:
            from sqlalchemy.pool import NullPool
            assert isinstance(engine.pool, NullPool)
            assert engine.dialect.driver == 'psycopg2'
            options = mod.app.config['SQLALCHEMY_ENGINE_OPTIONS']
            assert options['connect_args'] == {'connect_timeout': 5, 'sslmode': 'verify-full'}
        else:
            assert mod.app.test_client().get('/api/health').json['db'] == 'error'
        engine.dispose()
    assert all(trap.call_count == 0 for trap in traps)
print('Cold start, first request and bootstrap helper: no database or external I/O')
'''
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=40,
    )
    # Do not echo child diagnostics or connection configuration on failure.
    assert result.returncode == 0, "Isolated startup safety check failed"
    assert "no database or external I/O" in result.stdout
