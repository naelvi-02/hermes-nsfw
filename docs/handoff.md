# NAELVI — Handoff Summary

**Tanggal**: 2026-07-08 17:00 WIB  
**Sesi**: Wave 1 complete — Modal video workers live, Supabase exposed, video_client dual-mode

---

## Current State

| Komponen | Status |
|---|---|
| Hermes Agent | ✅ Running (2 gateway instances) |
| MCP Server | ✅ Running (mcp_server.py — 6 tools + video) |
| Supabase | ✅ Running (Kong exposed on 0.0.0.0:8100) |
| Telegram Bot | ✅ Running via Hermes |
| NSFW Image | ✅ Novita via MCP |
| SFW Image | ✅ Perchance wrapper |
| T2V Video | ✅ Modal AnimateDiff → Supabase Storage |
| I2V Video | ✅ Deployed, gated (FEATURE_I2V_ENABLED=false) |
| Billing | ⏳ Blocked — tunggu Pakasir review |

---

## Supabase (Self-Hosted — EXPOSED)

```
Lokasi:       /home/ubuntu/supabase/docker/
DB:           PostgreSQL 15.8
User:         postgres
Password:     (stored in /home/ubuntu/supabase/docker/.env)
Kong HTTP:    0.0.0.0:8100 (UFW allowed) — external access for Modal workers
Kong Internal: 127.0.0.1:8000 — use from VPS

Restart after reboot:
  cd /home/ubuntu/supabase/docker && docker compose up -d

Storage bucket: naelvi-videos (public, Supabase Storage)
```

---

## Modal Workers

| Worker | App Name | Endpoint | Status |
|---|---|---|---|
| T2V | `naelvi-video-t2v` | `https://naelvi-02--naelvi-video-t2v-generate-t2v.modal.run` | ✅ Live |
| I2V | `naelvi-video-i2v` | `https://naelvi-02--naelvi-video-i2v-generate-i2v.modal.run` | ✅ Deployed (gated) |

```
Model:      emilianJR/epiCRealism + ByteDance/AnimateDiff-Lightning (raw safetensors)
GPU:        L4
Deploy cmd: modal deploy -m workers.worker_t2v
            modal deploy -m workers.worker_i2v
Secret:     supabase-secrets (SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_STORAGE_BUCKET, FEATURE_I2V_ENABLED)
```

---

## video_client.py (Dual-Mode)

```
Path:   /home/ubuntu/.hermes/custom_mcp/video_client.py
Mode 1: Modal SDK (Function.from_name) — local dev + Modal token
Mode 2: Raw HTTP POST — VPS fallback (no Modal token on VPS)
```

---

## VPS Access

```
SSH: ssh root@172.232.232.65
OS:  Ubuntu 24.04
RAM: 8GB (4GB used)
Disk: 157GB (43GB used, 107GB free)
Modal SDK: v1.5.1 (no token — uses HTTP fallback)
```

---

## Pricing (Approved)

```
FREE   Rp 0       — DeepSeek chat SFW, Perchance image SFW, 30 msg/hari
PRO    Rp 39.000  — Hanami NSFW chat unlimited, 100 img/bulan
ULTRA  Rp 79.000  — Semua PRO + 300 img/bulan + 30 video/bulan

IMAGE CREDIT:  S 50 img = Rp 5K | M 150 img = Rp 12K | L 500 img = Rp 35K
VIDEO CREDIT:  M 30 = Rp 25K | L 100 = Rp 70K
```

---

## Next Steps (Build Order)

1. **Daftar Pakasir** — (menunggu review ~3 hari)
2. ✅ ~~SQL Migration~~ — Done (5 tables: schema_v1.sql)
3. ✅ ~~MCP Tier Tools~~ — Done (check_user_access, record_usage, dll)
4. ✅ ~~SOUL.md Update~~ — Done (tier rules injected)
5. ✅ ~~Modal Video Workers~~ — Done (T2V live, I2V gated)
6. ✅ ~~Bot Commands~~ — Done (/status, /help)
7. **Pakasir Client + Webhook** — payment link + callback handler (W2.1-W2.5)
8. **End-to-End Test** — semua tier
9. **Marketing** — setelah produk jalan

---

## Documents

| Document | Path |
|---|---|
| **Blueprint** | docs/blueprint.md |
| **Implementation Plan** | docs/implementation_plan.md |
| **Market Research** | docs/market_research.md |
| **Handoff** | docs/handoff.md |
| **AGENTS.md** | ./AGENTS.md |
| **RULESET** | ./RULESET.md |

---

## Key Credentials

```
OpenRouter:    (VPS: /home/ubuntu/.hermes/custom_mcp/.env)
Novita:        (VPS: /home/ubuntu/.hermes/custom_mcp/.env)
Supabase DB:   (VPS: /home/ubuntu/supabase/docker/.env)
Modal:         profile naelvi-02, secret supabase-secrets
```

---

## Key Decisions (Session 2026-07-08)

- D4: Video storage = Supabase Storage bucket `naelvi-videos`
- D7: Tripay CLOSED → Pakasir primary PG
- D8: Kong exposed to 0.0.0.0:8100 (Modal workers need external access)
- Modal folders: `modal/` → `workers/`
- video_client.py: dual-mode (SDK + HTTP fallback) for Modal SDK 1.x compat
- AnimateDiff: raw safetensors load (not `from_pretrained` — ByteDance model has no config.json)
- Bucket bug: original `naelvi-videos` had spaces in ID — recreated clean
