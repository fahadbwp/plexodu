# Technical debt deferred beyond Phase 0

These are recorded for later phases; Phase 0 does not change these behaviors.

- `real_api.py` caps momentum at +950.
- The default timeframe uses `search.list` rather than `mostPopular`; regionCode biases results rather than guaranteeing locality.
- A hidden likeCount is treated as zero.
- `nlp_engine._clean_text` removes non-ASCII characters, so Urdu/Hindi/emoji comments can become unclassified.
- Cache and rate-limiter state live in memory per serverless instance. Review remote_addr/proxy trust and distributed enforcement.
- No scheduled snapshots exist yet.
- Searches commit Trend/Metric/Sentiment rows without a retention policy.
- PDF exports are written to temporary storage (`/tmp` on Vercel).
- Preserve the legacy User table/model, all columns, relationships and production data: Trend.created_by, Report.generated_by and AuditLog.user_id reference users.id.
- Legacy roles, VALID_ROLES, validate_user_role and auth limiter helpers remain covered by existing security tests. AUTH_RATE_LIMIT_PER_MIN is still read.
- `vercel.json` uses the legacy builds/routes style.
- The legacy email service remains because a dedicated source-existence security test is outside the narrowly authorized test-import deletion allowance. Remove it in a separately approved cleanup with both dedicated tests reviewed.
- Root public asset copies remain conservatively because public root URL references exist, even though Vercel explicitly serves frontend copies. No asset was deleted on an assumed mapping.
- Bandit medium findings remain report-only: B108 for DATA_DIR /tmp default and B104 for the local development server binding. Neither is suppressed; high findings block CI.
- Database recovery now prevents production/Vercel bootstrap DDL and uses bounded encrypted NullPool connections. Actual production schema initialization, least-privilege roles, pooler/TLS verification and post-initialization health checks still require separately authorized work. Legacy explicit migration scripts remain potentially destructive and must not be used as an initialization shortcut.
- Analytics activation needs a real measurement ID, an applicable-consent review and a consent UI/integration. The committed placeholder causes no analytics requests; GA4 is disabled.
