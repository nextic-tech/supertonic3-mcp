"""Audio file I/O, /tmp cleanup, and optional system playback."""

from __future__ import annotations

import platform
import subprocess
import time
import uuid
from pathlib import Path

from supertonic3_mcp.errors import NoAudioDeviceError

TMP_DIR = Path("/tmp")
TMP_GLOB = "supertonic_*.wav"
TMP_MAX_AGE_SECONDS = 5 * 60


def sweep_tmp(max_age_seconds: int = TMP_MAX_AGE_SECONDS) -> int:
    """Delete stale supertonic WAV files under /tmp. Returns count removed."""
    removed = 0
    now = time.time()
    for path in TMP_DIR.glob(TMP_GLOB):
        try:
            if now - path.stat().st_mtime > max_age_seconds:
                path.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def make_tmp_wav_path() -> Path:
    return TMP_DIR / f"supertonic_{uuid.uuid4().hex}.wav"


def write_wav(tts_engine: object, wav: object, path: Path) -> None:
    """Write synthesized audio using the SDK save_audio helper."""
    tts_engine.save_audio(wav, str(path))  # type: ignore[attr-defined]


def play(path: Path) -> None:
    """Play a WAV file via the platform audio CLI."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["afplay", str(path)], check=True)
        return
    if system == "Linux":
        subprocess.run(["aplay", str(path)], check=True)
        return
    raise NoAudioDeviceError(
        "Auto-play is not supported on this platform. "
        "Use the returned WAV file path and play it locally."
    )
