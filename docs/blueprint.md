# NAELVI — AI Companion Bot Blueprint

> **Last updated**: 2026-07-07 (08:13 WIB)  
> **Status**: Pre-MVP — tier/billing + video belum dibangun. Supabase ✅ nyala.  
> **VPS**: Linode 8GB/4CPU, Jakarta, SSH `root@172.232.232.65`
> **DB Password**: (stored in `/home/ubuntu/supabase/docker/.env`)

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                       TELEGRAM USER                               │
│              kirim teks / image / perintah                        │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              VPS (Linode 8GB — 172.232.232.65)                    │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Hermes Agent │  │ MCP Server   │  │ Supabase (self-hosted)  │ │
│  │ (gateway)    │  │ (custom MCP) │  │ • tier/user DB          │ │
│  │ • Telegram   │  │ • tier gate  │  │ • payment log           │ │
│  │ • Discord    │  │ • Novita img │  │ • usage tracking        │ │
│  │ • CLI        │  │ • Perchance  │  └─────────────────────────┘ │
│  └──────┬───────┘  └──────┬───────┘                               │
│         │                 │                                        │
│         │    ┌────────────┴────────────┐                          │
│         │    │  billing/ (NEW)         │                          │
│         │    │  • tripay_client.py     │                          │
│         │    │  • webhook.py           │                          │
│         │    │  • products.py          │                          │
│         │    └─────────────────────────┘                          │
│         │                 │                                        │
└─────────┼─────────────────┼────────────────────────────────────────┘
          │                 │
          ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│  OpenRouter API  │  │  Tripay API      │
│  • Hanami (PRO+) │  │  • QRIS          │
│  • DeepSeek (free)│  │  • Virtual Acc   │
└──────────────────┘  │  • e-Wallet      │
                      └──────────────────┘

┌──────────────────┐  ┌──────────────────┐
│  Novita AI       │  │  Modal (GPU)      │
│  • Image NSFW    │  │  • T2V: Animate-  │
│  • RealVisXL     │  │    Diff-Lightning │
└──────────────────┘  │  • I2V: img2img   │
                      │  • L4 GPU         │
                      │  • ffmpeg → MP4   │
                      └──────────────────┘
```

---

## 2. Infrastructure Inventory

### 2.1 VPS (Linode — 172.232.232.65)

| Resource | Spec | Usage |
|---|---|---|
| CPU | 4 vCPU | ~30% normal load |
| RAM | 8 GB | ~4 GB used |
| Disk | 157 GB | 43 GB used (107 GB free) |
| OS | Ubuntu 24.04 x86_64 | Kernel 6.8 |
| Swap | 4.5 GB | 2.3 GB used |

### 2.2 Running Services

| Service | Process | Status | Port |
|---|---|---|---|
| Hermes Gateway | `hermes_cli.main gateway run` | ✅ Running | — |
| Hermes MCP | `custom_mcp/mcp_server.py` (2 instances) | ✅ Running | stdio |
| Perchance API | `perchance-wrapper/api.py` | ✅ Running | — |
| Autoclaw Proxy | Docker container | ✅ Running | 8070 |
| Autoclaw Dashboard | Docker container | ✅ Running | 1431 |
| Supabase | Docker compose | ✅ **UP** | 5432, 8100 |

> [!IMPORTANT]
> **Supabase di `/home/ubuntu/supabase/docker/`.** Setelah VPS reboot, jalankan:
> ```bash
> cd /home/ubuntu/supabase/docker && docker compose up -d
> ```

### 2.3 External Services & API Keys

| Service | Key Location | Notes |
|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` env di MCP | (stored in VPS env) |
| Novita AI | `NOVITA_API_KEY` env di MCP | (stored in VPS env) |
| Modal | Butuh daftar + token | $30 credit |
| Tripay | **Belum daftar** | Butuh KTP + rekening |
| Supabase Storage | **Active** (bucket: naelvi-videos, public, 100MB, mp4 only) | Untuk video storage |

### 2.4 Model Configuration

