# Environment configuration

Set production and preview secrets in the matching Vercel project environment, local values in an ignored `.env`, and only mock values in GitHub test jobs. Never commit real credentials. Run `python backend/verify_env.py` to print presence only; MISSING can be expected for optional variables. It performs no API requests.

| Variable | Required? | Where to set | Fake format example |
| --- | --- | --- | --- |
| SECRET_KEY | Stable production value required | Vercel/local; GitHub tests use mock | `replace-with-a-generated-long-random-secret` |
| DATABASE_URL | PostgreSQL required in production; optional locally | Vercel/local; GitHub tests empty | `postgresql://example_user:example_password@db.example.invalid:6543/plexudo` |
| YOUTUBE_API_KEY | For live YouTube tools | Vercel/local; GitHub mock | `mock-youtube-key-for-ci` |
| GROQ_API_KEY | For Groq AI features | Vercel/local; GitHub mock | `mock-groq-key-for-ci` |
| GROQ_MODEL | Optional, defaults to llama-3.3-70b-versatile | Vercel/local/GitHub | `llama-3.3-70b-versatile` |
| CORS_ALLOWED_ORIGINS | Explicit production list recommended | Vercel/local/GitHub | `https://example.invalid,http://localhost:5000` |
| API_RATE_LIMIT_PER_MIN | Optional, default 100 | Vercel/local | `100` |
| AI_RATE_LIMIT_PER_MIN | Optional, default 30 | Vercel/local | `30` |
| DATA_DIR | Optional writable runtime directory | Vercel/local | `/tmp` |
| CRON_SECRET | Needed from Phase 2; not currently consumed | Vercel/local, future GitHub if needed | `replace-with-a-generated-cron-secret` |
| FLASK_ENV | Set explicitly for production/development | Vercel/local/GitHub | `development` |
| PORT | Optional local server port | local | `5000` |
| HOST | Legacy configuration setting; runner currently binds all interfaces | local | `127.0.0.1` |
| FLASK_DEBUG | Optional; keep disabled in production | local | `false` |
| AUTH_RATE_LIMIT_PER_MIN | Legacy setting still read, default 10 | Vercel/local if needed | `10` |

For Supabase on Vercel, use the pooled PostgreSQL connection string from your Supabase dashboard, with its documented user, port and SSL settings. Do not use SQLite for production persistence: Vercel filesystem data is ephemeral. Keep DATABASE_URL empty for the existing local SQLite fallback and mocked CI tests.

Health monitoring: `GET /api/health` returns HTTP 200 and status `ok` or `degraded`, database `ok` or `error`, a short deployment commit (or `dev`) and UTC timestamp. Monitor the body as well as HTTP status. A missing production DATABASE_URL is degraded; an unconfigured local database probes the SQLite fallback. The probe opens an independent connection with a two-second driver timeout (and a two-second PostgreSQL statement timeout), returns no errors or connection details, and consumes no YouTube/Groq quota. PostgreSQL connectivity is mocked in local tests; no live production database was accessed.

Startup still initializes the existing database before serving requests. Health monitoring does not change that pre-existing bootstrap behavior. DATA_DIR is for existing temporary exports and local storage; it is not durable production database storage.

SMTP/EMAIL settings are excluded from the public deployment template. The retained legacy email module still reads them if explicitly imported; the application does not import it. No OAuth variables are required for the anonymous product.

Analytics remains disabled: `frontend/js/analytics.js` contains only a placeholder. No deployment variable is interpolated into static JavaScript. Before activation, review applicable consent requirements and add a consent mechanism that sets `window.plexudoAnalyticsConsent = true` and dispatches `plexudo:analytics-consent` only after opt-in. Also replace the placeholder measurement ID. Global Privacy Control and Do Not Track disable loading. No consent UI or live measurement ID was introduced in Phase 0.
