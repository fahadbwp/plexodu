# Phase 1 database integration recovery

## Recommendation

**Local recovery implementation and schema-parity verification: PASS. Production initialization/deployment: NO-GO pending the separately authorized checks and procedure below.** No production database was connected to, no SQL was executed against PostgreSQL, no secrets/environment settings were retrieved or changed, and nothing was pushed, merged or deployed. Phase 1 analytics tasks 1.1-1.9 remain stopped.

## Verified identity

- Git root: `C:\Users\Fahad Saleem\Documents\plexodu-main\plexodu-phase0`.
- Branch: `fix/phase1-data-accuracy`.
- Verified starting HEAD: `5725081df3fde13731d65d5db4b1492f2da1998c` (Phase 0 squash).
- Starting tracked working tree clean; an existing generated pytest-cache directory produces a Windows permission warning. It was not deleted or incorporated into commits.
- All repository commands ran from that Git root. The parent snapshot was not imported, copied wholesale, edited or used as the dependency/model source of truth.

## Tasks and commits

| Task | Result | Commit | Evidence |
| --- | --- | --- | --- |
| DB-1 driver | done | 9e84306 | Lossless prefix normalization and seven offline tests; 243 full-suite passes. |
| DB-2 pooling | done | 9c5e9b9 | Production NullPool, short driver timeout, SSL minimum; ten new tests; 253 passes. |
| DB-3 startup | done | ee7d769 | Four isolated cold-start tests; 257 passes; DDL/DBAPI/commit/API traps never called. |
| DB-4 schema | done | 6addab1 | Metadata-generated proposal and four parity/safety tests; 261 passes. |
| DB-5 security | done with documented dev advisory | verification only | Runtime audit clean; pytest dev advisory retained for separately tested upgrade. |
| DB-6 review | done | verification only | Baseline IDs preserved; no original test/frontend/model/CI/requirements changes or Gemini restoration. |
| DB-7 report | done | documentation commit containing this report | Final documentation commit SHA is reported in the final response, avoiding a self-referential hash. |

## Exact changes and rationale

1. `backend/app/core/config.py`: normalize postgres and postgresql scheme prefixes to explicit postgresql+psycopg2. Everything after the scheme is preserved verbatim, including encoded passwords, host/port/database and query parameters. Explicit psycopg2 and SQLite URLs are unchanged. Existing SQLite aiosqlite normalization remains. No connection URL is logged.
2. `backend/app/core/database.py`: pure engine-options helper. Production is determined by existing project settings/VERCEL environment, not a URL port. PostgreSQL production uses NullPool with connect_timeout=5 and minimum sslmode=require, preserving verify-ca/verify-full. No incompatible QueuePool settings are passed to NullPool. Local PostgreSQL retains its previous pool options; SQLite retains pre-ping. No runtime dependency was added.
3. `backend/app.py`: use the helper for engine options; retain independent health-probe disposal and its shorter timeouts, adding the production SSL minimum. The bootstrap helper immediately returns in production or Vercel, before create_all, migration, reset or seeding logic. Local behavior is preserved. SQLAlchemy/Flask teardown continues managing per-request sessions; NullPool releases underlying connections rather than retaining an application pool.
4. `database/generate_postgres_schema.py` and `database/schema_postgres.sql`: offline compile-only generator and its SQL proposal. The generator imports current models, never the Flask app, and never creates an engine or executes SQL. `--check` fails on drift without modifying files. Plain CREATE statements intentionally fail on existing objects instead of silently pretending to migrate them.
5. Four new test files cover URL/driver behavior, pool/SSL policy, real fresh-process startup and SQL artifact parity.
6. `docs/ENVIRONMENT.md` and `docs/TECH_DEBT.md`: update only database-readiness behavior and remaining operational work. This report records the final evidence and approval boundary.

## Driver and connection verification

Installed runtime versions: CPython 3.12.15, SQLAlchemy 2.1.6, Flask-SQLAlchemy 3.1.1, psycopg2-binary 2.9.10. These match the current branch environment; requirements were not changed. Plain PostgreSQL URLs would otherwise select a psycopg driver absent from that environment. Tests construct and dispose engines without opening database connections and verify the actual dialect selects psycopg2.

The actual application engine is inspected in isolated production/Vercel imports: NullPool, psycopg2, five-second driver timeout, preserved verify-full configuration. Port 6543 alone does not switch a local application into production. Pooler selection is configuration, not proof that a host is Supabase or trusted.

The five-second connect timeout is not a general query timeout or guarantee for all DNS/network failure durations. Health retains its separate two-second connection timeout and two-second PostgreSQL statement timeout. Real transaction-pooler/TLS compatibility, including health timeout behavior, must still be checked with authorized access. SSL require encrypts the connection; certificate identity verification requires appropriately configured verify-full and trust material.

