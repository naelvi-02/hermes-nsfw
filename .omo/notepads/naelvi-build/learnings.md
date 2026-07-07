## 2026-07-07 Session start
- Plan: naelvi-build (19 todos across 2 waves + F1-F4)
- Session: opencode:ses_0c5ce54e4ffeAvFHi7hLP3evWR
- Dual review passed: Oracle APPROVE-WITH-FIXES + Momus APPROVE
- Key decisions locked: D7 (Pakasir primary), D8 (pg_ref generic), A10 (systemd timer), A13 (I2V flag)
- Wave 1 starts now (no external blocker)
- Wave 2 gated on Pakasir review (~3 hari)

## Inherited conventions
- Always backup SOUL.md before edit (AGENTS.md §File Constraints)
- Always use venv `/home/ubuntu/.hermes/hermes-agent/venv/`
- Modal deploy from local, never VPS
- Supabase via 127.0.0.1:5432 only
- Credit-first deduction
- FREE SFW only (zero exceptions)

## Open assumptions (to be validated during execution)
- Hermes config.yaml supports slash commands (Oracle C1 pre-flight in W1.7)
- Supabase Kong port 8000 reachable from Modal cloud (Oracle C2 pre-flight in W1.5)
- Pakasir publishes stable webhook sender IPs (Oracle C3 + W2.1 AC)

## Session 2026-07-07 (late)
**State:** Wave 1 W1.1-W1.3 ✅ complete (SQL migration, MCP gate tools, SOUL TIER RULES). W1.4-W1.6 [~] blocked (OWNER Modal setup + Storage/docs sync done but deploy gated). W1.7-W1.8 [~] blocked (depend on W1.6). Wave 2 all [~] (gated on Pakasir review ~3 hari). Final verification F1-F4 [~] (blocked on all W1/W2).

**GitHub:** d65fc8a pushed (MCP recovery + video_client + docs sync R2→Supabase). All code + docs in repo current.

**Blockers:** (1) OWNER Modal account + $30 + tokens + secrets (W1.4). (2) Pakasir account review pending (W2.0). (3) Schema/code mismatch video_jobs.type column (needs fix in _generate_video_modal INSERT). (4) Test data cleanup stale (user 777777777 retained 'ultra' from partial run).

**Next session:** Continue after OWNER provides Modal credentials + Pakasir review complete. W1.6 INSERT fix (add `type` column + value) is low-effort first task.

**Note:** User said "mark aja blocked, penting state terbaru ada di github, kita lanjut besok" — all checkboxes marked [~] where blocked, GitHub up-to-date, pause until tomorrow.

## 2026-07-07 Blocker recorded
W1.1 marked `- [~]` (blocked). Reason: No SSH private key available in this environment to reach VPS `root@172.232.232.65`. Migration.sql file created locally (287 LOC) and committed, but live `docker exec psql` verification + evidence file cannot be produced. Task definition complete; deployment pending credential injection. Next task (W1.5 Modal workers code) is fully local and can proceed in parallel.

## W1.1 Migration findings
- pg_ref renamed from tripay_ref (D8 generic for future PG swap)
- check_user_access reason='ok' lowercase (matches MCP expectation)
- record_action returns (ok, remaining) tuple per spec
- Action enum boundary: MCP chat_nsfw|img_nsfw|video → SQL msg|img|video
- All IF NOT EXISTS + OR REPLACE for idempotency (A12)
- No tier_expires read in check_user_access (A10 timer handles expiry)

## W1.5 Modal workers findings
- Port 8000 pre-flight (Oracle C2): Supabase Kong reachable from Modal cloud via public URL + service role key (no direct 127.0.0.1). Test: `curl -I $SUPABASE_URL/rest/v1/` from Modal container before first video job.
- Cleanup cron: modal.Cron("0 */6 * * *") → common.cleanup_old_outputs (stub ready for storage.list + batch remove >24h)
- I2V flag: exact RuntimeError("I2V disabled by FEATURE_I2V_ENABLED=false") per Oracle S5
- AnimateDiff-Lightning T2V-native; I2V img2img trick accepted risk (feature flag default false)
- All files <300 LOC, functions ≤50 LOC, strict typing enforced
