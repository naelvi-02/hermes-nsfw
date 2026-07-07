# AGENTS.md — NAELVI AI Companion Bot

> Auto-loaded by Hermes Agent. Defines project context, constraints, and behavior rules.

---

## Project Identity

**Name**: NAELVI  
**Type**: AI Companion Telegram Bot with persona, avatar, tiered access  
**Stack**: Hermes Agent (gateway) + Custom MCP Server + Supabase + Modal + Tripay  
**Repo**: https://github.com/naelvi-02/hermes-nsfw

---

## Source of Truth

1. `AGENTS.md` (this file) — project rules & constraints
2. `blueprint.md` — full architecture & technical details
3. `implementation_plan.md` — build order & file manifest
4. `market_research.md` — competitor analysis & pricing rationale
5. `handoff.md` — quick reference, credentials, current state
6. VPS: `ssh root@172.232.232.65` — Hermes config, MCP server, Supabase

---

## Architecture Principles

1. **VPS is gateway only** — no heavy compute on VPS. LLM via OpenRouter, images via Novita/Perchance, video via Modal.
2. **Supabase is the single source of truth** — user tier, usage, payments, credits all in `postgres` DB.
3. **MCP tools gate all paid features** — Hermes calls `check_user_access` before NSFW chat/image/video. No bypass.
4. **Model routing by tier** — Free → DeepSeek (free), PRO/ULTRA → Hanami (OpenRouter).
5. **Credit-first deduction** — Purchased credits deducted before monthly allocation.
6. **No cold-start abuse** — Modal worker stays warm 60s. Queue multiple jobs per container.

---

## File Constraints

- **NEVER modify** `SOUL.md` without backup first. Backups in `/root/hermes-rp-backups/`.
- **NEVER modify** existing MCP tools — only ADD new tools to `mcp_server.py`.
- **ALWAYS use** the existing venv at `/home/ubuntu/.hermes/hermes-agent/venv/`.
- **ALWAYS deploy** Modal workers separately via `modal deploy`, not from VPS.

---

## Security Rules

- API keys NEVER hardcoded — use environment variables or Modal secrets
- Tripay webhook MUST verify HMAC signature
- Supabase connection via local Docker network only (127.0.0.1:5432)
- No user data leaves Supabase without encryption
- Telegram Bot Token stored in Hermes config only

---

## Tier Rules (enforced by MCP)

```python
FREE:   chat SFW only (DeepSeek), image SFW only (Perchance), 30 msg/day
PRO:    chat NSFW (Hanami), image NSFW 100/month + credits, no video
ULTRA:  all PRO + image NSFW 300/month + video 30/month + credits
```

---

## Key Paths

| Item | Path |
|---|---|
| MCP Server | `/home/ubuntu/.hermes/custom_mcp/mcp_server.py` |
| Billing Module | `/home/ubuntu/.hermes/custom_mcp/billing/` |
| Hermes Config | `/home/ubuntu/.hermes/hermes-rp-backups/20260701-013604/config.yaml` |
| SOUL.md | `/home/ubuntu/.hermes/hermes-rp-backups/20260701-013604/SOUL.md` |
| Supabase Docker | `/home/ubuntu/supabase/docker/` |
| Modal Workers | `./modal/` (in this repo) |

---

## Known Issues

1. Supabase doesn't auto-start on VPS reboot → `cd /home/ubuntu/supabase/docker && docker compose up -d`
2. No rate limiter on Modal — could drain credits fast
3. Video I2V not tested (AnimateDiff Lightning is T2V-native)
4. No admin dashboard — manual SQL queries for now

---

## Build Order (when resuming)

1. Tripay account registration
2. SQL migration to Supabase
3. MCP tier tools (check_user_access, record_usage, etc.)
4. SOUL.md tier rules injection
5. Tripay client + webhook server
6. Bot commands (/status, /upgrade, /topup)
7. Modal video workers
8. End-to-end testing all tiers
