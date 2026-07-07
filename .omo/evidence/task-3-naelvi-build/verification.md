# W1.3 — SOUL.md TIER RULES injection

## Status: ✅ DONE

## What was done

1. **Backup FIRST** (mandatory per AGENTS.md / W1.3 plan)
   - Created `/root/hermes-rp-backups/20260707-161025-tier-rules-LIVE/SOUL.md.bak` (11287 bytes, identical to pre-edit LIVE)
   - Created `/root/hermes-rp-backups/20260707-161025-tier-rules-LIVE/tier_rules_diff.patch` (719 bytes)
   - Also created `/root/hermes-rp-backups/20260707-160559-tier-rules/SOUL.md.bak` (initial mis-edit on backup dir, reverted)

2. **Identified LIVE SOUL.md** at `/home/ubuntu/.hermes/SOUL.md` (245 lines, 11287 bytes)
   - NOT the snapshot at `/root/hermes-rp-backups/20260701-013604/SOUL.md` (that's a backup, not used by gateway)
   - Other SOUL.md files exist: `/root/.hermes/SOUL.md` (513B stub), `/opt/hermes-code/hermes-agent/docker/SOUL.md`, `/var/lib/hermes-code/SOUL.md` (hermes-code service, separate)

3. **Injected TIER RULES section** via `inject_tier_rules_live.py` (Python pathlib read+insert+write)
   - Idempotency check: skip if `## TIER RULES (WAJIB DIIKUTI)` already present
   - Insertion point: after `# SOUL.md - Elara Valerina Core` title + blank line
   - Content: per implementation_plan.md:128-149
     - chat NSFW → action: chat_nsfw
     - generate image NSFW → action: img_nsfw
     - generate video → action: video
     - allowed=false → reject in persona + offer /upgrade + stay in character
     - msg_today >= limit (free: 30) → info reset 00:00 WIB + offer PRO
     - img/video habis → info credit + offer /topup
   - 245 → 267 lines (+22 TIER RULES + separator)
   - 11238 → 11803 bytes

4. **Reverted mistaken backup-dir edit**: snapshot `/root/hermes-rp-backups/20260701-013604/SOUL.md` restored from `.bak` (back to 245 lines, pristine pre-TIER-RULES state).

5. **Restarted Hermes gateway**
   - Service: `hermes-gateway.service` (systemd user unit, ubuntu user)
   - Command: `sudo -u ubuntu XDG_RUNTIME_DIR=/run/user/1001 systemctl --user restart hermes-gateway.service`
   - First start failed (exit 1, normal `--replace` semantics — old PID 3623109 still alive during takeover), systemd auto-restarted → new PID 1539879 active running 16:12:13 WIB
   - MCP children spawned: PID 1540048 (`mcp_server.py`), PID 1540050 (`python3 mcp_server.py`)
   - Memory 115.0M, CPU 2.651s, no journal errors post-restart

## Acceptance criteria verified

| AC | Status |
|---|---|
| Backup dir exists with SOUL.md.bak | ✅ `/root/hermes-rp-backups/20260707-161025-tier-rules-LIVE/SOUL.md.bak` |
| diff shows ONLY TIER RULES added | ✅ patch file 719 bytes, 22 line additions, no other changes |
| Hermes restart succeeds | ✅ PID 1539879 active, 2 MCP children spawned |
| No journal errors post-restart | ✅ clean since 16:12:13 |

## Must-NOT guardrails verified

- ✅ Backup created BEFORE edit (mandatory per AGENTS.md)
- ✅ Only TIER RULES section added — original content (CRITICAL TOOL OUTPUT RULE, VISUAL GENERATION ROUTING, persona rules, TRIGGER WORDS) untouched
- ✅ Did NOT modify existing MCP tools (W1.3 only touches SOUL.md)
- ✅ Live SOUL.md identified correctly (not the snapshot)
- ✅ Snapshot backup dir `/root/hermes-rp-backups/20260701-013604/` restored to pristine state

## Files touched on VPS

- `/home/ubuntu/.hermes/SOUL.md` (LIVE, edited +22 lines)
- `/root/hermes-rp-backups/20260707-161025-tier-rules-LIVE/SOUL.md.bak` (NEW backup)
- `/root/hermes-rp-backups/20260707-161025-tier-rules-LIVE/tier_rules_diff.patch` (NEW diff)
- `/root/hermes-rp-backups/20260701-013604/SOUL.md` (reverted to pristine 245 lines — snapshot, NOT modified)

## Commit

N/A — VPS file, will be committed as `docs/` reference copy at plan end (per commit strategy: VPS files committed as reference copies).

## Notes for downstream tasks

- W1.7 bot `/status` `/help`: SOUL.md already has TIER RULES that reference `/upgrade` `/topup` — these slash commands will be wired in W2.3 (Pakasir Wave). Until then, SOUL.md mentions them but they don't exist yet. Acceptable for Wave 1 (gating works without the commands existing).
- W1.8 verify Phase 1: when testing free-tier NSFW chat denial, persona should follow TIER RULES (in-character rejection + offer /upgrade).