| Purpose | Model | Source | Cost |
|---|---|---|---|
| Free chat | `deepseek/deepseek-chat-v3-0324:free` | OpenRouter | $0 |
| PRO chat | `sao10k/l3.1-70b-hanami-x1` | OpenRouter | per-token |
| Fallback | `sao10k/l3.3-euryale-70b` | OpenRouter | per-token |
| Image NSFW | `RealVisXL_V3.0` | Novita | ~$0.004/img |
| Image SFW | Perchance | Local wrapper | $0 |

---

## 3. Tier & Pricing System

### 3.1 Tier Definitions

```
FREE          Rp 0/bulan
├─ Model: deepseek/deepseek-chat-v3-0324:free
├─ Chat SFW only
├─ Image SFW unlimited (Perchance)
├─ Limit: 30 pesan/hari
└─ Tidak bisa NSFW

PRO           Rp 39.000/bulan
├─ Model: sao10k/l3.1-70b-hanami-x1
├─ Chat NSFW unlimited
├─ Image NSFW: 100 img/bulan (included)
├─ Bisa beli image credit tambahan
└─ Tidak bisa video

ULTRA         Rp 79.000/bulan
├─ Semua hak PRO
├─ Image NSFW: 300 img/bulan (included)
├─ Video NSFW: 30 credit/bulan (included)
└─ Bisa beli image + video credit tambahan
```

### 3.2 Credit Packs

```
IMAGE CREDIT
  S: 50 img   = Rp  5.000  (Rp 100/img)
  M: 150 img  = Rp 12.000  (Rp  80/img)
  L: 500 img  = Rp 35.000  (Rp  70/img)

VIDEO CREDIT (ULTRA only atau dibeli lepas)
  M: 30 video  = Rp 25.000  (Rp 833/video)
  L: 100 video = Rp 70.000  (Rp 700/video)
```

### 3.3 Per-User Cost Breakdown

| Tier | LLM Cost | Image Cost | Video Cost | Infra | Total HPP | Margin |
|---|---|---|---|---|---|---|
| FREE | $0 | $0 | $0 | ~$0.24 | ~$0.24 | N/A |
| PRO | ~$1.00 | ~$0.40 | $0 | ~$0.24 | ~$1.64 | ~58% |
| ULTRA | ~$1.00 | ~$1.20 | ~$1.80 | ~$0.24 | ~$4.24 | ~28% |

---

## 4. Database Schema (Supabase)

### 4.1 Tables

```sql
-- ============================================================
-- TABLE: users — Core user identity and tier
-- ============================================================
CREATE TABLE users (
    telegram_id    BIGINT PRIMARY KEY,
    username       TEXT,
    display_name   TEXT,
    tier           TEXT NOT NULL DEFAULT 'free',   
                    -- 'free' | 'pro' | 'ultra'
    tier_expires   TIMESTAMPTZ,
                    -- NULL for free tier = never expires
    persona_id     TEXT,
                    -- active persona UUID if multiple personas exist
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: usage — Daily/monthly usage tracking
-- ============================================================
CREATE TABLE usage (
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    period_start   DATE NOT NULL DEFAULT CURRENT_DATE,
    msg_count      INT NOT NULL DEFAULT 0,
    img_count      INT NOT NULL DEFAULT 0,
    video_count    INT NOT NULL DEFAULT 0,
    PRIMARY KEY (telegram_id, period_start)
);

-- ============================================================
-- TABLE: credits — Purchased credit balance (additive)
-- ============================================================
CREATE TABLE credits (
    telegram_id    BIGINT PRIMARY KEY REFERENCES users(telegram_id),
    img_credits    INT NOT NULL DEFAULT 0,
    video_credits  INT NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: payments — Transaction log
-- ============================================================
CREATE TABLE payments (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    tripay_ref     TEXT UNIQUE,
                    -- Tripay merchant reference
    product_type   TEXT NOT NULL,
                    -- pro_monthly | ultra_monthly | img_pack_s | img_pack_m | 
                    -- img_pack_l | video_pack_m | video_pack_l
    amount_idr     INT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
                    -- 'pending' | 'paid' | 'expired' | 'failed'
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at        TIMESTAMPTZ,
    raw_callback   JSONB
                    -- Store raw Tripay callback for audit
);

-- ============================================================
-- TABLE: video_jobs — Modal render job tracking
-- ============================================================
CREATE TABLE video_jobs (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id    BIGINT NOT NULL REFERENCES users(telegram_id),
    type           TEXT NOT NULL,          -- 't2v' | 'i2v'
    prompt         TEXT NOT NULL,
    input_image_url TEXT,
                    -- Only for I2V
    modal_job_id   TEXT,
    status         TEXT NOT NULL DEFAULT 'queued',
                    -- 'queued' | 'rendering' | 'encoding' | 'done' | 'failed'
    output_url     TEXT,
    error_message  TEXT,
    cost_estimate  NUMERIC(6,4),
                    -- Estimated cost in USD
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMPTZ
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_usage_period ON usage(period_start);
CREATE INDEX idx_payments_telegram ON payments(telegram_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_video_jobs_telegram ON video_jobs(telegram_id);
CREATE INDEX idx_users_tier ON users(tier);
```

