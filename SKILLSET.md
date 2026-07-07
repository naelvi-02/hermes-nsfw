# SKILLSET.md — NAELVI Capability Inventory

> Available tools, APIs, models, and integrations. What this system CAN do.

---

## Core Capabilities

### 1. Chat (LLM)

| Skill | Model | Tier | Provider |
|---|---|---|---|
| SFW Conversation | `deepseek/deepseek-chat-v3-0324:free` | FREE | OpenRouter |
| NSFW Conversation | `sao10k/l3.1-70b-hanami-x1` | PRO+ | OpenRouter |
| Fallback NSFW | `sao10k/l3.3-euryale-70b` | PRO+ | OpenRouter |
| Prompt Expansion | Hanami (system prompt) | ALL | OpenRouter |

**Features**:
- Persona-based RP with memory (Hermes memory engine)
- Indonesian + English bilingual
- Mood/intensity parameters
- Streaming responses via Telegram

---

### 2. Image Generation

| Skill | Model | Tier | Provider | Cost |
|---|---|---|---|---|
| SFW Image | Perchance wrapper | FREE | Local VPS | $0 |
| NSFW Image | `RealVisXL_V3.0` | PRO+ | Novita AI | ~$0.004/img |
| NSFW Image (alt) | Additional Novita models | PRO+ | Novita AI | varies |

**Image Features**:
- Txt2img with prompt engineering (Euryale-powered)
- Universal quality tags auto-appended
- Anti-artifact negative prompt
- Custom resolution (default 512×768)
- Img2img support

---

### 3. Video Generation (Planned)

| Skill | Model | Tier | Provider | Est. Cost |
|---|---|---|---|---|
| T2V | AnimateDiff-Lightning + epiCRealism | ULTRA | Modal L4 | ~$0.035/video |
| I2V | AnimateDiff img2img | ULTRA | Modal L4 | ~$0.035/video |

**Video Settings**:
- Resolution: 512×512 / 512×768
- Frames: 24 (standard) / 32 (premium)
- Steps: 4 (standard) / 8 (premium)
- FPS: 8–12
- Duration: ~2–3 seconds
- Output: MP4 (H.264)
- Storage: Cloudflare R2

---

### 4. Payment & Billing (Planned)

| Skill | Provider | Notes |
|---|---|---|
| Payment Gateway | Tripay | QRIS, VA, e-Wallet |
| Subscription | Custom (Supabase) | Monthly recurring |
| Credit Packs | Custom (Supabase) | One-time purchase |
| Webhook Handler | FastAPI on VPS | Tripay callback |

---

### 5. User Management

| Skill | Implementation | Notes |
|---|---|---|
| Tier Management | Supabase `users` table | free/pro/ultra + expiry |
| Usage Tracking | Supabase `usage` table | Daily msg, monthly img/video |
| Credit Balance | Supabase `credits` table | Additive, decrement on use |
| Payment History | Supabase `payments` table | Full audit trail |

---

### 6. Bot Commands

| Command | Function |
|---|---|
| `/start` | Welcome + onboarding |
| `/status` | Tier, usage, credit balance |
| `/upgrade` | PRO/ULTRA subscription links |
| `/topup` | Image/video credit pack purchase |
| `/help` | Usage guide & FAQ |
| `/reset` | Reset conversation context |

---

## Integration Points

### MCP Server Tools

| Tool | Purpose |
|---|---|
| `generate_uncensored_visuals` | Novita NSFW image generation |
| `list_available_models` | List Novita models |
| `get_conversation_context` | Hybrid RP memory |
| `check_user_access` | Tier gate (NEW) |
| `record_usage` | Usage tracking (NEW) |
| `get_user_status` | User summary (NEW) |
| `create_payment_link` | Tripay checkout (NEW) |
| `generate_video_modal` | Modal video dispatch (NEW) |

### External APIs

| API | Endpoint | Auth |
|---|---|---|
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | Bearer token |
| Novita AI | `https://api.novita.ai/v3/async` | API key |
| Tripay | `https://tripay.co.id/api/` | API key + private key |
| Modal | Deployed functions | Token |

---

## Hermes Plugins (Active)

| Plugin | Purpose |
|---|---|
| `nsfw-tools` | NSFW content generation routing |
| `video_gen` | Video generation (stub — needs implementation) |
| `browser` | Web browsing capability |
| `memory` | Long-term user memory |
| `hermes-achievements` | Gamification |
| `image_gen` | Image generation dispatch |

---

## Infrastructure

| Component | Spec | Location |
|---|---|---|
| VPS | Linode 8GB/4CPU | 172.232.232.65 |
| Database | PostgreSQL 15.8 (Supabase) | VPS Docker |
| GPU Compute | Modal L4 (24GB VRAM) | Modal Cloud |
| Video Storage | Cloudflare R2 | Cloud |
| LLM API | OpenRouter | Cloud |
| Image API | Novita AI | Cloud |
| Payment API | Tripay | Cloud |

---

## Languages & Frameworks

| Component | Language | Framework |
|---|---|---|
| Bot Gateway | Python | Hermes Agent |
| MCP Server | Python | `mcp` (stdio) |
| Billing Webhook | Python | FastAPI |
| Modal Workers | Python | Modal SDK |
| Video Encode | Shell | ffmpeg |
| Database | SQL | PostgreSQL (PL/pgSQL) |