No database operations occur in tested production/Vercel import and first-request paths. Traps cover psycopg2.connect, sqlite3.connect, create_all, drop_all, Connection.execute, Session.commit, migration entry point and outbound requests. The bootstrap helper is called directly under the same traps. A production import with empty DATABASE_URL also succeeds, while health remains honestly degraded. That preserves Phase 0 import behavior; an empty production database configuration is not considered usable production readiness.

Legacy migration entry points remain available for explicit, separately reviewed operations; they are not called on production startup. Do not invoke them as a production setup shortcut: they can drop legacy tables/columns.

## Schema parity

The proposal is generated from the current branch's unchanged SQLAlchemy metadata. It includes all six application tables and every mapped column. It also covers every column added by the current Python migration's trends/metrics additions. No copied legacy SQL was used.

| Table | Columns | Primary key | Foreign keys | Unique/index notes |
| --- | ---: | --- | --- | --- |
| users | 6 | id | none | UNIQUE email |
| audit_logs | 6 | id | user_id -> users.id | none |
| trends | 18 | trend_id | created_by -> users.id | ix_trends_observation_key |
| metrics | 10 | id | trend_id -> trends.trend_id | none |
| reports | 6 | report_id | generated_by -> users.id, trend_id -> trends.trend_id | none |
| sentiment | 7 | id | trend_id -> trends.trend_id | none |

Parity details:

- Integer primary keys compile to SERIAL with PostgreSQL sequence-backed defaults, just as current SQLAlchemy metadata does.
- All types, string widths, nullability, PK/FK targets and users.email uniqueness match the current metadata.
- All eight DateTime columns compile to TIMESTAMP WITHOUT TIME ZONE. No timezone-aware type change was introduced.
- All six foreign keys retain default NO ACTION behavior; there are no new CASCADE or SET NULL actions.
- Python client-side defaults remain client-side. No SQL server defaults were invented for counters, roles, dates or timestamps; SERIAL sequence behavior is the ORM's own PostgreSQL autoincrement compilation. Direct SQL inserts must provide values that the ORM normally supplies.
- The only explicitly modeled secondary index is ix_trends_observation_key, nonunique, and that name/definition is preserved. PostgreSQL also creates PK/unique enforcement indexes. Extra indexes from the stale proposal were not copied.
- No new migration or model change was introduced. This artifact is for empty-schema initialization only, not an existing-database upgrade.
- Existing schema.sql contains MySQL-oriented syntax and is not the PostgreSQL procedure. migration_phase2.sql and migrate_db.py have destructive legacy cleanup behavior; neither should be executed automatically.
- Python migration upgrade paths have some server defaults not present in model-created fresh tables. The proposal intentionally follows current model creation semantics, rather than silently changing metadata to match one historical upgrade path. Existing databases need explicit introspection and a separately reviewed migration plan.

The artifact matches metadata byte-for-byte after generation; --check also passed in fresh processes with PYTHONHASHSEED=1 and 42. This proves offline model parity, not execution validity against an inspected production database. A disposable non-production PostgreSQL validation remains required before production initialization.

## Tests and count reconciliation

- All **236 baseline node IDs remain collected**, with **zero missing**. Existing tests were not modified, skipped or deleted.
- **25 new cases:** seven driver cases, ten pool/SSL cases, four cold-start cases, four schema cases.
- Full command: `python -m pytest tests/ backend/test_seo_schema.py -q -p no:cacheprovider --basetemp=<fresh local review directory>`: **261 passed**, one pre-existing ReportLab deprecation warning.
- The tests/ directory contains 256 cases; backend/test_seo_schema.py adds five. CI still uses its existing tests/ command and automatically collects the new recovery files; no workflow gate was weakened or changed.
- Prior 229 report was from the stale parent snapshot: 226 old tests + three added database tests. It omitted the five schema tests and lacked five Phase 0 health tests. It is not the baseline used here.
- Initial new cold-start test runs hit Windows pytest temporary-directory ACL errors (no application assertion failed). They were rerun with explicitly scoped filesystem access and a fresh artifact-directory basetemp. No skip, assertion removal, test deletion, or permission-change to unrelated directories was used to hide the failure.

All test runs use FLASK_ENV=development, an empty DATABASE_URL, the Phase 0 mock SECRET_KEY/Groq/YouTube values, and local CORS origins. The production subprocesses use fake example.invalid hosts and connection traps, never real credentials. No live Google/Groq calls are required.

## Security and verification results