### 4.2 Key Functions

```sql
-- Get or create usage row for today
CREATE OR REPLACE FUNCTION get_or_create_usage(
    p_telegram_id BIGINT
) RETURNS usage AS $$
DECLARE
    v_row usage;
BEGIN
    INSERT INTO usage (telegram_id, period_start)
    VALUES (p_telegram_id, CURRENT_DATE)
    ON CONFLICT (telegram_id, period_start) DO NOTHING;
    
    SELECT * INTO v_row FROM usage 
    WHERE telegram_id = p_telegram_id 
    AND period_start = CURRENT_DATE;
    
    RETURN v_row;
END;
$$ LANGUAGE plpgsql;

-- Check if user can perform action
CREATE OR REPLACE FUNCTION check_user_access(
    p_telegram_id BIGINT,
    p_action TEXT  -- 'msg' | 'img_nsfw' | 'video'
) RETURNS TABLE(allowed BOOLEAN, reason TEXT, remaining INT) AS $$
DECLARE
    v_user users%ROWTYPE;
    v_usage usage%ROWTYPE;
    v_credits credits%ROWTYPE;
    v_msg_limit INT := 30;  -- free tier daily limit
BEGIN
    -- Get user (create if new)
    INSERT INTO users (telegram_id) VALUES (p_telegram_id)
    ON CONFLICT (telegram_id) DO NOTHING;
    SELECT * INTO v_user FROM users WHERE telegram_id = p_telegram_id;
    
    -- Get today's usage
    SELECT * INTO v_usage FROM get_or_create_usage(p_telegram_id);
    
    CASE p_action
        WHEN 'msg' THEN
            IF v_user.tier = 'free' AND v_usage.msg_count >= v_msg_limit THEN
                allowed := false;
                reason := 'Daily message limit reached. Upgrade to PRO for unlimited.';
                remaining := 0;
            ELSE
                allowed := true;
                reason := 'OK';
                remaining := CASE WHEN v_user.tier = 'free' 
                    THEN v_msg_limit - v_usage.msg_count 
                    ELSE 999999 END;
            END IF;
            
        WHEN 'img_nsfw' THEN
            -- Free tier: no NSFW
            IF v_user.tier = 'free' THEN
                allowed := false;
                reason := 'NSFW image requires PRO subscription.';
                remaining := 0;
                RETURN NEXT;
                RETURN;
            END IF;
            
            -- Check credits first, then monthly allocation
            SELECT * INTO v_credits FROM credits 
            WHERE telegram_id = p_telegram_id;
            
            IF COALESCE(v_credits.img_credits, 0) > 0 THEN
                allowed := true;
                reason := 'Using credit balance';
                remaining := v_credits.img_credits - 1;
            ELSIF v_user.tier = 'pro' AND v_usage.img_count < 100 THEN
                allowed := true;
                reason := 'Using monthly allocation';
                remaining := 99 - v_usage.img_count;
            ELSIF v_user.tier = 'ultra' AND v_usage.img_count < 300 THEN
                allowed := true;
                reason := 'Using monthly allocation';
                remaining := 299 - v_usage.img_count;
            ELSE
                allowed := false;
                reason := 'Monthly image limit reached. Buy credit pack with /topup';
                remaining := 0;
            END IF;
            
        WHEN 'video' THEN
            IF NOT (v_user.tier = 'ultra') THEN
                allowed := false;
                reason := 'Video generation requires ULTRA subscription.';
                remaining := 0;
                RETURN NEXT;
                RETURN;
            END IF;
            
            SELECT * INTO v_credits FROM credits 
            WHERE telegram_id = p_telegram_id;
            
            -- Combined: monthly + purchased credits
            remaining := COALESCE(v_credits.video_credits, 0) + 
                CASE WHEN v_usage.video_count < 30 
                    THEN 30 - v_usage.video_count ELSE 0 END;
            
            IF remaining > 0 THEN
                allowed := true;
                reason := CASE WHEN v_credits.video_credits > 0 
                    THEN 'Using video credit' ELSE 'Using monthly allocation' END;
                remaining := remaining - 1;
            ELSE
                allowed := false;
                reason := 'Video credits exhausted. Buy more with /topup';
            END IF;
    END CASE;
    
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Record usage after successful action
CREATE OR REPLACE FUNCTION record_action(
    p_telegram_id BIGINT,
    p_action TEXT  -- 'msg' | 'img' | 'video'
) RETURNS BOOLEAN AS $$
DECLARE
    v_credits credits%ROWTYPE;
    v_usage usage%ROWTYPE;
BEGIN
    SELECT * INTO v_usage FROM get_or_create_usage(p_telegram_id);
    
    CASE p_action
        WHEN 'msg' THEN
            UPDATE usage SET msg_count = msg_count + 1
            WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
            
        WHEN 'img' THEN
            -- Deduct from credits first
            SELECT * INTO v_credits FROM credits 
            WHERE telegram_id = p_telegram_id;
            
            IF COALESCE(v_credits.img_credits, 0) > 0 THEN
                UPDATE credits SET img_credits = img_credits - 1,
                    updated_at = NOW()
                WHERE telegram_id = p_telegram_id;
            ELSE
                UPDATE usage SET img_count = img_count + 1
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
            END IF;
            
        WHEN 'video' THEN
            SELECT * INTO v_credits FROM credits 
            WHERE telegram_id = p_telegram_id;
            
            IF COALESCE(v_credits.video_credits, 0) > 0 THEN
                UPDATE credits SET video_credits = video_credits - 1,
                    updated_at = NOW()
                WHERE telegram_id = p_telegram_id;
            ELSE
                UPDATE usage SET video_count = video_count + 1
                WHERE telegram_id = p_telegram_id AND period_start = CURRENT_DATE;
            END IF;
    END CASE;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## 5. MCP Server — Tool API Contracts

### 5.1 File: `/home/ubuntu/.hermes/custom_mcp/mcp_server.py`

#### Existing tools (unchanged):

| Tool | Signature | Purpose |
|---|---|---|
| `generate_uncensored_visuals` | `(prompt, negative_prompt?, width?, height?, steps?)` | Novita NSFW image gen |
| `list_available_models` | `()` | List Novita models |
| `get_conversation_context` | `()` | Hybrid history for RP |

#### NEW tools (to be added):

```
┌─────────────────────────────────────────────────────────────────┐
│ check_user_access                                               │
├─────────────────────────────────────────────────────────────────┤
│ INPUT:  telegram_id: int, action: "msg" | "img_nsfw" | "video" │
│ OUTPUT: { allowed: bool, reason: str, remaining: int }         │
│ DESC:   Called BEFORE action. Returns whether user can proceed. │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ record_usage                                                    │
├─────────────────────────────────────────────────────────────────┤
│ INPUT:  telegram_id: int, action: "msg" | "img" | "video"      │
│ OUTPUT: { ok: bool }                                            │
│ DESC:   Called AFTER successful action. Updates counters.       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ get_user_status                                                 │
├─────────────────────────────────────────────────────────────────┤
│ INPUT:  telegram_id: int                                        │
│ OUTPUT: {                                                       │
│   tier: str,                                                    │
│   tier_expires: str (ISO date),                                 │
│   msg_today: int, msg_limit: int,                               │
│   img_this_month: int, img_limit: int,                          │
│   video_this_month: int, video_limit: int,                      │
│   img_credits: int, video_credits: int                          │
│ }                                                               │
│ DESC:   /status command. Full user summary.                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ create_payment_link                                             │
├─────────────────────────────────────────────────────────────────┤
│ INPUT:  telegram_id: int, product_type: str                     │
│ OUTPUT: { payment_url: str, ref: str, amount: int }             │
│ DESC:   /upgrade and /topup. Creates Tripay transaction.        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ generate_video_modal (NEW)                                      │
├─────────────────────────────────────────────────────────────────┤
│ INPUT:  telegram_id: int, prompt: str,                          │
│         type: "t2v" | "i2v", image_url?: str                   │
│ OUTPUT: { job_id: str, status: "queued", eta_seconds: int }     │
│ DESC:   Submits job to Modal. Checks access first.              │
└─────────────────────────────────────────────────────────────────┘
```

#### Database connection helper:

```python
# Reuse existing Supabase — connect via local port 5432
# Schema: public (default)
# Auth: supabase service_role key

