#!/usr/bin/env python3
"""
video_client.py — Modal SDK wrapper for NAELVI video generation (T2V/I2V)
- Uses modal.Function.from_name (compatible with Modal SDK 1.x)
- 250s client timeout (Modal 300s, 50s buffer)
- Never raises — always returns dict
- I2V unavailable flag propagated verbatim
- Dual-mode: Modal SDK (preferred) with raw HTTP fallback
"""

import os
import logging
import urllib.request
import json as _json
from typing import Optional, Dict, Any

logger = logging.getLogger("video-client")

# Modal app names (deployed separately)
T2V_APP = "naelvi-video-t2v"
I2V_APP = "naelvi-video-i2v"

# Endpoint URLs (raw HTTP fallback)
T2V_URL = "https://naelvi-02--naelvi-video-t2v-generate-t2v.modal.run"
I2V_URL = "https://naelvi-02--naelvi-video-i2v-generate-i2v.modal.run"

# Client timeout (Modal server timeout = 300s)
CLIENT_TIMEOUT = 250


def _ensure_modal():
    """Lazy import + install check. Returns modal module or None."""
    try:
        import modal
        return modal
    except ImportError:
        logger.warning("modal SDK not installed — using raw HTTP fallback")
        return None


def _call_via_sdk(modal_mod, app_name: str, fn_name: str, payload: dict) -> dict:
    """Call a Modal web endpoint via the Python SDK (Function.from_name)."""
    fn = modal_mod.Function.from_name(app_name, fn_name)
    with modal_mod.enable_output():
        result = fn.remote(payload)
    if isinstance(result, dict):
        return result
    return {"status": "ok", "video_url": str(result), "job_id": None}


def _call_via_http(url: str, payload: dict) -> dict:
    """Raw HTTP POST fallback when Modal SDK is not available."""
    data = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=CLIENT_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            return _json.loads(body)
    except Exception as e:
        return {"status": "failed", "reason": str(e), "video_url": None}


def generate_t2v(
    prompt: str,
    chat_id: int,
    steps: int = 4,
    width: int = 512,
    height: int = 512,
    frames: int = 24,
) -> Dict[str, Any]:
    """
    Call Modal T2V worker via SDK (preferred) or raw HTTP.
    Returns: {status, video_url, job_id} or {status: unavailable|failed, reason, video_url:None}
    """
    payload = {
        "prompt": prompt,
        "chat_id": chat_id,
        "steps": steps,
        "width": width,
        "height": height,
        "frames": frames,
    }

    modal_mod = _ensure_modal()
    if modal_mod is not None:
        try:
            return _call_via_sdk(modal_mod, T2V_APP, "generate_t2v", payload)
        except Exception as e:
            logger.error(f"T2V SDK call failed: {e} — falling back to HTTP")
            return _call_via_http(T2V_URL, payload)
    else:
        logger.info("modal SDK not available — using raw HTTP for T2V")
        return _call_via_http(T2V_URL, payload)


def generate_i2v(
    prompt: str,
    image_url: str,
    chat_id: int,
    steps: int = 4,
    width: int = 512,
    height: int = 512,
    frames: int = 24,
) -> Dict[str, Any]:
    """
    Call Modal I2V worker via SDK (preferred) or raw HTTP.
    If FEATURE_I2V_ENABLED=false on Modal side → returns {status:unavailable, reason:..., video_url:None}
    Otherwise same shape as T2V.
    """
    payload = {
        "prompt": prompt,
        "image_url": image_url,
        "chat_id": chat_id,
        "steps": steps,
        "width": width,
        "height": height,
        "frames": frames,
    }

    modal_mod = _ensure_modal()
    if modal_mod is not None:
        try:
            result = _call_via_sdk(modal_mod, I2V_APP, "generate_i2v", payload)
            return result  # propagate "unavailable" verbatim
        except Exception as e:
            logger.error(f"I2V SDK call failed: {e} — falling back to HTTP")
            return _call_via_http(I2V_URL, payload)
    else:
        logger.info("modal SDK not available — using raw HTTP for I2V")
        return _call_via_http(I2V_URL, payload)
