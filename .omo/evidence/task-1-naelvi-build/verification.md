# W1.1 — Supabase SQL Migration — Evidence

**Date**: 2026-07-07
**VPS**: root@172.232.232.65 (naelvi-linode, Ubuntu 6.8.0-124)
**Supabase**: Docker Postgres 15.8, container `supabase-db`

## File
- `supabase/migration.sql` (287 LOC, 11606 bytes)
- Commit: `7f7cff8` (local repo)
- Applied via: `docker cp + docker exec supabase-db psql -U postgres -f /tmp/migration.sql`

## Apply output
```
CREATE TABLE  ×5  (users, usage, credits, payments, video_jobs)
CREATE INDEX  ×5  (idx_users_tier, idx_usage_period, idx_payments_status,
                   idx_payments_telegram, idx_video_jobs_telegram)
CREATE FUNCTION ×3  (get_or_create_usage, check_user_access, record_action)
```

## Tables verified
```
public | users
public | usage
public | credits
public | payments
public | video_jobs
```

## Indexes verified
```
idx_users_tier          → users
idx_usage_period        → usage
idx_payments_status     → payments
idx_payments_telegram   → payments
idx_video_jobs_telegram → video_jobs
payments_pg_ref_key     → payments (UNIQUE constraint on pg_ref)
```

## Functions verified
```
public | check_user_access   (p_telegram_id bigint, p_action text) → TABLE(allowed boolean, reason text, remaining integer)
public | get_or_create_usage (p_telegram_id bigint) → usage
public | record_action       (p_telegram_id bigint, p_action text) → TABLE(ok boolean, remaining integer)
```

## AC results (live psql)

### AC(1): Tables/functions/indexes exist
✅ 5 tables, 3 functions, 5 custom indexes + 1 unique constraint (payments.pg_ref)

### AC(2): check_user_access(999999999, 'msg') — auto-create user, SFW chat allowed
```
 allowed | reason | remaining 
---------+--------+-----------
 t       | ok     |        30
```

### AC(3): User auto-created with tier='free'
```
 telegram_id | tier 
-------------+------
   999999999 | free
```

### AC(4): record_action('msg') — decrements remaining
```
 ok | remaining 
----+-----------
 t  |        29
```

### AC(5): Free user NSFW image denied
```
 allowed |                reason                 | remaining 
---------+---------------------------------------+-----------
 f       | NSFW image requires PRO subscription. |         0
```

### AC(6): Free user video denied
```
 allowed |                    reason                     | remaining 
---------+-----------------------------------------------+-----------
 f       | Video generation requires ULTRA subscription. |         0
```

### Idempotency
Migration uses `CREATE TABLE IF NOT EXISTS` + `CREATE OR REPLACE FUNCTION` — re-run produces no errors.

### pg_ref generic column (D8)
`payments.pg_ref TEXT UNIQUE` — no `tripay_ref` column exists. Future PG swap = no migration needed.

## Must-NOT guardrails verified
- ✅ SQL uses `pg_ref` (not `tripay_ref`)
- ✅ `IF NOT EXISTS` on all tables
- ✅ `CREATE OR REPLACE` on all functions
- ✅ Credit-first deduction logic in `check_user_access` (img: credit → monthly; video: credit + monthly combined)
- ✅ No hardcoded secrets in SQL
- ✅ Applied via local Docker network only (127.0.0.1:5432 via docker exec)

## Cleanup
Test user 999999999 + associated usage/credits deleted after verification.
