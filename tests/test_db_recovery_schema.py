"""Prevent drift between the offline SQL proposal, current models and migration fields."""
import ast
from pathlib import Path
from unittest.mock import patch

from database.generate_postgres_schema import OUTPUT, render_schema
from backend.models import db


ROOT = Path(__file__).resolve().parents[1]


def test_postgres_artifact_matches_all_current_model_definitions():
    assert OUTPUT.read_text(encoding="utf-8") == render_schema()
    assert set(db.metadata.tables) == {"users", "trends", "metrics", "sentiment", "reports", "audit_logs"}


def test_schema_preserves_timezone_defaults_constraints_and_delete_semantics():
    sql = OUTPUT.read_text(encoding="utf-8")
    assert sql.count("CREATE TABLE ") == 6
    assert sql.count("TIMESTAMP WITHOUT TIME ZONE") == 8
    assert "TIMESTAMP WITH TIME ZONE" not in sql
    assert "ON DELETE" not in sql
    assert "DEFAULT" not in sql
    assert sql.count("SERIAL NOT NULL") == 6
    assert sql.count("PRIMARY KEY") == 6
    assert sql.count("FOREIGN KEY") == 6
    assert "UNIQUE (email)" in sql
    assert "CREATE INDEX ix_trends_observation_key ON trends (observation_key)" in sql
    assert "IF NOT EXISTS" not in sql


def test_all_existing_migration_additions_are_in_current_metadata():
    tree = ast.parse((ROOT / "backend/migrate_db.py").read_text(encoding="utf-8"))
    additions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("TRENDS_NEW_COLUMNS", "METRICS_NEW_COLUMNS"):
                    additions[target.id] = ast.literal_eval(node.value)
    assert set(additions) == {"TRENDS_NEW_COLUMNS", "METRICS_NEW_COLUMNS"}
    for variable, table in [("TRENDS_NEW_COLUMNS", "trends"), ("METRICS_NEW_COLUMNS", "metrics")]:
        assert {name for name, _ in additions[variable]} <= set(db.metadata.tables[table].columns.keys())


def test_rendering_never_connects_or_executes_sql():
    with patch("psycopg2.connect", side_effect=AssertionError("Unexpected connection")) as connection, \
         patch("sqlalchemy.engine.Connection.execute", side_effect=AssertionError("Unexpected SQL")) as execute:
        assert render_schema() == OUTPUT.read_text(encoding="utf-8")
    connection.assert_not_called()
    execute.assert_not_called()
