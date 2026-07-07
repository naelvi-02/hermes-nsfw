---
slug: naelvi-build
status: drafting
intent: clear
review_required: false
pending-action: write .omo/plans/naelvi-build.md
approach: 6-module build per docs/implementation_plan.md 8-step order, gated by Tripay registration + Modal setup decisions
---

# Draft: naelvi-build

## Components (topology ledger)
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
- C1 DB-MIGRATION     | Apply 5 tables + 3 functions to Supabase Postgres (127.0.0.1:5432 via docker exec)                       | active | docs/blueprint.md:163-421
- C2 MCP-TIER-TOOLS   | Add 5 new MCP tools (check_user_access, record_usage, get_user_status, create_payment_link, generate_video_modal) to mcp_server.py — NEVER modify existing 3 | active | docs/implementation_plan.md:87-120; SKILLSET.md
- C3 SOUL-PERSONA     | Inject TIER RULES section into SOUL.md (BACKUP FIRST to /root/hermes-rp-backups/)                                | active | docs/implementation_plan.md:123-149
- C4 TRIPAY-BILLING   | tripay_client.py + webhook.py (FastAPI :8088, HMAC verify) + products.py — BLOCKED on Tripay registration | active | docs/implementation_plan.md:153-184; docs/blueprint.md §6,§11.3
- C5 BOT-COMMANDS     | /status /upgrade /topup /help in Hermes Telegram config                                                          | active | docs/implementation_plan.md:188-196
- C6 VIDEO-MODAL      | Modal workers worker_t2v.py / worker_i2v.py + common.py (R2 upload) + video_client.py in MCP — BLOCKED on Modal account + R2 bucket | active | docs/implementation_plan.md:199-216

## Open assumptions (announced defaults)
- A1 EXEC-ENV        | SSH VPS for runtime code (MCP, billing, webhook, SOUL); Modal code local-then-`modal deploy`; SQL local file then `docker cp` to supabase-db | repo structure (docs-only mirror, code on VPS) | reversible
- A2 ENUM-TRANSLATE   | **(Metis M2)** Explicit mapping table at MCP→DB boundary via helper `map_action_for_db(action: str) -> str`:
    - `check_user_access` (MCP-in `chat_nsfw|img_nsfw|video`) → SQL `check_user_access` (in `msg|img_nsfw|video`): `chat_nsfw`→`msg`, `img_nsfw`→`img_nsfw`, `video`→`video`
    - `record_usage` (MCP-in `msg|img|video`) → SQL `record_action` (in `msg|img|video`): identity (no translation)
    Helper + unit tests (pytest) cover all 6 input→output cases. | resolves blueprint §5.1 vs implementation_plan Step 2 mismatch | reversible
- A3 WEBHOOK-PORT     | 8088 (not 8080) | blueprint §11.3 supersedes §6.2 | reversible
- A4 CREDIT-FIRST     | Purchased credits deducted before monthly allocation | SQL record_action + RULESET | not reversible (business rule)
- A5 FREE-GATE         | FREE tier SFW only, 30 msg/day, no NSFW ever | RULESET §Content | not reversible
- A6 EXISTING-TOOLS    | Never modify generate_uncensored_visuals, list_available_models, get_conversation_context — only ADD | AGENTS.md §File Constraints | not reversible
- A7 VENV              | Always use /home/ubuntu/.hermes/hermes-agent/venv/ | AGENTS.md | not reversible
- A8 TEST-MODE-BILLING | **REMOVED (Metis S1)**: D2 puts sandbox/placeholder billing in Scope OUT. A8 was dangling. Tripay built only with real registered keys in W2.
- A9 TEST-STRATEGY     | Manual QA per blueprint §12 phases 1-4 + tests-after where feasible (SQL function tests, MCP tool unit tests with mock Supabase); full TDD not practical for Telegram bot + external services | blueprint §12 | reversible
- A10 TIER-EXPIRY      | **CORRECTED (Metis M1)**: SQL `check_user_access` does NOT read `tier_expires` (blueprint.md:278-372 verified). Auto-downgrade is a blueprint §12 Phase 4 TODO with no impl. **Adopted default**: implement via new SQL function `downgrade_expired_tiers()` + VPS systemd timer `naelvi-tier-expiry.timer` daily 00:00 WIB (pg_cron not assumed in self-hosted Supabase). Added as W2.5. | business rule (expiry) + impl choice (systemd) | impl reversible
- A11 MIGRATION-PATH    | **(Metis M4)** SQL migration committed at `supabase/migration.sql` (new top-level dir); Modal workers at `modal/worker_t2v.py`, `modal/worker_i2v.py`, `modal/common.py` (matches blueprint §10 file manifest) | repo structure | reversible
- A12 DB-PRECHECK       | **(Metis N2)** W1.1 pre-check: `\dt` must return no business tables; migration uses `CREATE TABLE IF NOT EXISTS` + `CREATE OR REPLACE FUNCTION` for idempotency | blueprint.md:163-194 uses plain CREATE → harden | reversible
- A13 I2V-QA            | **(Metis N1)** W1.8 includes explicit I2V QA: send test image + caption as ULTRA → expect MP4 <180s; if AnimateDiff img2img trick fails, gate I2V behind feature flag + document | D6 risk mitigation | reversible