import psycopg2
SUPABASE_URL = "http://127.0.0.1:5432"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
```

---

## 6. Billing System (Tripay)

### 6.1 Tripay Account Setup

> [!IMPORTANT]
> **TODO**: Daftar di [tripay.co.id](https://tripay.co.id)
> 
> Requirements:
> - KTP (WNA bisa pakai paspor)
> - Rekening bank (settlement)
> - Website URL (bisa pakai placeholder bot Telegram)
> 
> Setelah daftar dapat:
> - `TRIPAY_API_KEY`
> - `TRIPAY_MERCHANT_CODE`
> - `TRIPAY_PRIVATE_KEY` (untuk verifikasi webhook)

### 6.2 Webhook Flow

```
User kirim /upgrade pro
  → Hermes panggil create_payment_link(telegram_id, "pro_monthly")
  → MCP panggil Tripay API: POST /transaction/create
  → Tripay return payment_url + reference
  → Hermes kirim payment_url ke user via Telegram

User bayar (QRIS / VA / e-wallet)
  → Tripay POST ke webhook: VPS:8080/tripay/callback
  → webhook.py verifikasi signature (private_key + HMAC)
  → Update payments.status = 'paid'
  → Update users.tier = 'pro', users.tier_expires = NOW() + 30 days
  → Reply user: "✅ Upgrade sukses! Sekarang kamu PRO."

  → Kalau topup:
  → Update credits.img_credits atau video_credits
  → Reply user: "✅ Credit ditambahkan!"
