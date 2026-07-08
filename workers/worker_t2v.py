"""workers/worker_t2v.py — Text-to-Video via AnimateDiff-Lightning."""

from __future__ import annotations

import os
from typing import Any

import modal

from .common import (
    cleanup_old_outputs,
    frames_to_mp4,
    load_animatediff,
    upload_to_supabase,
)

app = modal.App("naelvi-video-t2v")
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim()
    .pip_install(
        "diffusers",
        "transformers",
        "accelerate",
        "torch",
        "supabase",
        "pillow",
        "numpy",
        "safetensors",
        "huggingface_hub",
        "fastapi[standard]",
    )
    .apt_install("ffmpeg")
)

MODEL_ID = "emilianJR/epiCRealism"


@app.function(
    gpu="L4",
    image=image,
    volumes={"/models": volume},
    secrets=[modal.Secret.from_name("supabase-secrets")],
    timeout=300,
    scaledown_window=60,
)
@modal.fastapi_endpoint(method="POST")
def generate_t2v(request: dict[str, Any]) -> dict[str, Any]:
    """POST /generate — body: {prompt, steps=4, width=512, height=512, frames=24, chat_id}."""
    from PIL import Image  # type: ignore[import-untyped]  # lazy — resolved in Modal container

    prompt: str = request["prompt"]
    steps: int = request.get("steps", 4)
    width: int = request.get("width", 512)
    height: int = request.get("height", 512)
    frames: int = request.get("frames", 24)
    chat_id: int = request["chat_id"]

    pipe = load_animatediff(MODEL_ID)
    result = pipe(
        prompt=prompt,
        num_frames=frames,
        guidance_scale=1.0,
        num_inference_steps=steps,
        width=width,
        height=height,
    )
    pil_frames: list[Image.Image] = result.frames[0]

    mp4_path = frames_to_mp4(pil_frames, fps=8)
    object_name = f"{chat_id}/{os.urandom(8).hex()}.mp4"
    video_url = upload_to_supabase(mp4_path, object_name)
    os.unlink(mp4_path)

    return {"status": "ok", "video_url": video_url, "job_id": object_name}


@app.function(
    image=image,
    volumes={"/models": volume},
    schedule=modal.Cron("0 */6 * * *"),
)
def cleanup() -> None:
    """Every 6h: delete outputs older than 24h."""
    cleanup_old_outputs()