## Findings (cited - path:lines)
- docs/blueprint.md:163-421 — full SQL: users, usage, credits, payments, video_jobs + get_or_create_usage, check_user_access, record_action + 5 indexes
- docs/blueprint.md §3 — tier definitions (FREE/PRO/ULTRA limits)
- docs/blueprint.md §5.1 — MCP tool contracts (existing 3 + NEW 5)
- docs/blueprint.md §6 — Tripay transaction flow + webhook HMAC (X-Signature)
- docs/blueprint.md §11.3 — webhook runs on :8088 (`uvicorn ... --port 8088`)
- docs/blueprint.md §13 — env vars: SUPABASE_DB_HOST/PORT, TRIPAY_*, Modal secrets, R2_*
- docs/implementation_plan.md:38-263 — 8-step build order + SQL + tool signatures + products.py dict
- docs/handoff.md — current state: Hermes+MCP+Supabase+Perchance+Novita running; billing/video/Modal/R2 NOT built; Tripay+Modal+R2 credentials NOT set up
- AGENTS.md — NEVER modify existing MCP tools; ALWAYS use venv; ALWAYS backup SOUL.md; Modal deploy separate
- RULESET.md §Pricing — APPROVED pricing (PRO 39k/ULTRA 79k + image S/M/L + video M/L); supersedes market_research.md draft (29k/59k)
- RULESET.md §Financial — Tripay sandbox first; no prod billing until webhook verified E2E; Modal $30 budget alert at $20
- SKILLSET.md — existing 3 MCP tools listed

