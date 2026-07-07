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

## W1.1 Migration findings
- pg_ref renamed from tripay_ref (D8 generic for future PG swap)
- check_user_access reason='ok' lowercase (matches MCP expectation)
- record_action returns (ok, remaining) tuple per spec
- Action enum boundary: MCP chat_nsfw|img_nsfw|video → SQL msg|img|video
- All IF NOT EXISTS + OR REPLACE for idempotency (A12)
- No tier_expires read in check_user_access (A10 timer handles expiry)
