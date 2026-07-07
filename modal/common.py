"""modal/common.py — shared helpers for video workers."""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any

import modal
import numpy as np
from PIL import Image
from supabase import Client, create_client


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
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
    # Implementation: list + filter by created_at, remove batch
    # (left as stub — full impl uses storage API pagination)
    pass
