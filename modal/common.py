"""modal/common.py — shared helpers for video workers."""

from __future__ import annotations

import datetime
import os
import subprocess
import tempfile
from typing import Any

import modal
import torch
import numpy as np
from PIL import Image
from supabase import Client, create_client


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
BUCKET = "naelvi-videos"


def get_supabase() -> Client:
    """Return authenticated Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def load_animatediff(model_id: str, device: str = "cuda") -> Any:
    """Load AnimateDiff pipeline once per container."""
    from diffusers import AnimateDiffPipeline, MotionAdapter
    from diffusers import EulerDiscreteScheduler

    adapter = MotionAdapter.from_pretrained(
        "guoyww/animatediff-motion-adapter-sdxl-beta",
        torch_dtype=torch.float16,
    )
    pipe = AnimateDiffPipeline.from_pretrained(
        model_id,
        motion_adapter=adapter,
        torch_dtype=torch.float16,
    )
    pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    pipe.enable_vae_slicing()
    return pipe


def frames_to_mp4(frames: list[Image.Image], fps: int = 8) -> str:
    """Convert PIL frames → H.264 MP4 via ffmpeg pipe. Return path."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output = tmp.name

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
        output,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        proc.stdin.write(np.array(f).tobytes())
    proc.stdin.close()
    proc.wait()
    return output


def upload_to_supabase(local_path: str, object_name: str) -> str:
    """Upload MP4 to Supabase Storage. Return public URL."""
    supa = get_supabase()
    with open(local_path, "rb") as f:
        supa.storage.from_(BUCKET).upload(object_name, f, {"content-type": "video/mp4"})
    return supa.storage.from_(BUCKET).get_public_url(object_name)


def cleanup_old_outputs():
    """Cron: delete objects >24h old. Scheduled in worker files."""
    supa = get_supabase()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    to_delete: list[str] = []
    limit = 1000
    # list root prefixes (chat_id folders)
    offset = 0
    while True:
        try:
            items = supa.storage.from_(BUCKET).list(
                path="",
                options={"limit": limit, "offset": offset}
            )
        except Exception:
            break
        if not items:
            break
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            if name.endswith("/"):
                prefix = name
            else:
                prefix = name + "/"
            # list inside prefix
            sub_offset = 0
            while True:
                try:
                    sub_items = supa.storage.from_(BUCKET).list(
                        path=prefix.rstrip("/"),
                        options={"limit": limit, "offset": sub_offset}
                    )
                except Exception:
                    break
                if not sub_items:
                    break
                for sub in sub_items:
                    sub_name = sub.get("name", "")
                    if not sub_name or sub_name.endswith("/"):
                        continue
                    full_name = f"{prefix}{sub_name}" if prefix.endswith("/") else f"{prefix}/{sub_name}"
                    created_str = (
                        sub.get("created_at")
                        or sub.get("updated_at")
                        or sub.get("last_accessed_at")
                    )
                    if created_str:
                        try:
                            created = datetime.datetime.fromisoformat(
                                created_str.replace("Z", "+00:00")
                            )
                            if created < cutoff:
                                to_delete.append(full_name)
                        except Exception:
                            pass  # bad timestamp, skip
                sub_offset += len(sub_items)
                if len(sub_items) < limit:
                    break
        offset += len(items)
        if len(items) < limit:
            break
    # delete per-object with try/except so one failure doesn't kill run
    for obj_name in to_delete:
        try:
            supa.storage.from_(BUCKET).remove([obj_name])
        except Exception:
            pass  # continue cleanup
