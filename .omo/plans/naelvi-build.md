# naelvi-build - Work Plan

## TL;DR (For humans)

**What you'll get:** Bot NAELVI jadi punya 3 tingkat langganan (Gratis, PRO Rp 39.000, ULTRA Rp 79.000) dengan pembayaran via Pakasir (QRIS+VA, pending review akun ~3 hari) + video NSFW lewat Modal + credit pack untuk gambar/video. Free user dibatas 30 pesan/hari + SFW only. PRO/ULTRA dapat NSFW unlimited + gambar/video bulanan. **Pakasir tidak mendukung e-wallet/BCA VA/Mandiri VA/retail — metode yang hilang akan diisi custom PG di masa depan (di luar plan ini).**

**Why this approach:** Dipecah jadi 2 gelombang — Gelombang 1 dikerjakan sekarang (database + gerbang tier + persona SOUL + video Modal + command /status) karena butuh PG; Gelombang 2 (billing Pakasir + /upgrade + /topup + auto-expiry) menyusul setelah review akun Pakasir selesai (~3 hari). Penyimpanan video pakai Supabase Storage (bukan R2) karena sudah jalan. SQL pakai nama kolom generik `pg_ref` (bukan `tripay_ref`) supaya swap ke custom PG di masa depan tanpa migrasi.

**What it will NOT do:** Tidak ada dashboard admin, tidak ada persona tambahan selain Naelvi, tidak ada R2/Cloudflare, tidak ada billing sandbox/test-mode (Pakasir pakai key asli setelah review), tidak ada refactor tool MCP yang sudah ada, **tidak ada custom PG di plan ini** (future enhancement untuk metode yang tidak didukung Pakasir: e-wallet, BCA VA, Mandiri VA, retail).

**Effort:** XL (14 todos across 2 waves, ~5-8 hari kerja + bottleneck Pakasir review ~3 hari)
**Risk:** Medium — AnimateDiff I2V belum teruji (mitigasi: feature flag + dokumentasi degradasi); Modal $30 budget (mitigasi: alert di $20); tier-expiry sebelumnya tidak ada implementasi (mitigasi: systemd timer daily); **Pakasir webhook tanpa HMAC signature** (mitigasi: IP whitelist + double-check via `transactiondetail` API + idempotent DB upsert); **Pakasir BI license unverif** (mitigasi: owner accept risk, dokumentasi untuk future custom PG swap)
**Decisions to sanity-check:** (1) Video pakai Supabase Storage bukan R2. (2) Tier-expiry pakai systemd timer VPS. (3) Pakasir sebagai PG utama (review pending), Custom PG future scope-out. (4) SQL pakai `pg_ref` generik.

Your next move: approve plan, lalu jalankan `$start-work .omo/plans/naelvi-build.md` atau `/start-work`. Detail lengkap di bawah.

---

> TL;DR (machine): XL | Risk-Medium | 14 todos 2 waves | NAELVI 3-tier bot + Pakasir billing (pending review) + Modal video + tier-expiry | blocker: Pakasir account review (~3 hari) | future scope-out: custom PG for missing methods

## Scope
### Must have
- **Wave 1 (no external blocker — build now)**:
  - SQL migration: 5 tables (`users`, `usage`, `credits`, `payments`, `video_jobs`), 3 functions (`get_or_create_usage`, `check_user_access`, `record_action`), 5 indexes — applied to self-hosted Supabase (127.0.0.1:5432 via `docker exec supabase-db`)
  - 4 of 5 new MCP tools in `/home/ubuntu/.hermes/custom_mcp/mcp_server.py`: `check_user_access`, `record_usage`, `get_user_status`, `generate_video_modal` (+ action-translation helper `map_action_for_db` with unit tests)
  - SOUL.md TIER RULES section injected (backup FIRST to `/root/hermes-rp-backups/<timestamp>/`)
  - Modal video workers `modal/worker_t2v.py`, `modal/worker_i2v.py`, `modal/common.py` (AnimateDiff-Lightning 4-step, ffmpeg→MP4, upload to Supabase Storage bucket `naelvi-videos`), deployed via `modal deploy` from local/CI
  - `video_client.py` in MCP + `generate_video_modal` tool wiring Modal HTTP + credit deduction on success
  - Bot commands `/status` + `/help` in Hermes config
  - Docs synced: `blueprint.md` + `SKILLSET.md` swap R2→Supabase Storage for video output
  - Verification: blueprint §12 Phase 1 (tier gate) + Phase 3 (video, incl. explicit I2V QA)
- **Wave 2 (gated on Pakasir account review — owner action)**:
  - Pakasir account review complete (owner: ~3 hari wait), real `slug` + `api_key` obtained
  - `pakasir_client.py` + `products.py` + `webhook.py` (FastAPI on `:8088`, **NO HMAC** — verifikasi via IP whitelist + double-check `GET /api/transactiondetail`, idempotent DB upsert on `order_id`)
  - 5th MCP tool `create_payment_link` in `mcp_server.py`
  - Bot commands `/upgrade` + `/topup`
  - Tier-expiry mechanism: `downgrade_expired_tiers()` SQL function + VPS systemd timer `naelvi-tier-expiry.timer` daily 00:00 WIB
  - Verification: blueprint §12 Phase 2 (billing E2E) + Phase 4 (edge cases)
  - **SQL uses generic `pg_ref` column** (not `pakasir_ref`) — future custom PG swap = no migration

