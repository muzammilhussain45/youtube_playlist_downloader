"""Utility helpers for formatting and thumbnails."""


from pathlib import Path
from typing import Optional

import requests


def format_size(num_bytes: Optional[float]) -> str:
    """
    Formats a byte count into a human readable string.
    """

    if not num_bytes:
        return "0 B"

    size = float(num_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]

    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    return f"{size:.1f} {units[index]}"


def format_speed(bytes_per_second: Optional[float]) -> str:
    """
    Formats a transfer rate into a human readable string.
    """

    if not bytes_per_second:
        return "0 B/s"

    return f"{format_size(bytes_per_second)}/s"


def format_duration(seconds: Optional[int]) -> str:
    """
    Formats a duration in seconds into H:MM:SS or M:SS.
    """

    if not seconds or seconds < 0:
        return "Unknown"

    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


# Estimated combined bitrate (bits/second) per resolution used to
# approximate download size from a video's duration. Values are
# video bitrate + audio bitrate approximations.
_RESOLUTION_BITRATES = {
    "1080p": 4_628_000,          # ~4500 kbps video + 128 kbps audio
    "720p": 2_628_000,           # ~2500 kbps video + 128 kbps audio
    "Best Available": 4_628_000,  # fall back to 1080p estimate
}


def estimate_video_size(
    duration_seconds: Optional[float],
    quality: str
) -> float:
    """
    Estimates a video's download size in bytes for the given quality,
    based on its duration. This is an approximation used for the
    size column and size-weighted progress.
    """

    if not duration_seconds or duration_seconds <= 0:
        return 0.0

    bitrate = _RESOLUTION_BITRATES.get(quality, 4_628_000)
    return (bitrate / 8.0) * float(duration_seconds)


def format_eta(seconds: Optional[float]) -> str:
    """
    Formats an ETA in seconds into a human readable string
    such as "2 minutes, 7 seconds".
    """

    if seconds is None or seconds < 0 or seconds == float("inf"):
        return "calculating..."

    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    return ", ".join(parts)


def load_thumbnail(
    url: Optional[str],
    size: tuple = (160, 90)
) -> Optional["object"]:
    """
    Downloads a thumbnail image and returns a CTkImage-ready PhotoImage.

    Returns None when the image cannot be fetched.
    """

    if not url:
        return None

    try:
        from PIL import Image

        import customtkinter as ctk

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        image = Image.open(__import__("io").BytesIO(response.content))
        image = image.convert("RGB")
        image = image.resize(size, Image.LANCZOS)

        return ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=size
        )

    except Exception:
        return None