## Decisions (with rationale)
- D1 Pricing source = RULESET.md (not market_research.md) | market_research draft superseded by approved | cited
- D2 Two-wave build: Wave 1 = no-external-blocker modules (DB, MCP gate tools, SOUL, Modal video, /status+/help bot); Wave 2 = gated on Tripay account registration (billing, /upgrade+//topup, create_payment_link) | F2 user chose "wait for Tripay first" → C4/C5-payment cannot build until registered | cited
- D3 VIDEO INCLUDED now (F1=user include) | full 6-module plan | cited
- D4 Video storage = Supabase Storage (F3=user Supabase) NOT R2 | R2 not configured, Supabase running | cited
- D5 Test strategy = manual QA blueprint §12 phases 1-4 + tests-after where feasible (F4 confirmed) | pragmatic for bot+external | cited
- D6 AnimateDiff I2V = use img2img trick (T2V-native model, blueprint §14 known issue); test in W1 verify; if fails, I2V documented as degraded | risk accepted | cited

## Scope IN
- Wave 1: C1 DB migration, C2-partial MCP (check_user_access, record_usage, get_user_status, generate_video_modal = 4 of 5 new tools), C3 SOUL tier rules, C6 Modal video (T2V+I2V via AnimateDiff-Lightning, Supabase Storage output), C5-partial bot /status + /help
- Wave 2 (gated, post-Tripay-registration): C4 Tripay billing (tripay_client + webhook :8088 + products), C2-remaining MCP create_payment_link, C5-remaining bot /upgrade + /topup
- All verified via blueprint §12 phases 1 (tier gate), 3 (video) in Wave 1; phases 2 (billing sandbox→E2E), 4 (edge cases) in Wave 2
- Docs updated locally (handoff.md status, implementation_plan.md checkboxes)
- SQL migration file + Modal worker code committed to this repo

## Scope OUT (Must NOT have)
- Marketing automation, persona system beyond Naelvi base, admin dashboard, multi-bot support
- Refactor of existing 3 MCP tools (generate_uncensored_visuals, list_available_models, get_conversation_context)
- SOUL.md content rewrite (only ADD tier rules section after backup)
- Move Supabase off self-hosted / off 127.0.0.1:5432
- Hardcode any API key (env vars / Modal secrets only)
- Run `modal deploy` from VPS (deploy from local/CI only)
- Use R2 for video (Supabase Storage decision D4)
- Build Tripay billing in sandbox/placeholder mode (D2 — wait for real registration)

## Open questions (forks to ask user)
ALL RESOLVED:
- F1 VIDEO-SCOPE     → INCLUDE now (D3)
- F2 TRIPAY-TIMING   → WAIT for registration (D2)
- F3 VIDEO-STORAGE   → Supabase Storage (D4)
- F4 TEST-STRATEGY   → Manual QA + tests-after (D5)

## Build waves (dependency-resolved)
### Wave 1 — no external blocker (build now)
| # | Todo | Component | Deps | Owner? |
|---|---|---|---|---|
| W1.1 | Write + apply SQL migration to Supabase (5 tables, 3 functions, 5 indexes; IF NOT EXISTS) | C1 | — | no |
| W1.2 | Add MCP tools check_user_access, record_usage, get_user_status to mcp_server.py (helper map_action_for_db + tests) | C2 | W1.1 | no |
| W1.3 | Backup SOUL.md → /root/hermes-rp-backups/<ts>/, inject TIER RULES section | C3 | W1.2 | no |
| W1.4 | **OWNER**: Modal account ($30 credit) + Supabase Storage bucket `naelvi-videos` + Modal secrets (MODAL_TOKEN_*) + update blueprint.md/SKILLSET.md R2→Supabase Storage (S3) | C6-prep + docs | — | **YES (owner)** |
| W1.5 | Write + `modal deploy` worker_t2v.py + worker_i2v.py + common.py (AnimateDiff-Lightning, ffmpeg→MP4, Supabase Storage upload) | C6 | W1.4 | no |
| W1.6 | Add MCP generate_video_modal + video_client.py (HTTP→Modal, deduct video credit on success, return URL) | C6+C2 | W1.5, W1.2 | no |
| W1.7 | Add bot /status (calls get_user_status) + /help to Hermes config | C5 | W1.2 | no |
| W1.8 | Verify blueprint §12 Phase 1 (tier gate) + Phase 3 (video incl. explicit I2V QA A13) | — | W1.1-W1.7 | no |

### Wave 2 — gated on Tripay account registration (owner action)
| # | Todo | Component | Deps | Owner? |
|---|---|---|---|---|
| W2.0 | **OWNER**: register Tripay (KTP + bank), get API_KEY + MERCHANT_CODE + PRIVATE_KEY | pre | — | **YES (owner)** |
| W2.1 | Write tripay_client.py + products.py + webhook.py (FastAPI :8088, HMAC X-Signature verify) | C4 | W2.0 | no |
| W2.2 | Add MCP create_payment_link tool to mcp_server.py | C2 | W2.1 | no |
| W2.3 | Add bot /upgrade + /topup to Hermes config | C5 | W2.2 | no |
| W2.4 | Implement `downgrade_expired_tiers()` SQL function + systemd timer `naelvi-tier-expiry.timer` daily 00:00 WIB (A10) | new | W2.1 | no |
| W2.5 | Verify blueprint §12 Phase 2 (billing E2E) + Phase 4 (edge cases: double-stack, timeout, Supabase down, spam, tier-expiry now impl'd) | — | W2.1-W2.4 | no |

## Approval gate
status: approved (user said "ok" 2026-07-07) + post-approval revision D7 (Tripay→Pakasir) + dual-review revision (Oracle APPROVE-WITH-FIXES + Momus REJECT → all fixes applied, awaiting Momus re-review)
Metis gap analysis: APPROVE-WITH-FIXES → all 5 must-fix + 3 should-fix applied

### Dual-review history (2026-07-07)
- Oracle (bg_2492afec / ses_0c4716eecffevC0aLyhIWKfbsA): APPROVE-WITH-FIXES — 3 deep + 5 surface + 3 unverified assumptions
- Momus round 1 (bg_94e400cd / ses_0c46fcca2ffeQgG5lnms0wb3DX): REJECT — 3 critical + 3 medium + 3 low
- All 14 fixes applied to .omo/plans/naelvi-build.md (Momus M-C1/C2/C3, M-M4/M5/M6, Oracle C1/C2/C3, S1/S2/S3/S4/S5)
- Residual accepted: Momus M-L7 (SQL cosmetic), M-L8 (W2.0 handoff boundary — addressed via AC), M-L9 (W2.5 "ALL 3" reworded), Oracle O-W1.9 (Modal cost alert — scoped out, F3 manual QA), O-W2.0-AC4 (Pakasir IPs — folded into W2.1 IP whitelist)

### Plan-format warning
W2.0b uses `9b.` label not parsed by /start-work progress counter (shows 18/19). All 19 todos visible to executor. Acceptable tradeoff — renumbering 10-15 would cascade evidence paths.

**Post-approval revision (D7)**: User decided Tripay CLOSED → swap to Pakasir (account under review ~3 hari) + future Custom PG (out of scope, fills e-wallet/BCA VA/Mandiri VA/retail gap). Duitku rejected (needs NPWP). Midtrans rejected (likely NSFW-blocked). Plan updated: Wave 2 W2.0-W2.5 swap Tripay→Pakasir (drop HMAC, add IP whitelist + double-check API, rename env/file/service, status enum `pending/canceled/completed`), SQL column `tripay_ref`→`pg_ref` (generic for future swap), W2.5 adds 3 forged-webhook-resistance tests. Custom PG = future enhancement plan (NOT this plan).
Plan written to: .omo/plans/naelvi-build.md (TL;DR + Scope + Verification + Execution + 14 todos + Final verification + Commit + Success criteria) — Pakasir-swap applied
Next: re-spawn Momus for re-review → if APPROVE → /start-work
**Decision D7 added**: Pakasir primary PG (pending review), Custom PG future scope-out (e-wallets/BCA VA/Mandiri VA/retail). Owner accepts Pakasir BI-license unverif risk (mitigation: future custom PG swap if needed).
**Decision D8 added**: SQL uses generic `pg_ref` column (not `tripay_ref`/`pakasir_ref`) — future-proofs custom PG swap with zero migration.