### Must NOT have (guardrails, anti-slop, scope boundaries)
- **Never modify existing 3 MCP tools** (`generate_uncensored_visuals`, `list_available_models`, `get_conversation_context`) — only ADD
- **Never edit SOUL.md without backup first**
- **Always use venv** `/home/ubuntu/.hermes/hermes-agent/venv/` for VPS Python work
- **Always deploy Modal via `modal deploy`** from local/CI — NEVER from VPS
- **API keys NEVER hardcoded** — env vars or Modal secrets only
- **Supabase via local Docker network only** (127.0.0.1:5432)
- **No Tripay** (registration closed — D2 superseded by D7)
- **No Duitku** (requires NPWP — owner rejected)
- **No Midtrans** (likely NSFW-rejected per librarian research)
- **No custom payment gateway in this plan** — Pakasir is primary PG; missing methods (e-wallet OVO/DANA/ShopeePay, BCA VA, Mandiri VA, retail Alfamart/Indomaret) deferred to future enhancement plan
- **No Tripay sandbox/placeholder code** — Wave 2 builds only with real Pakasir keys (post-review)
- **No R2 / Cloudflare** — video storage is Supabase Storage (decision D4)
- **No full SOUL.md rewrite** — only insert TIER RULES section
- **No marketing automation, persona system beyond Naelvi, admin dashboard, multi-bot support**
- **No hardcoded `as any` / `@ts-ignore`** — type-safe code only where applicable
- **FREE tier SFW only — zero exceptions** (RULESET §Content)
- **Credit-first deduction** — purchased credits before monthly allocation (RULESET business rule)
- **Modal spending alert at $20** of $30 budget (RULESET §Financial)

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: **tests-after** for SQL functions (pytest + psycopg2 mock Supabase / direct docker exec psql) and MCP tools (pytest + mock DB); **manual QA** per blueprint §12 phases 1-4 for end-to-end Telegram bot behavior (pragmatic given external services: Telegram, OpenRouter, Novita, Modal, Pakasir).
- Evidence: `.omo/evidence/task-<N>-naelvi-build.<ext>` (SQL output dumps, pytest reports, screenshots of Telegram bot responses, Modal dashboard cost screenshots, Pakasir webhook callback logs)
- Frameworks: pytest 8.x, psycopg2, httpx (for webhook/MCP tool tests),ffmpeg for video validation, `docker exec supabase-db psql` for direct DB verification

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Wave 1 = 8 todos (W1.1-W1.8), Wave 2 = 7 todos (W2.0, W2.0b, W2.1-W2.5).

**Wave 1** (8 todos, no external blocker): DB migration → MCP gate tools → SOUL → [OWNER: Modal+Storage+docs setup] parallel with → Modal workers → video_client → bot /status → verify Phase 1+3
**Wave 2** (7 todos, gated): [OWNER: Pakasir review wait] + [Docs sync Tripay→Pakasir parallel] → Pakasir client/webhook → create_payment_link → bot /upgrade+/topup → tier-expiry mechanism → verify Phase 2+4

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| W1.1 SQL migration | — | W1.2 | W1.4 (owner setup) |
| W1.2 MCP gate tools | W1.1 | W1.3, W1.6, W1.7 | W1.4, W1.5 (after W1.4) |
| W1.3 SOUL tier rules | W1.2 | W1.8 | W1.4, W1.5, W1.6, W1.7 |
| W1.4 OWNER: Modal+Storage+docs | — | W1.5 | W1.1, W1.2, W1.3 |
| W1.5 Modal workers | W1.4 | W1.6 | W1.2 (after W1.1), W1.3, W1.7 |
| W1.6 video_client + generate_video_modal | W1.5, W1.2 | W1.8 | W1.3, W1.7 |
| W1.7 bot /status + /help | W1.2 | W1.8 | W1.3, W1.5, W1.6 |
| W1.8 verify Phase 1+3 | W1.1-W1.7 | — | — |
| W2.0 OWNER: Pakasir review wait | — | W2.1 | (any W1 remaining) |
| W2.0b Docs sync Tripay→Pakasir | — | W2.5 | W2.0, W2.1, W2.2, W2.3, W2.4 |
| W2.1 Pakasir billing | W2.0 | W2.2, W2.3 | W2.0b, W2.4 |
| W2.2 create_payment_link MCP | W2.1 | W2.3, W2.5 | W2.4 |
| W2.3 bot /upgrade + /topup | W2.2 | W2.5 | W2.4 |
| W2.4 tier-expiry mechanism | — | W2.5 | W2.1, W2.2, W2.3 |
| W2.5 verify Phase 2+4 | W2.1-W2.4 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.

### Wave 1 — no external blocker (build now)