| Check | Result |
| --- | --- |
| Full Python + schema suite | 261 passed |
| Node trend rendering regression | Both groups passed |
| Node analytics hook regression | Passed |
| Ruff backend + generator, E9/F63/F7/F82 | Passed |
| Bandit high-severity, medium-confidence gate | Passed, zero high findings |
| Runtime requirements pip-audit | Passed, zero known vulnerabilities |
| Flask/Vercel entrypoint smoke | Local import passed; four trapped production/serverless cold starts passed |
| SQL generator --check | Passed, including two hash seeds |
| Existing baseline test IDs | 236 of 236 preserved |
| git diff --check | Passed |
| Existing CI/requirements/models/frontend/tooling | Unchanged |

Development-only advisory: installed pytest 8.4.2 reports PYSEC-2026-1845, with fix version 9.0.3. The scanner reports the same advisory twice; this is one unique advisory in one package. It is not a runtime requirement. As requested, no unrelated dependency upgrade or ignore was applied. Safe follow-up path: in a separate isolated environment, install a candidate fixed pytest version (at least 9.0.3), check Python/plugin compatibility and rerun all 261 tests/CI jobs before proposing a requirements-dev.txt change. That future upgrade is not claimed verified here. Gitleaks remains in unchanged CI; it was not executed locally.

Bandit retains the pre-existing four medium metrics (including low-confidence migration warnings); the high gate passes. No nosec comments, broad exclusions or advisory suppressions were added.

## Final scope review against 5725081

Only backend database/configuration code, offline schema files, four new recovery test files and database documentation changed. No original test file was changed or deleted; no dependency/workflow/model/frontend/analytics/service logic was changed. The removed Gemini service remains absent. Existing Phase 0 health and disabled analytics behavior remain covered. No secret values or real database URLs were introduced. The stale snapshot remains outside this work.

## Environment requirements

- Vercel sets its VERCEL marker; existing Settings treat that or FLASK_ENV=production as production. Do not use a port number as environment authentication.
- Configure a valid DATABASE_URL for the intended project/database, with properly encoded credentials. Common PostgreSQL schemes are normalized to the installed psycopg2 driver. Runtime should use the documented Supabase transaction pooler; initialization should use an explicitly authorized administrative/session/direct connection.
- Enforce the approved TLS mode. The application requires at least SSL encryption in production and preserves stronger verify-ca/verify-full settings. Supply valid certificate/trust settings when using verification.
- Configure a stable SECRET_KEY, intended CORS_ALLOWED_ORIGINS, and backend-only YOUTUBE_API_KEY/GROQ_API_KEY as needed for the corresponding tools. Keep credentials in Vercel/ignored local configuration, never Git or report text.
- DATA_DIR is temporary export/local storage, not durable production database storage. No new environment variable or secret was introduced.
- Runtime role should have only the approved DML/sequence privileges needed by the app; schema initialization must not rely on granting DDL privileges to every serverless invocation.

## Proposed production initialization procedure — NOT EXECUTED

1. Review this exact branch/commit and generated SQL. Confirm the target Supabase/Vercel project and approved environment without exposing credentials. Obtain separate explicit authorization before any production access or SQL execution.
2. With separately authorized read-only access, inspect existing application objects, migration state, roles, timezone/TLS settings and data. Take/verify a restorable backup where data exists. If any of the six application tables already exists, STOP: this plain-CREATE artifact is not an upgrade or reconciliation script.
3. First apply the reviewed proposal only to an approved disposable non-production PostgreSQL schema using a separate administrative connection. Compare columns/types/nullability, PK/FK/unique/index definitions and default semantics to generated metadata; test ORM writes, relationships, exports and transaction-pooler behavior there. No such PostgreSQL execution occurred during this recovery.
4. After separate explicit approval for production initialization and confirmation the target application schema is empty, execute the exact reviewed generated SQL as one controlled transaction using an appropriate administrative/session/direct connection. Roll back on any error; never substitute the legacy destructive migration scripts or run initialization from cold start.
5. Verify the resulting catalog and runtime-role privileges under separately approved access. Configure runtime credentials/TLS in Vercel. Any environment write or deployment still requires explicit authorization.
6. After an independently authorized deployment, verify /api/health returns db=ok and status=ok without cache, and complete approved end-to-end application checks. SELECT 1 health alone is not proof that application tables and privileges are complete.

## Remaining deployment blockers / authorization boundary

- Production database configuration, actual catalog/data, project/pooler identity, runtime role permissions and TLS behavior have not been inspected or verified.
- Proposed SQL has not been executed even in disposable PostgreSQL; only offline parity and SQLite/mocked regression checks have run.
- The dev-only pytest advisory remains documented for a separately tested upgrade.
- No new GitHub CI run or live production health result is claimed for these unpushed commits.

**NO-GO for production initialization/deployment now.** The local reconstruction is complete and reviewable; the remaining operational steps require separate authorization. Do not resume Phase 1 analytics tasks 1.1-1.9 without explicit user approval.