```

### 6.3 Webhook Server

```python
# File: /home/ubuntu/.hermes/custom_mcp/billing/webhook.py

from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib

app = FastAPI()

@app.post("/tripay/callback")
async def tripay_callback(request: Request):
    data = await request.json()
    
    # Verify callback signature
    callback_event = request.headers.get("X-Callback-Event")
    callback_signature = request.headers.get("X-Signature")
    
    computed = hmac.new(
        TRIPAY_PRIVATE_KEY.encode(),
        json.dumps(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    if computed != callback_signature:
        raise HTTPException(403, "Invalid signature")
    
    if data.get("status") != "PAID":
        return {"ok": True}
    
    # Process in database...
    # update_users_tier(data["merchant_ref"])
    
    return {"ok": True}
```

---

## 7. Video Generation Pipeline (Modal)

### 7.1 Modal Setup

```bash
# Install Modal CLI
pip install modal

# Auth
modal token set --token-id <ID> --token-secret <SECRET>

# Deploy
cd modal/
modal deploy worker_t2v.py
modal deploy worker_i2v.py
```

### 7.2 Video Worker Config

```python
# modal/worker_t2v.py

import modal

app = modal.App("naelvi-video-t2v")
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

# 1 TiB volume = free on Modal Starter

image = (
    modal.Image.debian_slim()
    .pip_install("diffusers", "transformers", "accelerate", "torch")
    .run_commands(
        # Model download happens once during build
        "python -c 'from diffusers import AnimateDiffPipeline; "
        "pipeline = AnimateDiffPipeline.from_pretrained(...)' "
    )
)

@app.function(
    gpu="L4",
    image=image,
    volumes={"/models": volume},
    timeout=300,        # 5 min max render time
    container_idle_timeout=60  # Stay warm for 60s after last job
)
@modal.web_endpoint(method="POST")
async def generate_t2v(request):
    """
    POST /generate
    Body: { prompt, steps: 4, width: 512, height: 512, frames: 24, chat_id }
    
    Returns: { status, video_url, job_id }
    """
    ...

@app.function(
    gpu="L4",
    image=image,
    volumes={"/models": volume},
    timeout=300,
    container_idle_timeout=60
)
@modal.web_endpoint(method="POST")
async def generate_i2v(request):
    """
    POST /generate-i2v
    Body: { prompt, image_url, steps: 4, width: 512, height: 512, frames: 24, chat_id }
    
    Returns: { status, video_url, job_id }
    """
    ...

@app.function(
    image=image,
    volumes={"/models": volume},
    schedule=modal.Cron("0 */6 * * *")  # Every 6 hours
)
def cleanup_old_outputs():
    """Delete output files older than 1 hour from Supabase Storage naelvi-videos bucket."""
    ...
```

### 7.3 Video Settings

| Parameter | Free/Preview | Standard | Premium |
|---|---|---|---|
| GPU | — | L4 | L4 |
| Resolution | — | 512×512 | 512×768 |
| Frames | — | 24 | 32 |
| Steps | — | 4 | 8 |
| FPS | — | 8 | 12 |
| Duration | — | ~3 detik | ~2.7 detik |
| Est. cost | — | ~$0.035 | ~$0.085 |

### 7.4 ffmpeg Encode

```python
# In Modal worker, after getting frame tensors:
import subprocess, tempfile

def frames_to_mp4(frames: list, output_path: str, fps: int = 8):
    """Convert PIL frames to MP4 via ffmpeg pipe."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{frames[0].width}x{frames[0].height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for frame in frames:
        process.stdin.write(np.array(frame).tobytes())
    process.stdin.close()
    process.wait()
```

---

## 8. System Prompt (SOUL.md) Rules

### 8.1 Tier Gate Rules (insert at top)

```markdown
## TIER RULES (Wajib diikuti tanpa pengecualian)

Sebelum chat NSFW, generate NSFW image, atau video:
1. Panggil tool `check_user_access` dengan telegram_id user
2. Jika allowed=false: tolak SOPAN dalam karakter persona + tawarkan upgrade
3. Setelah aksi sukses: panggil `record_usage`

### Free Tier (default user baru)
- Model chat: DeepSeek via OpenRouter
- HANYA SFW chat
- Image: SFW via Perchance
- Max 30 pesan/hari
- Jika minta NSFW → tolak + tawarkan PRO

### PRO Tier
- Model chat: Hanami
- NSFW chat: UNLIMITED
- Image NSFW: 100/bulan + credit tambahan
- Tidak bisa video
- Jika minta video → tawarkan ULTRA

### ULTRA Tier
- Model chat: Hanami
- Semua hak PRO
- Image NSFW: 300/bulan + credit tambahan
- Video: 30/bulan + credit tambahan
```

---

## 9. Bot Commands

| Command | Tier | Description |
|---|---|---|
| `/start` | All | Welcome message + first-time setup |
| `/status` | All | Tier, usage stats, credit balance |
| `/upgrade` | All | Tampilkan pilihan PRO / ULTRA + Tripay link |
| `/topup` | PRO+ | Tampilkan pilihan image/video credit pack |
| `/help` | All | Panduan + FAQ |
| `/reset` | All | Reset conversation context |

---

## 10. File Manifest

### Existing Files (JANGAN DIHAPUS)

```
/home/ubuntu/.hermes/
├── custom_mcp/
│   ├── mcp_server.py           ← MODIFY: tambah 5 tools tier
│   ├── img2img_direct.py
│   └── billing/                 ← NEW: folder
├── perchance_api.py
├── hermes-agent/               ← Hermes source
│   └── venv/
└── skills/

/root/hermes-rp-backups/20260701-013604/
├── SOUL.md                     ← MODIFY: tambah tier rules
├── config.yaml
├── plugins/
│   ├── nsfw-tools/
│   └── video_gen/              ← empty stub
└── env
```

### New Files to Create

```
/home/ubuntu/.hermes/custom_mcp/
├── billing/
│   ├── __init__.py
│   ├── tripay_client.py        ← Tripay API wrapper
│   ├── webhook.py              ← FastAPI callback receiver
│   └── products.py             ← Product definitions

/modal/
├── worker_t2v.py               ← Modal T2V function
├── worker_i2v.py               ← Modal I2V function
├── common.py                   ← Shared: model load, ffmpeg, upload

C:\Users\naufa\...
└── supabase/
    └── migration.sql           ← Database migration script
```

---

## 11. Deployment Procedures

### 11.1 Restart Supabase After VPS Reboot

```bash
# Confirmed location: /home/ubuntu/supabase/docker/
# Volume data preserved in: supabase_db-config
# DB password: (stored in .env file)

ssh root@172.232.232.65
cd /home/ubuntu/supabase/docker
docker compose up -d

# Verify (~30 detik untuk semua container healthy)
docker ps | grep supabase
# Expect: supabase-db, supabase-kong, supabase-rest, etc.

# Test DB connection
docker exec supabase-db psql -U postgres -c 'SELECT version();'
```

### 11.2 Deploy Modal Workers

```bash
# From your dev machine (or VPS)
pip install modal
cd /path/to/modal/

# One-time auth
modal token set --token-id $MODAL_TOKEN_ID --token-secret $MODAL_TOKEN_SECRET

# Deploy
modal deploy worker_t2v.py
modal deploy worker_i2v.py
```

### 11.3 Start Webhook Server

```bash
ssh root@172.232.232.65
mkdir -p /home/ubuntu/.hermes/custom_mcp/billing/
cd /home/ubuntu/.hermes/custom_mcp/billing/

# Using existing venv
source /home/ubuntu/.hermes/hermes-agent/venv/bin/activate
pip install fastapi uvicorn psycopg2-binary

# Run as background service (note: port 8080 may conflict — use 8088 or check)
nohup uvicorn webhook:app --host 0.0.0.0 --port 8088 > webhook.log 2>&1 &
```

### 11.4 Database Migration

```bash
# Via docker exec (psql not installed on VPS host)
cd /home/ubuntu/supabase/docker
# Copy migration file to container
docker cp /path/to/migration.sql supabase-db:/tmp/migration.sql
# Run
docker exec supabase-db psql -U postgres -d postgres -f /tmp/migration.sql
# Or pipe directly
cat /path/to/migration.sql | docker exec -i supabase-db psql -U postgres -d postgres

# Verify tables
docker exec supabase-db psql -U postgres -d postgres -c "\dt"
# Expect: users, usage, credits, payments, video_jobs
```

---

## 12. Testing Checklist

### Phase 1: Tier Gate (no payment needed)

- [ ] User baru auto-created as `free` on first interaction
- [ ] Free user coba NSFW chat → MCP tolak, Hermes tawarkan upgrade
- [ ] Free user coba generate NSFW image → MCP tolak
- [ ] Free user coba generate video → MCP tolak
- [ ] Free user chat SFW → jalan normal (DeepSeek)
- [ ] Free user generate SFW image → Perchance jalan normal
- [ ] Manually set user to `pro` in DB → NSFW chat + image jalan
- [ ] PRO user coba video → tolak
- [ ] Manually set user to `ultra` → video jalan

### Phase 2: Billing (Tripay sandbox)

- [ ] `/upgrade` → dapat link bayar
- [ ] Bayar via Tripay sandbox → webhook diterima
- [ ] Payment di DB diupdate → `paid`
- [ ] User tier otomatis upgrade
- [ ] `/status` → tampilkan tier baru
- [ ] `/topup` → beli credit → credit bertambah
- [ ] Credit digunakan (img/video) → credit berkurang

### Phase 3: Video (Modal)

- [ ] ULTRA user request video T2v → Modal worker jalan
- [ ] Video selesai → terkirim di Telegram
- [ ] I2V: user kirim gambar + caption → video generated
- [ ] Credit terdeduct
- [ ] Video junk/error → graceful error message ke user
- [ ] Modal dashboard: cost tracking akurat

### Phase 4: Edge Cases

- [ ] User nggak aktif 30 hari → tier expire → downgrade ke free
- [ ] User sudah PRO, beli ULTRA → langsung upgrade (tidak double stack)
- [ ] Tripay timeout → payment status = 'expired', user tetap free
- [ ] Supabase down → MCP tools error gracefully, tidak crash Hermes
- [ ] User spam /upgrade → tidak bikin duplicate payment link

---

## 13. Environment Variables

```bash
# === VPS (add to /home/ubuntu/.hermes/custom_mcp/.env) ===

# Supabase (self-hosted)
SUPABASE_DB_HOST=127.0.0.1
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASS=(stored in /home/ubuntu/supabase/docker/.env)

# Tripay
TRIPAY_API_KEY=
TRIPAY_MERCHANT_CODE=
TRIPAY_PRIVATE_KEY=
TRIPAY_API_URL=https://tripay.co.id/api-sandbox/

# OpenRouter (existing, already in env)
OPENROUTER_API_KEY=(stored in VPS env)

# Novita (existing, already in env)
NOVITA_API_KEY=(stored in VPS env)

# === Modal (in Modal secrets, not VPS) ===

MODAL_TOKEN_ID=
MODAL_TOKEN_SECRET=
SUPABASE_STORAGE_BUCKET=naelvi-videos
SUPABASE_URL=http://172.232.232.65:8000
SUPABASE_SERVICE_KEY=
```

---

## 14. Known Issues & Future Work

| Issue | Priority | Notes |
|---|---|---|
| Supabase no auto-restart | 🔴 High | Cari docker-compose path, add systemd unit |
| Video I2V not tested | 🟡 Medium | AnimateDiff Lightning doesn't natively do I2V — need img2img trick |
| No rate limiter | 🟡 Medium | Bisa abuse Modal credits |
| No admin dashboard | 🟢 Low | Manual SQL query for now |
| Persona system not built | 🟢 Low | Next iteration after billing works |
| Marketing / user acquisition | 🟢 Low | Focus: make product work first |

---

## 15. Key Contacts & Links

| Item | Link / Value |
|---|---|
| VPS SSH | `ssh root@172.232.232.65` |
| Hermes config | [config.yaml](file:///home/ubuntu/.hermes/hermes-rp-backups/20260701-013604/config.yaml) |
| SOUL.md (persona) | [SOUL.md](file:///home/ubuntu/.hermes/hermes-rp-backups/20260701-013604/SOUL.md) |
| MCP server | [mcp_server.py](file:///home/ubuntu/.hermes/custom_mcp/mcp_server.py) |
| Modal pricing | https://modal.com/pricing |
| Tripay docs | https://tripay.co.id/developer |
| OpenRouter models | https://openrouter.ai/models |
| Novita console | https://novita.ai/console |
