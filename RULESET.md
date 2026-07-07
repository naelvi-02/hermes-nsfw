# RULESET.md — NAELVI Operational Rules

> Hard constraints, safety rules, and operational procedures. MUST be followed.

---

## 🚫 Hard Constraints

### Content Safety
```
1. SFW-only enforcement for FREE tier — NO exceptions
2. NSFW content ONLY for PRO and ULTRA tier users
3. No illegal content under any tier (zero tolerance)
4. Telegram ToS compliance — no public NSFW groups without age gate
5. Bot operates in private chat / private groups only
```

### Financial Safety
```
1. Modal GPU: $30 credit budget — monitor spending via Modal dashboard
2. Novita API: per-image cost tracked, soft cap enforced
3. OpenRouter: set spending limits in OpenRouter dashboard
4. Tripay: test all transactions in sandbox FIRST
5. No production billing until Tripay webhook verified end-to-end
```

### Data Safety
```
1. Supabase volume MUST be backed up before destructive changes
2. SOUL.md MUST be backed up before ANY edit
3. No user chat logs stored outside Hermes session (ephemeral)
4. Payment data retained for audit (7 years per Indonesian law)
5. No credit card data on VPS — Tripay handles all PCI
```

---

## 📋 Operational Procedures

### Before Every Code Change
```bash
1. Read nearest AGENTS.md
2. Read blueprint.md for architecture context
3. Backup any file you're about to modify (especially SOUL.md)
4. Test change locally or on staging before VPS deploy
```

### After VPS Reboot
```bash
ssh root@172.232.232.65

# Supabase MUST be restarted
cd /home/ubuntu/supabase/docker && docker compose up -d

# Verify
docker ps | grep supabase
docker exec supabase-db psql -U postgres -c 'SELECT 1;'
```

### Before Deploying to VPS
```bash
1. Push to GitHub first
2. SSH to VPS
3. git pull in the relevant directory
4. Restart affected service (Hermes gateway, MCP, webhook)
5. Monitor logs for 5 minutes for errors
```

### Modal Deployment
```bash
cd modal/
modal deploy worker_t2v.py
modal deploy worker_i2v.py

# Check status
modal app list
modal function logs naelvi-video-t2v
```

---

## 💰 Pricing Rules (Approved)

```
SUBSCRIBE:
  PRO  = Rp 39.000/bulan → Tripay product: pro_monthly
  ULTRA = Rp 79.000/bulan → Tripay product: ultra_monthly

CREDIT PACKS:
  Image S (50)    = Rp  5.000
  Image M (150)   = Rp 12.000
  Image L (500)   = Rp 35.000
  Video M (30)    = Rp 25.000
  Video L (100)   = Rp 70.000

DISCOUNT RULES:
  - No auto-discount. Manual only via admin.
  - First-time user onboarding: no discount (focus on free tier value)
```

---

## 🎭 Persona Rules

```
1. Persona identity defined in SOUL.md — NEVER break character
2. Tier rules appended to persona, not replacing it
3. When denying access: stay in persona, be flirtatious/seductive
   Example: "Mmm, you want more of me? Unlock it with PRO, darling... 💋"
4. When offering upgrade: subtle, not pushy. Once per session max.
5. Free tier personality: playful, hinting at "more" behind the paywall
```

---

## 📊 Monitoring Rules

```
ALERTS (check weekly):
  - Modal GPU spending > $20 in $30 credit
  - Novita API calls > expected per PRO user
  - Tripay failed payments > 5%
  - Supabase disk usage > 50%

KPI (monthly review):
  - Free → PRO conversion rate
  - PRO → ULTRA conversion rate
  - Video generation count vs credit usage
  - Average session duration per tier
  - User retention (Day 7, Day 30)
```

---

## 🔒 Access Control

```
TIER              CAN CHAT    CAN IMG    CAN VIDEO
───────────────────────────────────────────────────
FREE              SFW only    SFW only   ❌
PRO               NSFW        NSFW       ❌  
ULTRA             NSFW        NSFW       ✅

ACCESS CHECK FLOW:
  1. Hermes receives user message
  2. Hermes determines intent (chat / image / video)
  3. Hermes calls MCP tool: check_user_access(telegram_id, action)
  4. If allowed=true → proceed
  5. If allowed=false → deny with persona-appropriate message
  6. After success → record_usage(telegram_id, action)
```

---

## 🛑 Stop Conditions

```
DO NOT PROCEED if:
  - Supabase is down (data integrity at risk)
  - Modal credit exhausted (unexpected charges)
  - Tripay API key not configured (billing failure)
  - SOUL.md corrupted or missing backup
  - Telegram Bot Token invalid
  - Database migration conflicts with existing schema
```

---

## 🔄 Recovery Procedures

### Supabase Down
```bash
cd /home/ubuntu/supabase/docker && docker compose up -d
# Wait 30 seconds
docker exec supabase-db psql -U postgres -c 'SELECT 1;'
```

### Hermes Gateway Crash
```bash
ssh root@172.232.232.65
# Check logs
journalctl -u hermes-gateway -n 100
# Restart
systemctl restart hermes-gateway
# Or manually
su - ubuntu -c 'cd /home/ubuntu/.hermes && nohup hermes gateway run &'
```

### Payment Webhook Failure
```bash
# Check webhook logs
ssh root@172.232.232.65
tail -f /home/ubuntu/.hermes/custom_mcp/billing/webhook.log

# Manual payment reconciliation:
SELECT * FROM payments WHERE status='pending' AND created_at > NOW() - INTERVAL '1 hour';
# Cross-reference with Tripay dashboard
```

### Video Render Failure
```bash
# Check Modal logs
modal function logs naelvi-video-t2v --tail 50

# Check failed jobs in DB
SELECT * FROM video_jobs WHERE status='failed' ORDER BY created_at DESC LIMIT 10;
# Re-queue manually if needed
```

---

## 📝 Change Log Rules

```
1. Every significant change → update blueprint.md "Last Updated"
2. Every schema change → update migration.sql + version number
3. Every pricing change → update this file + market_research.md
4. Every new tool → update SKILLSET.md MCP tools section
5. Version format: YYYY.MM.DD.BUILD (e.g., 2026.07.07.01)
```
