# Companion AI Bot — Final Implementation Plan

## Approved Pricing

```
FREE   Rp 0       — Chat SFW (DeepSeek gratis), Image SFW Perchance unlimited, 30 msg/hari
PRO    Rp 39.000  — Chat NSFW unlimited (Hanami), Image NSFW 100 img/bulan
ULTRA  Rp 79.000  — Semua PRO + Image NSFW 300 img/bulan + 30 video credit/bulan
```

### Credit Pack
```
IMAGE:  Pack S  50 img  = Rp  5.000
        Pack M 150 img  = Rp 12.000
        Pack L 500 img  = Rp 35.000

VIDEO:  Pack M  30 video = Rp 25.000
        Pack L 100 video = Rp 70.000
```

---

## Stack

| Layer | Tech |
|---|---|
| User DB + billing state | Supabase (self-hosted, sudah ada) |
| Tier gate | MCP tool baru di `mcp_server.py` |
| Payment | Tripay (QRIS, VA, e-wallet) |
| LLM Free | `deepseek/deepseek-chat-v3-0324:free` via OpenRouter |
| LLM PRO+ | Hanami `sao10k/l3.1-70b-hanami-x1` via OpenRouter |
| Image SFW | Perchance (existing) |
| Image NSFW | Novita (existing) |
| Video | Modal L4 + AnimateDiff-Lightning (baru) |

---

## Proposed Changes

### Step 1 — Supabase Schema

#### [NEW] SQL migration di Supabase

```sql
-- Users & tier
CREATE TABLE users (
  telegram_id   BIGINT PRIMARY KEY,
  username      TEXT,
  tier          TEXT DEFAULT 'free',       -- 'free' | 'pro' | 'ultra'
  tier_expires  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE usage (
  telegram_id   BIGINT REFERENCES users(telegram_id),
  period_start  DATE DEFAULT CURRENT_DATE,
  msg_count     INT DEFAULT 0,
  img_count     INT DEFAULT 0,
  video_count   INT DEFAULT 0,
  PRIMARY KEY (telegram_id, period_start)
);

-- Credit balance (additive, dibeli terpisah)
CREATE TABLE credits (
  telegram_id   BIGINT REFERENCES users(telegram_id),
  img_credits   INT DEFAULT 0,
  video_credits INT DEFAULT 0,
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Payment log
CREATE TABLE payments (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  telegram_id   BIGINT REFERENCES users(telegram_id),
  tripay_ref    TEXT UNIQUE,
  product_type  TEXT,   -- 'pro_monthly' | 'ultra_monthly' | 'img_pack_s' | etc
  amount_idr    INT,
  status        TEXT DEFAULT 'pending',  -- 'pending' | 'paid' | 'failed'
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  paid_at       TIMESTAMPTZ
);
```

---

### Step 2 — MCP Tier Gate Tools

#### [MODIFY] `/home/ubuntu/.hermes/custom_mcp/mcp_server.py`

Tambah 4 tools baru:

**`check_user_access`**
```
Input:  telegram_id, action (chat_nsfw | img_nsfw | video)
Output: { allowed: bool, reason: str, remaining: int }
```

**`record_usage`**
```
Input:  telegram_id, action (msg | img | video)
Output: { ok: bool, remaining: int }
```

**`get_user_status`**
```
Input:  telegram_id
Output: { tier, expires, msg_today, img_month, video_month, img_credits, video_credits }
```

**`create_payment_link`**
```
Input:  telegram_id, product_type
Output: { payment_url: str, tripay_ref: str, amount: int }
```

Logic routing LLM di Hermes:
- Free → paksa `deepseek/deepseek-chat-v3-0324:free`
- PRO/ULTRA → pakai Hanami seperti sekarang

---

### Step 3 — SOUL.md Update

#### [MODIFY] `/home/ubuntu/.hermes/hermes-rp-backups/20260701-013604/SOUL.md`

Tambah section TIER RULES di bagian awal:

```
## TIER RULES (WAJIB DIIKUTI)

Sebelum setiap aksi, panggil check_user_access:
- chat NSFW → action: chat_nsfw
- generate image NSFW → action: img_nsfw  
- generate video → action: video

Jika allowed=false:
- Tolak dengan sopan dalam karakter persona
- Tawarkan upgrade: "Mau unlock fitur ini? Ketik /upgrade"
- Jangan keluar dari karakter

Jika msg_today >= limit (free: 30):
- Info user limit habis, reset besok jam 00.00 WIB
- Tawarkan upgrade ke PRO

Jika img/video habis:
- Info sisa credit
- Tawarkan beli credit pack: "Ketik /topup untuk beli credit"
```

