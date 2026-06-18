"""Supertonic TTS integration — speak, list_voices, list_expressions."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from supertonic import TTS

from supertonic3_mcp import audio
from supertonic3_mcp.errors import TextTooLongError, VoiceNotFoundError
from supertonic3_mcp.lang import VOICE_GENDER, resolve_language, resolve_voice_id

MAX_TEXT_LENGTH = 5000
MIN_SPEED = 0.7
MAX_SPEED = 2.0

# Curated from Supertonic 3 docs — no SDK list_expressions() API (see notes/spike-result.md).
EXPRESSION_CATALOG: list[dict[str, str]] = [
    {
        "tag": "<laugh>",
        "description": "Natural laugh vocalization",
        "example": "Oh that's funny! <laugh> I never expected that.",
    },
    {
        "tag": "<breath>",
        "description": "Breath sound",
        "example": "Let me catch my breath. <breath> Okay, continue.",
    },
    {
        "tag": "<sigh>",
        "description": "Sigh vocalization",
        "example": "Well, <sigh> that's how it goes sometimes.",
    },
    {
        "tag": "<gasp>",
        "description": "Gasp vocalization",
        "example": "<gasp> I can't believe you did that!",
    },
    {
        "tag": "<cough>",
        "description": "Cough vocalization",
        "example": "<cough> Excuse me, as I was saying...",
    },
    {
        "tag": "<hm>",
        "description": "Thinking hum",
        "example": "<hm> Let me think about that.",
    },
    {
        "tag": "<oh>",
        "description": "Exclamation oh",
        "example": "<oh> I see what you mean now.",
    },
    {
        "tag": "<um>",
        "description": "Filler um",
        "example": "I was, <um>, planning to finish today.",
    },
    {
        "tag": "<uh>",
        "description": "Filler uh",
        "example": "The answer is, <uh>, complicated.",
    },
    {
        "tag": "<pause>",
        "description": "Short pause",
        "example": "Wait <pause> did you hear that?",
    },
]

_tts = TTS(auto_download=True)
_onnx_lock = asyncio.Lock()


def _duration_seconds(duration: Any) -> float:
    if hasattr(duration, "item"):
        return float(duration.item())
    return float(duration)


def _validate_voice(voice_id: str) -> None:
    if voice_id not in _tts.voice_style_names:
        raise VoiceNotFoundError(
            f"unknown voice_id '{voice_id}'; call list_voices() for valid values"
        )


async def speak(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    speed: float = 1.0,
    play: bool = False,
) -> str:
    """Synthesize speech and return an absolute WAV path with metadata."""
    if not text.strip():
        raise ValueError("text must be non-empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise TextTooLongError(
            f"text exceeds {MAX_TEXT_LENGTH} char limit ({len(text)} chars)"
        )
    if speed < MIN_SPEED or speed > MAX_SPEED:
        raise ValueError(f"speed must be in [{MIN_SPEED}, {MAX_SPEED}]")

    audio.sweep_tmp()
    lang = resolve_language(language, voice_id)
    resolved_voice = resolve_voice_id(voice_id, language, list(_tts.voice_style_names))
    _validate_voice(resolved_voice)

    style = _tts.get_voice_style(voice_name=resolved_voice)
    wav_path = audio.make_tmp_wav_path()

    try:
        async with _onnx_lock:
            wav, duration = _tts.synthesize(
                text,
                voice_style=style,
                lang=lang,
                speed=speed,
            )
        audio.write_wav(_tts, wav, wav_path)
    except Exception:
        wav_path.unlink(missing_ok=True)
        raise

    if play:
        audio.play(wav_path)

    dur_s = _duration_seconds(duration)
    return (
        f"Audio saved to {wav_path.resolve()} "
        f"({dur_s:.1f}s, voice: {resolved_voice}, lang: {lang})"
    )


async def list_voices() -> str:
    """Return JSON list of available voice styles."""
    voices: list[dict[str, str | None]] = []
    for voice_id in _tts.voice_style_names:
        gender = VOICE_GENDER.get(voice_id)
        voices.append(
            {
                "voice_id": voice_id,
                "language_code": None,
                "language_name": None,
                "gender": gender,
            }
        )
    return json.dumps(voices, indent=2)


async def list_expressions() -> str:
    """Return JSON list of inline expression tags supported in speak() text."""
    return json.dumps(EXPRESSION_CATALOG, indent=2)
