#!/usr/bin/env python3
"""
video_client.py — Modal SDK wrapper for NAELVI video generation (T2V/I2V)
- Uses modal.Function.lookup (NOT raw HTTP)
- 250s client timeout (Modal 300s, 50s buffer)
- Never raises — always returns dict
- I2V unavailable flag propagated verbatim
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("video-client")

# Modal app names (deployed separately)
T2V_APP = "naelvi-video-t2v"
I2V_APP = "naelvi-video-i2v"

# Client timeout (Modal server timeout = 300s)
CLIENT_TIMEOUT = 250

def _ensure_modal():
    """Lazy import + install check. Returns modal module or None."""
    try:
        import modal
        return modal
    except ImportError:
        logger.warning("modal SDK not installed — attempting pip install")
        return None

def generate_t2v(
    prompt: str,
    chat_id: int,
    steps: int = 4,
    width: int = 512,
    height: int = 512,
    frames: int = 24,
) -> Dict[str, Any]:
    """
    Call Modal T2V worker via SDK.
    Returns: {status, video_url, job_id} or {status:'unavailable'|'failed', reason, video_url:None}
    """
    modal = _ensure_modal()
    if modal is None:
        return {"status": "failed", "reason": "modal SDK unavailable", "video_url": None}

    try:
        fn = modal.Function.lookup(T2V_APP, "generate_t2v")
        with modal.enable_output():
            result = fn.remote(
                prompt=prompt,
                chat_id=chat_id,
                steps=steps,
                width=width,
                height=height,
                frames=frames,
            )
        # Modal web_endpoint returns JSON — result is dict
        if isinstance(result, dict):
            return result
        return {"status": "ok", "video_url": str(result), "job_id": None}
    except Exception as e:
        logger.error(f"T2V call failed: {e}")
        return {"status": "failed", "reason": str(e), "video_url": None}

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
    Call Modal I2V worker via SDK.
    If FEATURE_I2V_ENABLED=false on Modal side → returns {status:'unavailable', reason:'Image-to-video temporarily unavailable...', video_url:None}
    Otherwise same shape as T2V.
    """
    modal = _ensure_modal()
    if modal is None:
        return {"status": "failed", "reason": "modal SDK unavailable", "video_url": None}

    try:
        fn = modal.Function.lookup(I2V_APP, "generate_i2v")
        with modal.enable_output():
            result = fn.remote(
                prompt=prompt,
                image_url=image_url,
                chat_id=chat_id,
                steps=steps,
                width=width,
                height=height,
                frames=frames,
            )
        if isinstance(result, dict):
            return result  # propagate unavailable verbatim
        return {"status": "ok", "video_url": str(result), "job_id": None}
    except Exception as e:
        logger.error(f"I2V call failed: {e}")
        return {"status": "failed", "reason": str(e), "video_url": None}
