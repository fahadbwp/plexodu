"""Compile model metadata to PostgreSQL SQL offline; never execute statements."""
import argparse
from pathlib import Path
import sys

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.models import db

OUTPUT = Path(__file__).with_name("schema_postgres.sql")
HEADER = """-- Generated offline from backend/models.py; do not edit by hand.
-- Regenerate: python database/generate_postgres_schema.py
-- Verify: python database/generate_postgres_schema.py --check
-- Proposal for an EMPTY application schema only; execution requires authorization.
-- Plain CREATE statements intentionally fail if objects already exist.
-- Client-side Python defaults are not SQL server defaults.
-- Existing databases require a separately reviewed migration, not this file.
"""


def render_schema():
    dialect = postgresql.dialect()
    statements = []
    for table in db.metadata.sorted_tables:
        statements.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        for index in sorted(table.indexes, key=lambda item: item.name):
            statements.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
    sql = HEADER + "\n" + "\n\n".join(statements) + "\n"
    return "\n".join(line.rstrip() for line in sql.splitlines()) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check parity without writing")
    args = parser.parse_args()
    rendered = render_schema()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("PostgreSQL schema is missing or differs from current model metadata")
            return 1
        print("PostgreSQL schema matches current model metadata (offline check)")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print("Generated PostgreSQL schema proposal; no database connection or SQL execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