---

### Step 4 — Tripay Billing Module

#### [NEW] `/home/ubuntu/.hermes/custom_mcp/billing/tripay_client.py`

```python
# Tripay API client
# - create_transaction(telegram_id, product_type) → payment_url
# - verify_callback(data, signature) → bool
# - get_transaction_status(ref) → status
```

#### [NEW] `/home/ubuntu/.hermes/custom_mcp/billing/webhook.py`

FastAPI endpoint `POST /tripay/callback`:
- Verifikasi signature Tripay
- Update `payments` table → status = 'paid'
- Update `users` table → tier + tier_expires
- Atau top-up credits kalau product_type = credit pack

#### [NEW] `/home/ubuntu/.hermes/custom_mcp/billing/products.py`

```python
PRODUCTS = {
  'pro_monthly':    {'name': 'PRO 1 Bulan',        'amount': 39000, 'tier': 'pro',   'days': 30},
  'ultra_monthly':  {'name': 'ULTRA 1 Bulan',       'amount': 79000, 'tier': 'ultra', 'days': 30},
  'img_pack_s':     {'name': 'Image Credit 50',     'amount':  5000, 'credits': {'img': 50}},
  'img_pack_m':     {'name': 'Image Credit 150',    'amount': 12000, 'credits': {'img': 150}},
  'img_pack_l':     {'name': 'Image Credit 500',    'amount': 35000, 'credits': {'img': 500}},
  'video_pack_m':   {'name': 'Video Credit 30',     'amount': 25000, 'credits': {'video': 30}},
  'video_pack_l':   {'name': 'Video Credit 100',    'amount': 70000, 'credits': {'video': 100}},
}
```

---

### Step 5 — Bot Command Handlers

Tambah ke Hermes Telegram platform config:

**`/status`** → tampilkan tier, sisa limit, expiry  
**`/upgrade`** → tampilkan pilihan PRO / ULTRA + link bayar  
**`/topup`** → tampilkan pilihan credit pack + link bayar  
**`/help`** → panduan bot

---

### Step 6 — Modal Video Workers

#### [NEW] `modal/worker_t2v.py`
- `@app.function(gpu="L4", timeout=300)`
- AnimateDiff-Lightning 4-step, 24 frame, 512px
- ffmpeg → MP4
- Upload ke Supabase Storage (bucket: naelvi-videos, public)
- Callback ke VPS

#### [NEW] `modal/worker_i2v.py`
- Same setup, tapi input: image bytes + prompt
- VAE encode image → AnimateDiff img2img

#### [NEW] `/home/ubuntu/.hermes/custom_mcp/video_client.py`
- Panggil Modal worker via HTTP
- Deduct video credit setelah render sukses
- Return video URL ke Hermes → Telegram sendVideo

---

## Build Order

```
[ ] Step 1: Supabase migration (SQL)
[ ] Step 2: MCP tier gate tools + test
[ ] Step 3: SOUL.md update + test gate
[ ] Step 4: Tripay client + webhook server
[ ] Step 5: Bot commands (/upgrade, /topup, /status)
[ ] Step 6: Modal video workers
[ ] Step 7: video_client.py → wire ke MCP
[ ] Step 8: End-to-end test semua tier
```

---

## Verification Plan

```bash
# Step 1–3: Tier gate
# User baru → free tier → coba NSFW → harus ditolak ✓
# User coba video tanpa ultra → ditolak ✓

# Step 4–5: Payment
# /upgrade → dapat link Tripay → bayar (test mode) → tier upgrade ✓
# /topup → credit bertambah ✓

# Step 6–7: Video
# Ultra user request video → dapat MP4 di Telegram ✓
# Credit berkurang ✓

# Semua: tidak ada crash, log bersih
```

---

## Catatan Penting

> [!WARNING]
> SOUL.md punya banyak backup. Sebelum edit, backup dulu ke file baru. Jangan overwrite langsung.

> [!NOTE]
> Tripay perlu daftar dulu (KTP + rekening). Selama proses daftar, Step 4–5 bisa dibuild dulu pakai test mode.

> [!NOTE]
> Video worker Modal: deploy terpisah dari VPS. Butuh `modal token set` dan `modal deploy` dari lokal atau CI.
