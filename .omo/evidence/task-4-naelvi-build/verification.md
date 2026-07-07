# W1.4 — OWNER: Modal + Supabase Storage + R2→Supabase docs sync

## Status: ⚠️ PARTIAL — agent portion DONE, OWNER portion blocked (Modal account setup)

## What was done by agent (this session)

### 1. Supabase Storage bucket `naelvi-videos` created ✅
- VPS executed via `docker exec supabase-db psql -U postgres -c "INSERT INTO storage.buckets ..."`
- Bucket config:
  - `id` = `name` = `naelvi-videos`
  - `public` = true (so Modal worker can write, anyone with URL can read MP4)
  - `file_size_limit` = 104857600 bytes (100 MB)
  - `allowed_mime_types` = `{"video/mp4"}`
- Verified via `SELECT FROM storage.buckets WHERE id='naelvi-videos'` → 1 row returned

### 2. Docs sync: R2 → Supabase Storage across 4 files ✅
- Delegated to Sisyphus-Junior (ses_0c41dff26ffeHUMhxTHSPVJH0n, model grok-code-fast-1, 6m53s)
- Edits:
  - `SKILLSET.md:142` — `Cloudflare R2 | Cloud` → `Supabase Storage (bucket: naelvi-videos) | Cloud (Self-hosted)`
  - `docs/blueprint.md:96` — `Cloudflare R2 | **Belum setup** | Untuk video storage` → `Supabase Storage | **Active** (bucket: naelvi-videos, public, 100MB, mp4 only) | Untuk video storage`
  - `docs/blueprint.md:658` — cleanup function comment `R2` → `Supabase Storage naelvi-videos bucket`
  - `docs/blueprint.md:941-944` — env vars:
    - `R2_BUCKET=naelvi-videos` → `SUPABASE_STORAGE_BUCKET=naelvi-videos`
    - `R2_ENDPOINT=` → `SUPABASE_URL=http://172.232.232.65:8000` (Kong gateway, exposed for Modal per Oracle C2)
    - `R2_ACCESS_KEY=` → `SUPABASE_SERVICE_KEY=` (owner fills from `/home/ubuntu/supabase/docker/.env`)
    - `R2_SECRET_KEY=` → deleted entirely
  - `docs/implementation_plan.md:205` — `Upload ke Supabase Storage atau R2` → `Upload ke Supabase Storage (bucket: naelvi-videos, public)`
  - `docs/handoff.md:106` — `R2 Access Key/Secret → setup R2 bucket` → `Supabase Storage bucket naelvi-videos → ✅ DONE (W1.4 — created via SQL INSERT, public, 100MB, mp4 only)`
- Also: `SKILLSET.md:57` was pre-edited by orchestrator (R2→Supabase Storage) before delegation — verified intact
- **Verification grep across the 4 target files (excluded market_research.md): 0 matches** for `R2|cloudflare.*storage|R2_BUCKET|R2_ACCESS|R2_ENDPOINT|R2_SECRET`
- **Commit:** `046eca6 docs(sync): swap R2 → Supabase Storage across SKILLSET, blueprint, implementation_plan, handoff (D7/S3 conformance)`
- market_research.md untouched (historical preserved per Must-NOT)

## OWNER portion — BLOCKED (not yet done)

The following steps require the owner (Nopal) to act on a third-party web UI; the agent cannot perform them:

1. **Modal account**: ensure modal.com account has $\ge$ $30 credit (or alert threshold set at $20 spend)
2. **Modal tokens**: generate `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` from modal.com → Settings → API Tokens
3. **Modal secrets** (set on modal.com → app settings or via `modal secret create`):
   - `SUPABASE_URL` = `http://172.232.232.65:8000` (VPS Kong gateway — verify `curl -I http://172.232.232.65:8000` from external machine returns 200/401 not refused; if refused, open ufw: `ufw allow 8000/tcp` — per Oracle C2 fix)
   - `SUPABASE_SERVICE_KEY` = service_role key from `/home/ubuntu/supabase/docker/.env` on VPS (DO NOT commit, DO NOT echo in chat — owner sets via `modal secret create SUPABASE_SERVICE_KEY=...` from their local machine)
   - `SUPABASE_STORAGE_BUCKET` = `naelvi-videos` (already created, see agent portion above)
   - `FEATURE_I2V_ENABLED` = `false` (default disabled — per Oracle S5)

Once owner has done the above, W1.5 (Modal workers deploy) can run `modal deploy` from local repo to push worker_t2v.py / worker_i2v.py / common.py.

## Acceptance criteria status

| AC | Status | Evidence |
|---|---|---|
| Storage bucket `naelvi-videos` exists | ✅ | `SELECT FROM storage.buckets WHERE id='naelvi-videos'` returns 1 row |
| Bucket is public, 100MB, mp4 only | ✅ | row data: `public=t, file_size_limit=104857600, allowed_mime_types={" video/mp4 "}` |
| `grep R2 docs/blueprint.md` returns 0 | ✅ | post-edit grep = 0 matches |
| `grep R2 SKILLSET.md` returns 0 | ✅ | post-edit grep = 0 matches |
| Modal token current/valid | ⏳ PENDING OWNER | agent has no modal.com credentials |
| `modal app list` works | ⏳ PENDING OWNER | depends on token |
| Modal credit ≥ $30 | ⏳ PENDING OWNER | account billing UI only |

## Must-NOT guardrails verified

- ✅ Did NOT modify `docs/market_research.md` (historical preserved)
- ✅ Did NOT change tier definitions, pricing, or non-R2 content (diff stat: 4 files, 9 insertions, 10 deletions — only R2-related lines touched)
- ✅ Did NOT hardcode SUPABASE_SERVICE_KEY value in docs (left blank for owner fill)
- ✅ Did NOT expose Supabase service key in any committed file

## Files touched

**VPS:**
- (Supabase DB) `storage.buckets` row inserted — `naelvi-videos` bucket

**Local repo (committed at 046eca6):**
- `SKILLSET.md` (line 57 + line 142)
- `docs/blueprint.md` (lines 96, 658, 941-944)
- `docs/implementation_plan.md` (line 205)
- `docs/handoff.md` (line 106)

## Owner action items (-blocking W1.5 deploy)

1. Top up Modal account to ≥ $30 credit
2. Generate Modal token ID + secret, set as env vars on local machine (for `modal deploy`)
3. Verify port 8000 reachable from external (curl from local: `curl -I http://172.232.232.65:8000`)
   - If refused: `ssh root@172.232.232.65 'ufw allow 8000/tcp'`
4. Set Modal secrets (run from local where Modal CLI installed):
   ```
   modal secret create SUPABASE_URL http://172.232.232.65:8000
   modal secret create SUPABASE_SERVICE_KEY <value from /home/ubuntu/supabase/docker/.env>
   modal secret create SUPABASE_STORAGE_BUCKET naelvi-videos
   modal secret create FEATURE_I2V_ENABLED false
   ```
5. Notify agent when done — W1.5 deploy can proceed

## Commit (agent portion)

`046eca6 docs(sync): swap R2 → Supabase Storage across SKILLSET, blueprint, implementation_plan, handoff (D7/S3 conformance)`

(Storage bucket is VPS-side state, not a repo file — recorded here only.)