- [x] 1. W1.1 — Supabase SQL migration (5 tables, 3 functions, 5 indexes)
  What to do / Must NOT do: Write `supabase/migration.sql` in this repo with `CREATE TABLE IF NOT EXISTS` (harden blueprint's plain CREATE per A12) for `users`, `usage`, `credits`, `payments`, `video_jobs`; `CREATE OR REPLACE FUNCTION` for `get_or_create_usage`, `check_user_access` (action enum `msg|img_nsfw|video`), `record_action` (action enum `msg|img|video`, credit-first deduction); 5 indexes. **CRITICAL: rename `payments.tripay_ref` from blueprint.md:163-194 to `payments.pg_ref` (TEXT UNIQUE) — generic column for future PG swap (D7 custom PG future scope-out; current PG = Pakasir)**. Apply via `docker cp supabase/migration.sql supabase-db:/tmp/migration.sql` then `docker exec supabase-db psql -U postgres -f /tmp/migration.sql`. Must NOT drop existing data; must NOT use plain `CREATE TABLE` (idempotent only); must NOT touch Supabase auth/system tables; must NOT use `tripay_ref` column name (use `pg_ref`).
  Parallelization: Wave 1 | Blocked by: — | Blocks: W1.2 | Parallelize with: W1.4 (owner setup)
  References (executor has NO interview context): `docs/blueprint.md:163-421` (full SQL), `docs/implementation_plan.md:44-83` (table defs), `docs/handoff.md:25-37` (Supabase access), `AGENTS.md` §Key Paths, `RULESET.md` §Data Safety (lines 27-34, backup before destructive). SSH `root@172.232.232.65`, Supabase dir `/home/ubuntu/supabase/docker/`.
  Acceptance criteria (agent-executable): (1) `docker exec supabase-db psql -U postgres -c "\dt" | grep -E "users|usage|credits|payments|video_jobs"` returns 5 rows. (2) `docker exec supabase-db psql -U postgres -c "\df" | grep -E "get_or_create_usage|check_user_access|record_action"` returns 3 rows. (3) `SELECT check_user_access(999999, 'msg')` returns `(allowed=true, reason='ok', remaining=30)` for non-existent user (auto-creates as free). (4) `SELECT record_action(999999, 'msg')` returns `(ok=true, remaining=29)`. (5) Re-run migration.sql — no errors (idempotent).
  QA scenarios: happy = fresh DB → all 5 tables + 3 functions created, function calls return expected; failure = run migration on DB with existing `users` table → must not error (IF NOT EXISTS), must not truncate. Evidence `.omo/evidence/task-1-naelvi-build.txt` (psql output).
  Commit: Y | feat(supabase): add migration.sql with users/usage/credits/payments/video_jobs + 3 functions

- [x] 2. W1.2 — MCP tier gate tools (check_user_access, record_usage, get_user_status) + action-translation helper
  What to do / Must NOT do: Add 3 new tools to `/home/ubuntu/.hermes/custom_mcp/mcp_server.py` (SSH VPS, use venv `/home/ubuntu/.hermes/hermes-agent/venv/`). Add helper `map_action_for_db(action: str) -> str` mapping `chat_nsfw`→`msg`, `img_nsfw`→`img_nsfw`, `video`→`video` (for `check_user_access`); identity for `record_usage` (`msg|img|video`). Tools call Supabase via `psycopg2` with env vars `SUPABASE_DB_HOST=127.0.0.1`, `SUPABASE_DB_PORT=5432`, `SUPABASE_DB_NAME=postgres`, `SUPABASE_DB_USER=postgres`, `SUPABASE_DB_PASS` (from `/home/ubuntu/supabase/docker/.env`). Must NOT modify existing 3 tools. Must NOT hardcode DB password. Must NOT use `as any`. Each tool returns JSON-serializable dict.
  Parallelization: Wave 1 | Blocked by: W1.1 | Blocks: W1.3, W1.6, W1.7 | Parallelize with: W1.4, W1.5 (after W1.4)
  References: `docs/implementation_plan.md:87-120` (tool signatures), `docs/blueprint.md:278-415` (SQL function bodies — `check_user_access` does NOT read `tier_expires`), `.omo/drafts/naelvi-build.md` A2 (mapping table), AGENTS.md §File Constraints (only ADD), `RULESET.md` §Access Control (lines 137-151).
  Acceptance criteria: (1) `mcp_server.py` imports without error: `cd /home/ubuntu/.hermes/custom_mcp && /home/ubuntu/.hermes/hermes-agent/venv/bin/python -c "import mcp_server"`. (2) `pytest tests/test_map_action_for_db.py` passes all 6 cases. (3) Manual MCP call `check_user_access(telegram_id=999999, action='chat_nsfw')` returns `{"allowed": false, "reason": "free tier SFW only", "remaining": 0}` for free user — `remaining:0` = no NSFW quota (free tier has 0 NSFW by design; SFW quota tracked separately via `record_action('msg')` returning remaining of 30). (4) `record_usage(999999, 'msg')` decrements `remaining`. (5) `get_user_status(999999)` returns dict with `tier, expires, msg_today, img_month, video_month, img_credits, video_credits`.
  QA scenarios: happy = free user denied NSFW chat with persona-friendly reason; failure = Supabase down → tool returns `{"allowed": false, "reason": "service unavailable", "remaining": 0}` (no crash). Evidence `.omo/evidence/task-2-naelvi-build.txt` (pytest + MCP call logs).
  Commit: Y | feat(mcp): add check_user_access, record_usage, get_user_status + map_action_for_db helper

- [x] 3. W1.3 — SOUL.md TIER RULES injection (backup FIRST)
  What to do / Must NOT do: SSH VPS. Backup `cp /root/hermes-rp-backups/20260701-013604/SOUL.md /root/hermes-rp-backups/$(date +%Y%m%d-%H%M%S)-tier-rules/SOUL.md` (create dir first). Then insert TIER RULES section (per `docs/implementation_plan.md:128-149`) at the TOP of SOUL.md after the persona header. Must NOT rewrite existing persona content. Must NOT skip backup. Must NOT edit any other SOUL.md backup.
  Parallelization: Wave 1 | Blocked by: W1.2 | Blocks: W1.8 | Parallelize with: W1.4, W1.5, W1.6, W1.7
  References: `docs/implementation_plan.md:123-149` (TIER RULES text), `AGENTS.md` §File Constraints (NEVER modify SOUL.md without backup), `RULESET.md` §Persona Rules, `/root/hermes-rp-backups/20260701-013604/SOUL.md` (live file).
  Acceptance criteria: (1) `ls /root/hermes-rp-backups/ | grep $(date +%Y%m%d)` shows new backup dir with SOUL.md copy. (2) `diff` between backup and live shows ONLY the TIER RULES section added (no other lines changed). (3) `head -50 /root/hermes-rp-backups/20260701-013604/SOUL.md` shows TIER RULES section near top. (4) Hermes gateway restart succeeds (no SOUL.md parse error): `systemctl restart hermes-gateway && systemctl status hermes-gateway` shows active.
  QA scenarios: happy = backup created + TIER RULES injected + Hermes restarts clean + free user NSFW chat request gets in-persona denial mentioning /upgrade; failure = SOUL.md syntax breaks Hermes parse → rollback from backup, fix syntax, retry. Evidence `.omo/evidence/task-3-naelvi-build.txt` (diff + systemctl status + Telegram screenshot).
  Commit: N (VPS file, not in repo) — but commit a `docs/soul_tier_rules_snippet.md` reference copy to repo
  Commit (repo): Y | docs(soul): add TIER RULES snippet reference for SOUL.md injection

- [~] 4. W1.4 — OWNER: Modal account + Supabase Storage bucket + docs sync (Storage ✅ + docs ✅ done; Modal $30 + tokens + secrets blocked on owner — W1.5 deploy gated)
  What to do / Must NOT do: **OWNER ACTION** (user does this, not agent). (a) Register modal.com account, add credit card, claim $30 starter credit, run `modal token set` locally to set `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` (do NOT put on VPS). (b) Create Supabase Storage bucket `naelvi-videos` via Supabase dashboard or `docker exec supabase-db psql -U postgres -c "INSERT INTO storage.buckets (id, name) VALUES ('naelvi-videos', 'naelvi-videos');"` (c) Add env vars to Modal secrets (not VPS): `SUPABASE_DB_PASS`, `MODAL_TOKEN_*` already set. (d) **Agent does**: update `docs/blueprint.md` §2.3 table + §7 R2 references + §13 env vars (`R2_BUCKET` → `SUPABASE_STORAGE_BUCKET=naelvi-videos`); update `SKILLSET.md` video storage row. Must NOT put Modal tokens on VPS. Must NOT use R2.
  Parallelization: Wave 1 | Blocked by: — | Blocks: W1.5 | Parallelize with: W1.1, W1.2, W1.3
  References: `docs/handoff.md:99-107` (credentials needed), `docs/blueprint.md:57` (§2.3 R2 row), `docs/blueprint.md:941` (`R2_BUCKET=naelvi-videos`), `docs/blueprint.md:599-660` (worker_t2v.py skeleton with R2 refs), `AGENTS.md` (Modal deploy separate), `RULESET.md` §Modal Deployment.
  Acceptance criteria: (1) `modal token current` returns valid token locally. (2) `modal app list` works. (3) `docker exec supabase-db psql -U postgres -c "SELECT id FROM storage.buckets WHERE id='naelvi-videos';"` returns 1 row. (4) `grep -n "R2" docs/blueprint.md` returns 0 matches (all replaced with Supabase Storage). (5) `grep -n "R2" SKILLSET.md` returns 0 matches.
  QA scenarios: happy = Modal token valid + bucket exists + docs clean; failure = Modal token invalid → re-run `modal token set`; bucket exists → skip creation. Evidence `.omo/evidence/task-4-naelvi-build.txt` (modal token + psql + grep outputs).
  Commit: Y (docs sync only) | docs(infra): swap R2 → Supabase Storage for video output

- [~] 5. W1.5 — Modal video workers (worker_t2v.py, worker_i2v.py, common.py) deployed (code done commit d2c13d3 + 836ad9d fix; deploy gated on W1.4 owner Modal setup)
  What to do / Must NOT do: Write `modal/worker_t2v.py` (AnimateDiff-Lightning 4-step, 24 frame, 512px T2V), `modal/worker_i2v.py` (img2img trick: VAE encode input image → AnimateDiff), `modal/common.py` (model load, ffmpeg→MP4 H.264, upload to Supabase Storage bucket `naelvi-videos`, return public URL). Deploy via `modal deploy modal/worker_t2v.py` + `modal deploy modal/worker_i2v.py` from LOCAL (never VPS). GPU=L4, timeout=300s. **(Oracle C2 — PRE-FLIGHT before deploying workers)** Modal workers run on Modal cloud, NOT VPS — they need to reach Supabase Storage on VPS public IP `172.232.232.65:8000` (Kong gateway internal port). (a) Test from a NON-VPS machine (e.g. local laptop): `curl -I http://172.232.232.65:8000` must return 200/401 (NOT connection refused). (b) If refused: open firewall `ufw allow 8000/tcp` (or `iptables -A INPUT -p tcp --dport 8000 -j ACCEPT`), verify Supabase Kong `docker compose` exposes 8000 in `/home/ubuntu/supabase/docker/docker-compose.yml`. (c) Provide Modal secrets `SUPABASE_URL=http://172.232.232.65:8000` + `SUPABASE_SERVICE_KEY` (anon/service role key from `/home/ubuntu/supabase/docker/.env`). (d) If port 8000 cannot be exposed (security policy), fallback: VPS-side relay endpoint `POST /v1/video-upload` on the existing webhook FastAPI that proxies Supabase Storage upload — adds ~50 LOC + 1 endpoint. Document which path taken in `docs/handoff.md`. **(Oracle S2 — cleanup_old_outputs cron)** Add Modal scheduled function `@app.function(schedule=modal.Period(hours=6)) def cleanup_old_outputs()` that lists objects in `naelvi-videos` bucket older than 24h and deletes them (prevents unbounded disk growth; cost ~$0/ month). **(Oracle S5 — I2V feature flag)** Gate `worker_i2v` behind env `FEATURE_I2V_ENABLED` (default `false`). When disabled, `generate_video_modal(type='i2v')` returns `{allowed: false, reason: 'Image-to-video temporarily unavailable. Please use text-to-video with /video.', video_url: null}` with NO credit deduction. When enabled, run I2V QA in W1.8; if I2V fails, document degradation in `docs/handoff.md` known issues + leave flag `false`. Must NOT deploy from VPS. Must NOT hardcode secrets (use `modal.Secret.from_name`). Must NOT exceed $30 budget.
  Parallelization: Wave 1 | Blocked by: W1.4 | Blocks: W1.6 | Parallelize with: W1.2 (after W1.1), W1.3, W1.7
  References: `docs/blueprint.md:599-660` (worker_t2v.py skeleton), `docs/blueprint.md:662-710` (worker_i2v.py skeleton), `docs/blueprint.md:712-780` (common.py: model load, ffmpeg, upload), `docs/blueprint.md:782-790` (video settings table), `docs/implementation_plan.md:199-216`, `docs/market_research.md` §infra HPP (Modal L4 $0.000294/sec), `RULESET.md` §Financial (alert at $20).
  Acceptance criteria: (1) `modal app list` shows `worker_t2v` + `worker_i2v` deployed. (2) Local test: `python -c "import modal; f = modal.Function.lookup('worker_t2v', 'generate'); print(f.remote('a cat playing piano, anime style'))"` returns a Supabase Storage URL within 180s. (3) `curl -I <url>` returns 200 + content-type video/mp4. (4) `ffprobe <url>` shows 24fps, 512px, H.264, ~5s duration. (5) Modal dashboard spend < $5 after test runs.
  QA scenarios: happy = T2V prompt → MP4 URL returned <180s, valid MP4; failure = I2V AnimateDiff img2img trick fails (known risk blueprint §14) → gate I2V behind `FEATURE_I2V_ENABLED=false` flag, log error, document degradation in `docs/handoff.md` known issues. Evidence `.omo/evidence/task-5-naelvi-build.txt` (modal app list + ffprobe + Modal dashboard screenshot).
  Commit: Y | feat(modal): add worker_t2v, worker_i2v, common with AnimateDiff-Lightning + Supabase Storage upload

- [~] 6. W1.6 — video_client.py + generate_video_modal MCP tool (recovery on VPS done, live tests paused for commit/push)
  What to do / Must NOT do: Write `/home/ubuntu/.hermes/custom_mcp/video_client.py` (HTTP client to Modal functions via `modal.Function.lookup`, deducts video credit on success via `record_action(telegram_id, 'video')`, returns URL to Hermes). Add `generate_video_modal` tool to `mcp_server.py` (input: `telegram_id, prompt, type ('t2v'|'i2v'), image_url?`; output: `{job_id, status, eta_seconds}` or `{video_url}`). Must call `check_user_access(telegram_id, 'video')` BEFORE render. Must NOT render if allowed=false. Must NOT deduct credit on render failure. **(Oracle S3 — circuit breaker)** Maintain in-process counter of `video_jobs.status='failed'` in last 1h (query DB). If >5 failures in 1h: log alert to `/var/log/naelvi-video-circuit.log` + `generate_video_modal` returns `{status: 'unavailable', reason: 'video service temporarily disabled — try again in 30 min'}` (no credit deduction, no Modal call). Resets after 1h of no new failures. **(Oracle S5 conformance)** When `FEATURE_I2V_ENABLED=false` (set in Modal secrets + mirrored to MCP env): `generate_video_modal(type='i2v')` returns `{allowed: false, reason: 'Image-to-video temporarily unavailable. Please use text-to-video with /video.', video_url: null}` with NO credit deduction (no Modal call).
  Parallelization: Wave 1 | Blocked by: W1.5, W1.2 | Blocks: W1.8 | Parallelize with: W1.3, W1.7
  References: `docs/implementation_plan.md:212-216` (video_client spec), `docs/blueprint.md:530-560` (generate_video_modal contract), `docs/blueprint.md:391-415` (record_action credit-first deduction), `.omo/drafts/naelvi-build.md` A2.
  Acceptance criteria: (1) `generate_video_modal(telegram_id=ULTRA_USER, prompt='cat playing', type='t2v')` returns `{video_url: 'https://...mp4', status: 'done'}` within 180s. (2) `SELECT video_count FROM usage WHERE telegram_id=ULTRA_USER` incremented by 1. (3) `generate_video_modal(telegram_id=FREE_USER, ...)` returns `{allowed: false, reason: 'ultra tier required'}`. (4) On Modal timeout → returns `{status: 'failed', reason: 'render timeout'}` + no credit deducted. (5) `video_jobs` table row inserted with `modal_job_id`, `status`, `output_url`, `cost_estimate`.
  QA scenarios: happy = ULTRA user gets MP4 in Telegram via sendVideo + credit deducted; failure = Modal 500 → graceful error message in Telegram, no credit deduction, video_jobs row marked `status='failed'`. Evidence `.omo/evidence/task-6-naelvi-build.txt` (MCP call + psql + Telegram screenshot).
  Commit: Y | feat(mcp): add video_client + generate_video_modal tool with credit gating

- [~] 7. W1.7 — Bot commands /status + /help in Hermes config (blocked: depends on W1.6 video flow + W1.4 owner Modal setup)
  What to do / Must NOT do: Add `/status` (calls `get_user_status` MCP tool, formats tier + usage + credits + expiry) and `/help` (static usage guide) to Hermes Telegram platform config. Edit Hermes config YAML (backup current first). Must NOT add `/upgrade` or `/topup` (Wave 2). Must NOT break existing `/start` `/reset`. **(Oracle C1 — PRE-FLIGHT before editing Hermes config)** First inspect `/root/hermes-rp-backups/20260701-013604/config.yaml` (or current live config under `/home/ubuntu/.hermes/`) for command-routing mechanism. If config-driven slash commands are supported (e.g. `commands:` block, `platforms.telegram.commands:` schema), use it. If NOT supported (Hermes routes ALL messages through LLM persona without explicit command handlers), implement fallback W1.7-ALT: small `python-telegram-bot` wrapper script `/home/ubuntu/.hermes/bot_commands.py` running as separate systemd service `naelvi-bot-commands.service` that intercepts messages starting with `/` BEFORE Hermes gateway, handles `/status` `/help` locally, forwards everything else to Hermes. Document chosen path in `docs/bot_commands_spec.md`. Must NOT modify Hermes gateway source code itself.
  Parallelization: Wave 1 | Blocked by: W1.2 | Blocks: W1.8 | Parallelize with: W1.3, W1.5, W1.6
  References: `docs/implementation_plan.md:188-196`, `docs/blueprint.md:467-469` (/status calls get_user_status), `docs/blueprint.md:461-465` (/help), Hermes config at `/root/hermes-rp-backups/20260701-013604/config.yaml` (or current live config).
  Acceptance criteria: (1) `systemctl restart hermes-gateway` succeeds. (2) Telegram bot responds to `/status` with: tier, tier_expires (or "—"), msg_today/30 (free) or "unlimited" (pro/ultra), img_month/limit, video_month/limit (ultra), img_credits, video_credits. (3) `/help` returns usage guide. (4) `/start` `/reset` still work (regression check). (5) Free user `/status` shows `tier: free, msg: X/30`.
  QA scenarios: happy = user runs /status → formatted card with all fields; failure = MCP get_user_status returns error → /status shows "Maaf, status sedang tidak tersedia" (no crash). Evidence `.omo/evidence/task-7-naelvi-build.txt` (Telegram screenshots).
  Commit: N (VPS Hermes config) — commit `docs/bot_commands_spec.md` reference to repo
  Commit (repo): Y | docs(bot): add /status + /help command spec

- [~] 8. W1.8 — Verify blueprint §12 Phase 1 (tier gate) + Phase 3 (video) (blocked: depends on W1.7 + W1.6 + W1.5 deploy)
  What to do / Must NOT do: Execute blueprint §12 Phase 1 checklist (8 items: new user free auto-create, free NSFW chat denied, free NSFW image denied, free video denied, free SFW chat+image works, manual DB set pro → NSFW works, pro video denied, manual DB set ultra → video works) + Phase 3 checklist (ULTRA T2V → MP4 in Telegram, I2V image+caption → video, credit deducted, error → graceful, Modal dashboard cost accurate). Must NOT skip any checklist item. Must NOT mark pass without screenshot/log evidence.
  Parallelization: Wave 1 (final) | Blocked by: W1.1-W1.7 | Blocks: — | Parallelize with: —
  References: `docs/blueprint.md:847-905` (Phase 1-4 checklists), `.omo/drafts/naelvi-build.md` A13 (explicit I2V QA).
  Acceptance criteria: ALL 8 Phase 1 items + ALL 5 Phase 3 items pass with evidence. Specifically: free user NSFW chat → in-persona denial + /upgrade offer (not raw error); ULTRA T2V → MP4 in Telegram <180s; I2V either works OR `FEATURE_I2V_ENABLED=false` set + documented degradation.
  QA scenarios: happy = all 13 items pass; failure = any item fails → file as known issue in `docs/handoff.md`, decide fix-now vs defer. Evidence `.omo/evidence/task-8-naelvi-build/` (directory with 13 evidence files: screenshots, psql outputs, Modal logs).
  Commit: Y | docs(verify): record Wave 1 Phase 1+3 verification evidence

### Wave 2 — gated on Pakasir account review (owner action, ~3 hari)

- [~] 9. W2.0 — OWNER: Tunggu review akun Pakasir selesai (~3 hari) (owner action, external review pending)
  What to do / Must NOT do: **OWNER ACTION**. Akun Pakasir sudah didaftarkan, status under review (max 3 hari). Setelah approval: dapatkan real `slug` (project slug) + `api_key`. Set in VPS env `/home/ubuntu/.hermes/custom_mcp/.env` (NOT in repo) sebagai `PAKASIR_SLUG`, `PAKASIR_API_KEY`, `PAKASIR_API_URL=https://app.pakasir.com`. Must NOT commit keys to git. Must NOT pakai akun reseller pihak ketiga selain Pakasir official.
  Parallelization: Wave 2 | Blocked by: — | Blocks: W2.1 | Parallelize with: any remaining W1
  References: `docs/handoff.md:99-107` (credentials needed), `RULESET.md` §Financial, `.omo/drafts/naelvi-build.md` D7 (Pakasir swap decision), riset librarian Pakasir.
  Acceptance criteria: (1) `grep PAKASIR_API_KEY /home/ubuntu/.hermes/custom_mcp/.env` returns non-empty (NOT placeholder). (2) `curl -X POST "$PAKASIR_API_URL/api/transactioncreate/qris" -d "project=$PAKASIR_SLUG&order_id=TEST&amount=1000&api_key=$PAKASIR_API_KEY"` returns 200 JSON with `payment.payment_number`. (3) Keys NOT in `git log`. (4) Project mode = Production (bukan Sandbox) di dashboard Pakasir.
  QA scenarios: happy = Pakasir API responds 200 + payment URL generated; failure = 401 → re-verify api_key + project status active; project masih Sandbox → toggle ke Production. Evidence `.omo/evidence/task-9-naelvi-build.txt`.
  Commit: N (owner action, no code)

- [~] 9b. W2.0b — Docs sync: Tripay → Pakasir references (all 5 doc files) (blocked: depends on W2.0 owner keys)
  What to do / Must NOT do: Search-replace residual `Tripay`/`tripay_ref`/`TRIPAY_*` references to Pakasir equivalents across all repo docs (NOT market_research.md which keeps Tripay as historical comparison per Momus M-C3 fix). Files + targeted edits: (1) `docs/blueprint.md` §6 (Tripay transaction flow → Pakasir flow: drop HMAC X-Signature section, add IP whitelist + double-check pattern), §10 (`billing/tripay_client.py` → `billing/pakasir_client.py`), §13 (env vars: drop `TRIPAY_API_KEY`/`TRIPAY_MERCHANT_CODE`/`TRIPAY_PRIVATE_KEY`/`TRIPAY_API_URL`, add `PAKASIR_SLUG`/`PAKASIR_API_KEY`/`PAKASIR_API_URL`), §6 schema `payments.tripay_ref` → `payments.pg_ref`. (2) `docs/implementation_plan.md:76,114,155` (Tripay → Pakasir, tripay_client.py → pakasir_client.py, HMAC verify → IP whitelist + double-check). (3) `docs/handoff.md:67,71,102-104` (creds needed, billing status). (4) `RULESET.md:24-25,33,86-87,122,161,197` (Stop Conditions: "Tripay key unconfigured" → "Pakasir key unconfigured"; financial safety refs). (5) `docs/blueprint.md §12 Phase 2 checklist lines 884-893` (verification source-of-truth must reflect Pakasir double-check, not Tripay HMAC sandbox). Must NOT touch `docs/market_research.md` (historical Tripay vs Midtrans comparison preserved). Must NOT change RULESET pricing (PRO Rp39k/ULTRA Rp79k unchanged). Must NOT change tier definitions.
  Parallelization: Wave 2 | Blocked by: W2.0 (Pakasir real keys confirmed for accurate docs) | Blocks: W2.5 (verify reads synced docs) | Parallelize with: W2.1, W2.2, W2.3, W2.4
  References: Momus M-C3 (Critical — Tripay→Pakasir doc sync not assigned to any todo), Oracle S4 (AGENTS.md security rule update — covered separately in W2.1 AC), D7 (Pakasir swap decision), D8 (`pg_ref` generic column).
  Acceptance criteria: (1) `grep -i "tripay" docs/blueprint.md docs/implementation_plan.md docs/handoff.md RULESET.md AGENTS.md | grep -v "market_research"` returns 0 matches. (2) `grep "tripay_ref" docs/` returns 0 matches (all renamed to `pg_ref`). (3) `grep "TRIPAY_API_KEY\|TRIPAY_MERCHANT_CODE\|TRIPAY_PRIVATE_KEY" docs/` returns 0 matches. (4) `grep "PAKASIR_SLUG\|PAKASIR_API_KEY\|PAKASIR_API_URL" docs/blueprint.md` returns ≥3 matches. (5) `grep "HMAC\|X-Signature" docs/blueprint.md` returns 0 matches in billing section (historical ref in market_research.md OK). (6) `grep "double-check\|transactiondetail" docs/blueprint.md` returns ≥2 matches (new pattern documented).
  QA scenarios: happy = all 5 doc files synced, grep clean, blueprint §12 Phase 2 checklist now describes Pakasir double-check verification flow; failure = residual Tripay ref found → fix and re-grep. Evidence `.omo/evidence/task-9b-naelvi-build.txt` (grep outputs + diff snippets).
  Commit: Y | docs(sync): swap Tripay → Pakasir across blueprint, implementation_plan, handoff, RULESET, AGENTS (drop HMAC, add IP whitelist + double-check)

- [~] 10. W2.1 — Pakasir client + products + webhook (FastAPI :8088, NO HMAC — IP whitelist + double-check API) (blocked: depends on W2.0)
  What to do / Must NOT do: Write `/home/ubuntu/.hermes/custom_mcp/billing/pakasir_client.py` (`create_transaction(telegram_id, product_type, method='qris') → payment_url`; `get_transaction_status(order_id, amount) → status` via `GET /api/transactiondetail?project=&amount=&order_id=&api_key=`), `/home/ubuntu/.hermes/custom_mcp/billing/products.py` (PRODUCTS dict per `docs/implementation_plan.md:175-183`), `/home/ubuntu/.hermes/custom_mcp/billing/webhook.py` (FastAPI `POST /pakasir/callback` on `:8088`, **NO HMAC verify** — verifikasi pakai: (1) IP whitelist Pakasir webhook sender IP, (2) double-check `get_transaction_status(order_id, amount)` dari server VPS setiap callback, (3) idempotent DB upsert ON CONFLICT (pg_ref) DO NOTHING, (4) status enum map `pending`→`pending`, `completed`→`paid`, `canceled`→`canceled`). Update `payments.status='paid'` + `paid_at` only jika double-check returns `completed`. Update `users.tier`+`tier_expires` for subscription products OR increment `credits.img_credits`/`video_credits` for packs. Run via `uvicorn webhook:app --host 0.0.0.0 --port 8088` as systemd service `naelvi-pakasir-webhook`. Must NOT trust webhook payload tanpa double-check. Must NOT update DB sebelum double-check confirm. Must NOT use port 8080. Must NOT pakai HMAC logic (Pakasir tidak punya signature header).
  Parallelization: Wave 2 | Blocked by: W2.0 | Blocks: W2.2, W2.3 | Parallelize with: W2.4
  References: `docs/implementation_plan.md:153-184` (billing module + products dict), riset librarian Pakasir (API contract: `POST /api/transactioncreate/{method}`, body `{project, order_id, amount, api_key}`; webhook payload `{amount, order_id, project, status, payment_method, completed_at}`; status enum `pending/canceled/completed`; double-check via `GET /api/transactiondetail`), `docs/blueprint.md:830-845` (webhook :8088), `.omo/drafts/naelvi-build.md` A3 (port 8088), D7 (Pakasir swap).
  Acceptance criteria: (1) `systemctl start naelvi-pakasir-webhook && systemctl status naelvi-pakasir-webhook` active. (2) `curl -X POST http://localhost:8088/pakasir/callback` from non-whitelisted IP → 403. (3) Forged webhook with valid IP spoof + fake `order_id` tidak ada di DB → 404 (double-check fails). (4) Trigger test callback via Pakasir `/api/paymentsimulation` (test feature available in Production-mode projects, NOT a sandbox-mode contradiction with W2.0 AC(4)) → webhook terima → double-check returns `completed` → `payments.status='paid'`, `users.tier='pro'` + `tier_expires=NOW()+30 days`. (5) Credit pack callback → `credits.img_credits` incremented. (6) Duplicate callback (same `pg_ref`) → idempotent (no double tier upgrade). (7) `pytest tests/test_webhook_pakasir.py` passes (cases: valid callback, forged, duplicate, mismatched amount, IP-blocked). **(Oracle C3) Webhook handler MUST**: validate `request.client.host` (real TCP socket IP, NOT `X-Forwarded-For` header — trivially forgeable); wrap double-check + INSERT in Postgres `SERIALIZABLE` transaction (or `SELECT ... FOR UPDATE` on payments row) to prevent TOCTOU race between concurrent forged webhooks; explicitly compare `webhook_payload.amount == double_check_response.amount` and reject on mismatch with alert log. **(Oracle S4) Update `AGENTS.md` line ~50 §Security Rules**: replace "Tripay HMAC verify via X-Signature" with "Pakasir no-HMAC verify via IP whitelist + double-check API + idempotent DB upsert".
  QA scenarios: happy = real Pakasir callback → double-check confirms → DB updated → user sees tier upgrade; failure = forged webhook → 403/404 + no DB change; duplicate → idempotent (UNIQUE pg_ref constraint catches); amount mismatch (webhook says 39000, double-check says 0) → reject + log alert. Evidence `.omo/evidence/task-10-naelvi-build.txt` (pytest + curl + psql).
  Commit: Y | feat(billing): add pakasir_client, products, webhook with IP whitelist + double-check + idempotent DB updates

- [~] 11. W2.2 — create_payment_link MCP tool (Pakasir) (blocked: depends on W2.1)
  What to do / Must NOT do: Add `create_payment_link` tool to `mcp_server.py` (input: `telegram_id, product_type` ∈ `pro_monthly|ultra_monthly|img_pack_s|img_pack_m|img_pack_l|video_pack_m|video_pack_l`, optional `method='qris'`; output: `{payment_url, pg_ref, amount}`). Calls `pakasir_client.create_transaction` (`POST /api/transactioncreate/{method}`, body `{project, order_id, amount, api_key}`). Inserts `payments` row with `status='pending'`, `pg_ref=order_id`. Must NOT create duplicate pending payments for same user+product within 5 min (spam guard). Must NOT expose Pakasir internal errors to user.
  Parallelization: WAVE 2 | Blocked by: W2.1 | Blocks: W2.3, W2.5 | Parallelize with: W2.4
  References: `docs/implementation_plan.md:111-115` (create_payment_link contract), riset librarian Pakasir (API contract), `docs/implementation_plan.md:175-183` (PRODUCTS dict), D7 (Pakasir swap).
  Acceptance criteria: (1) `create_payment_link(telegram_id=USER, product_type='pro_monthly')` returns `{payment_url: 'https://app.pakasir.com/...', pg_ref: 'ORDER-XXXX', amount: 39000}`. (2) `SELECT * FROM payments WHERE pg_ref='ORDER-XXXX'` returns row with `status='pending'`. (3) Spam: call 3x in 1 min → same `pg_ref` returned (no duplicate rows). (4) Invalid `product_type` → returns `{error: 'invalid product'}`.
  QA scenarios: happy = user gets payment URL → pays → webhook upgrades tier; failure = Pakasir API down → returns `{error: 'payment service unavailable'}` (no crash, no DB row). Evidence `.omo/evidence/task-11-naelvi-build.txt`.
  Commit: Y | feat(mcp): add create_payment_link (Pakasir) with spam guard + pending payment tracking

- [~] 12. W2.3 — Bot commands /upgrade + /topup (blocked: depends on W2.2)
  What to do / Must NOT do: Add `/upgrade` (shows PRO Rp 39.000 + ULTRA Rp 79.000 options, calls `create_payment_link` on selection) and `/topup` (shows credit packs, calls `create_payment_link`) to Hermes config. Edit Hermes config YAML (backup first). Must NOT break `/status` `/help` `/start` `/reset`.
  Parallelization: Wave 2 | Blocked by: W2.2 | Blocks: W2.5 | Parallelize with: W2.4
  References: `docs/implementation_plan.md:188-196`, `docs/blueprint.md:474-477` (/upgrade, /topup), `docs/implementation_plan.md:175-183` (PRODUCTS for /topup options).
  Acceptance criteria: (1) `/upgrade` shows PRO + ULTRA with prices. (2) Selecting PRO → returns Pakasir payment URL. (3) `/topup` shows 5 credit packs (img S/M/L + video M/L). (4) Selecting pack → returns payment URL. (5) After real payment → user tier/credits updated (verified via `/status`). (6) `/status` `/help` still work (regression).
  QA scenarios: happy = /upgrade → pay → /status shows new tier; failure = user closes payment → no DB change (payments row stays `pending` then Pakasir marks `expired` after timeout). Evidence `.omo/evidence/task-12-naelvi-build.txt` (Telegram screenshots + psql).
  Commit: N (VPS Hermes config) — commit `docs/bot_commands_spec.md` update to repo
  Commit (repo): Y | docs(bot): add /upgrade + /topup command spec

- [~] 13. W2.4 — Tier-expiry mechanism (downgrade_expired_tiers + systemd timer) (blocked: depends on W2.1)
  What to do / Must NOT do: Write SQL function `downgrade_expired_tiers()` (UPDATE users SET tier='free', tier_expires=NULL WHERE tier_expires < NOW() AND tier IN ('pro','ultra'); return count). Add systemd timer `naelvi-tier-expiry.timer` (daily 00:00 Asia/Jakarta = 17:00 UTC) + service `naelvi-tier-expiry.service` (runs `docker exec supabase-db psql -U postgres -c "SELECT downgrade_expired_tiers();"`). **(Oracle S1) Service unit must include**: `Persistent=true` (catch up if VPS was down at scheduled time), `Restart=on-failure`, `RestartSec=300`, `StandardOutput=append:/var/log/naelvi-tier-expiry.log`, `StandardError=append:/var/log/naelvi-tier-expiry.log`. **(Oracle S1) Commit `docs/tier-expiry-manual-recovery.sql`** with idempotent fallback SQL for manual run if timer fails: `SELECT downgrade_expired_tiers();` + log cleanup `find /var/log -name 'naelvi-tier-expiry.log' -mtime +30 -delete`. Must NOT run more than once/day. Must NOT downgrade users with NULL tier_expires (free users). Must NOT use pg_cron (not assumed installed). Must NOT skip Persistent=true (multi-day downtime catch-up required).
  Parallelization: Wave 2 | Blocked by: — | Blocks: W2.5 | Parallelize with: W2.1, W2.2, W2.3
  References: `.omo/drafts/naelvi-build.md` A10 (corrected — SQL check_user_access does NOT read tier_expires; this todo fills the gap), `docs/blueprint.md:905` (Phase 4 tier-expiry TODO with no impl), `docs/blueprint.md:163-194` (users.tier_expires column).
  Acceptance criteria: (1) `SELECT downgrade_expired_tiers();` returns count. (2) Manual test: `UPDATE users SET tier='pro', tier_expires=NOW()-INTERVAL'1 day' WHERE telegram_id=TEST; SELECT downgrade_expired_tiers(); SELECT tier FROM users WHERE telegram_id=TEST;` → tier='free'. (3) `systemctl start naelvi-tier-expiry.service` succeeds. (4) `systemctl list-timers | grep naelvi-tier-expiry` shows next run 17:00 UTC. (5) Free users (tier_expires=NULL) untouched.
  QA scenarios: happy = expired pro/ultra → downgraded to free daily; failure = timer fails → `journalctl -u naelvi-tier-expiry.service` shows SQL error, retry. Evidence `.omo/evidence/task-13-naelvi-build.txt` (psql + systemctl + journalctl).
  Commit: Y | feat(billing): add downgrade_expired_tiers SQL + systemd timer for daily tier expiry

- [~] 14. W2.5 — Verify blueprint §12 Phase 2 (billing E2E) + Phase 4 (edge cases incl. forged-webhook resistance) (blocked: depends on W2.1-W2.4)
  What to do / Must NOT do: Execute Phase 2 checklist (/upgrade → payment link, real payment → webhook → double-check → DB updated → tier upgrade, /topup → credit added → credit decremented on use) + Phase 4 edge cases (30-day expiry → auto-downgrade via W2.4, PRO buying ULTRA → no double stack via payments.pg_ref UNIQUE, Pakasir order expiry → status='canceled' from double-check, Supabase down → MCP errors gracefully, /upgrade spam → no duplicate payment links via W2.2 spam guard, **forged webhook from non-whitelisted IP → 403, no DB change**, **forged webhook from whitelisted IP with fake order_id → 404 from double-check, no DB change**, **amount mismatch between webhook payload vs double-check → reject + alert log**). Must NOT skip any item. Must NOT mark pass without evidence.
  Parallelization: Wave 2 (final) | Blocked by: W2.1-W2.4 | Blocks: — | Parallelize with: —
  References: `docs/blueprint.md:880-905` (Phase 2 + Phase 4 checklists), W2.4 tier-expiry mechanism, D7 (Pakasir security model), riset librarian Pakasir (no-HMAC + double-check pattern).
  Acceptance criteria: ALL 4 Phase 2 items + ALL 5 Phase 4 items + ALL 3 forged-webhook-resistance items pass with evidence. Specifically: real Pakasir payment → tier upgrade within 60s of webhook (double-check adds latency vs Tripay HMAC); 30-day expiry → user downgraded on next timer run; /upgrade spam → single payment link returned; forged webhook attempts → no DB mutation.
  QA scenarios: happy = all 12 items pass; failure = any item fails → file as known issue, decide fix-now vs defer. Evidence `.omo/evidence/task-14-naelvi-build/` (12 evidence files).
  Commit: Y | docs(verify): record Wave 2 Phase 2+4 + forged-webhook-resistance verification evidence

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for user's explicit okay before declaring complete.
- [~] F1. Plan compliance audit — every W1/W2 todo done, every acceptance criterion met, all evidence files present in `.omo/evidence/` (blocked: depends on all W1/W2)
- [~] F2. Code quality review — no `as any`/`@ts-ignore`, no hardcoded keys, no empty catch, all functions ≤50 lines, existing 3 MCP tools unmodified (diff check) (blocked: depends on all W1/W2)
- [~] F3. Real manual QA — full Telegram bot walkthrough as free/pro/ultra user across chat/image/video/billing; Modal dashboard cost < $20; Supabase volume backup taken before W2.4 destructive test (blocked: depends on all W1/W2)
- [~] F4. Scope fidelity — no scope-creep beyond Wave 1+2 todos; docs (blueprint.md, SKILLSET.md, handoff.md, implementation_plan.md) updated to reflect built state; no R2 references remain (blocked: depends on all W1/W2)

## Commit strategy
- Conventional commits: `feat(<scope>):`, `docs(<scope>):`, `fix(<scope>):` per todo Commit lines
- Scopes: `supabase`, `mcp`, `soul`, `infra`, `modal`, `bot`, `billing`, `verify`
- VPS files (mcp_server.py, SOUL.md, Hermes config, billing/) committed to repo as reference copies under `docs/` (e.g. `docs/soul_tier_rules_snippet.md`, `docs/bot_commands_spec.md`) — actual VPS files edited in place via SSH
- Local repo files (`supabase/migration.sql`, `modal/worker_*.py`, `modal/common.py`) committed directly
- NEVER commit API keys, .env, or credentials
- Branch: work on `feature/naelvi-build` (or directly on main per repo's single-commit history — confirm with user before PR)

## Success criteria
- Wave 1 done: free/pro/ultra tier gating works, NSFW denied for free, ULTRA T2V video renders in Telegram, /status shows tier+usage, Modal spend <$20 of $30
- Wave 2 done: real Pakasir payment → tier upgrade (within 60s incl. double-check), credit packs → credits decremented on use, 30-day expiry → auto-downgrade, all 4 phases of blueprint §12 + forged-webhook-resistance verified with evidence
- Docs synced: blueprint.md + SKILLSET.md reflect Supabase Storage (no R2), blueprint.md §6 + §13 + §10 + handoff.md swap Tripay→Pakasir (drop HMAC section, add double-check pattern, env vars `PAKASIR_SLUG`/`PAKASIR_API_KEY`/`PAKASIR_API_URL`, file `billing/pakasir_client.py`, column `pg_ref`), handoff.md shows all components ✅, implementation_plan.md checkboxes ticked
- Zero hardcoded secrets in git history
- Existing 3 MCP tools unmodified (verified via diff)
