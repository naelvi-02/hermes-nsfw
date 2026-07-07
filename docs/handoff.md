# NAELVI — Handoff Summary

**Tanggal**: 2026-07-07 08:13 WIB  
**Sesi**: Selesai — blueprint, riset, plan, implementasi selanjutnya siap build

---

## Current State

| Komponen | Status |
|---|---|
| Hermes Agent | ✅ Running (2 gateway instances) |
| MCP Server | ✅ Running (mcp_server.py) |
| Supabase | ✅ **Nyala** (baru di-restart) |
| Telegram Bot | ✅ Running via Hermes |
| NSFW Image | ✅ Novita via MCP |
| SFW Image | ✅ Perchance wrapper |
| Billing | ❌ Belum dibangun |
| Video | ❌ Modal belum terhubung |

---

## Supabase (Self-Hosted)

```
Lokasi:     /home/ubuntu/supabase/docker/
DB:         PostgreSQL 15.8
User:       postgres
Password:   (stored in /home/ubuntu/supabase/docker/.env)
Port:       localhost:5432

Restart after reboot:
  cd /home/ubuntu/supabase/docker && docker compose up -d

Test connection:
  docker exec supabase-db psql -U postgres -c 'SELECT version();'
```

---

## VPS Access

```
SSH: ssh root@172.232.232.65
OS:  Ubuntu 24.04
RAM: 8GB (4GB used)
Disk: 157GB (43GB used, 107GB free)
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

1. **Daftar Tripay** — butuh KTP + rekening bank
2. **SQL Migration** — jalankan SQL dari blueprint ke Supabase
3. **MCP Tier Tools** — tambah `check_user_access`, `record_usage`, dll ke mcp_server.py
4. **SOUL.md Update** — tambah tier rules ke persona
5. **Tripay Client + Webhook** — create payment link + callback handler
6. **Bot Commands** — `/status`, `/upgrade`, `/topup`
7. **Modal Video Workers** — Aku build menggunakan $30 credit
8. **End-to-End Test** — semua tier
9. **Marketing** — setelah produk jalan

---

## Documents Created

| Document | Path |
|---|---|
| **Blueprint (handoff)** | [blueprint.md](file:///C:/Users/naufa/.gemini/antigravity/brain/2fe08fd1-4e07-4fe3-aafc-e054bbc4cb38/blueprint.md) |
| **Implementation Plan** | [implementation_plan.md](file:///C:/Users/naufa/.gemini/antigravity/brain/2fe08fd1-4e07-4fe3-aafc-e054bbc4cb38/implementation_plan.md) |
| **Market Research** | [market_research.md](file:///C:/Users/naufa/.gemini/antigravity/brain/2fe08fd1-4e07-4fe3-aafc-e054bbc4cb38/market_research.md) |

---

## Key Credentials (Existing)

```
OpenRouter: (stored in VPS env — /home/ubuntu/.hermes/custom_mcp/.env)
Novita:     (stored in VPS env — /home/ubuntu/.hermes/custom_mcp/.env)
Supabase DB: (stored in VPS — /home/ubuntu/supabase/docker/.env)
```

---

## Key Credentials (Needed)

```
Tripay API Key         → daftar dulu
Tripay Merchant Code   → daftar dulu
Tripay Private Key     → daftar dulu
Modal Token ID/Secret  → daftar modal.com
R2 Access Key/Secret   → setup R2 bucket
```
