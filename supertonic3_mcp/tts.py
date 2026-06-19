"""Supertonic TTS integration — speak, list_voices, list_expressions."""

from __future__ import annotations

import asyncio
from typing import Any

from supertonic import TTS

from supertonic3_mcp import audio
from supertonic3_mcp.errors import (
    EmptyTextError,
    SpeedOutOfRangeError,
    TextTooLongError,
    VoiceNotFoundError,
)

MAX_TEXT_LENGTH = 5000
MIN_SPEED = 0.7
MAX_SPEED = 2.0
DEFAULT_LANGUAGE = "en"
DEFAULT_VOICE = "M1"

# Built-in voices are style presets; language is passed separately to synthesize().
VOICE_GENDER: dict[str, str] = {
    "M1": "male",
    "M2": "male",
    "M3": "male",
    "M4": "male",
    "M5": "male",
    "F1": "female",
    "F2": "female",
    "F3": "female",
    "F4": "female",
    "F5": "female",
}

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

_tts: TTS | None = None
_init_lock = asyncio.Lock()
_onnx_lock = asyncio.Lock()


def resolve_language(language: str | None) -> str:
    """Return ISO 639-1 language code for synthesize().

    Defaults to English when omitted. Agents must pass language= for non-English text.
    """
    if language is not None and language.strip():
        return language.strip().lower()
    return DEFAULT_LANGUAGE


def resolve_voice(voice_id: str | None, available_voices: list[str]) -> str:
    """Pick a voice name; raise VoiceNotFoundError when voice_id is unknown."""
    if voice_id is not None:
        if voice_id not in available_voices:
            raise VoiceNotFoundError(
                f"unknown voice_id '{voice_id}'; call list_voices() for valid values"
            )
        return voice_id
    if DEFAULT_VOICE in available_voices:
        return DEFAULT_VOICE
    if available_voices:
        return available_voices[0]
    return DEFAULT_VOICE


async def _get_tts() -> TTS:
    global _tts
    if _tts is not None:
        return _tts
    async with _init_lock:
        if _tts is None:
            _tts = TTS(auto_download=True)
        return _tts


def _duration_seconds(duration: Any) -> float:
    if hasattr(duration, "item"):
        return float(duration.item())
    return float(duration)


async def speak(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    speed: float = 1.0,
    play: bool = False,
) -> str:
    """Synthesize speech and return an absolute WAV path with metadata."""
    if not text.strip():
        raise EmptyTextError("text must be non-empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise TextTooLongError(
            f"text exceeds {MAX_TEXT_LENGTH} char limit ({len(text)} chars)"
        )
    if speed < MIN_SPEED or speed > MAX_SPEED:
        raise SpeedOutOfRangeError(f"speed must be in [{MIN_SPEED}, {MAX_SPEED}]")

    tts = await _get_tts()
    lang = resolve_language(language)
    resolved_voice = resolve_voice(voice_id, list(tts.voice_style_names))

    style = tts.get_voice_style(voice_name=resolved_voice)
    wav_path = audio.make_tmp_wav_path()

    try:
        async with _onnx_lock:
            wav, duration = tts.synthesize(
                text,
                voice_style=style,
                lang=lang,
                speed=speed,
            )
        audio.write_wav(tts, wav, wav_path)
    except Exception:
        wav_path.unlink(missing_ok=True)
        raise

    if play:
        await asyncio.to_thread(audio.play, wav_path)

    dur_s = _duration_seconds(duration)
    return (
        f"Audio saved to {wav_path.resolve()} "
        f"({dur_s:.1f}s, voice: {resolved_voice}, lang: {lang})"
    )


async def list_voices() -> list[dict[str, str | None]]:
    """Return available voice styles."""
    tts = await _get_tts()
    return [
        {"voice_id": name, "gender": VOICE_GENDER.get(name)}
        for name in tts.voice_style_names
    ]


async def list_expressions() -> list[dict[str, str]]:
    """Return inline expression tags supported in speak() text."""
    return list(EXPRESSION_CATALOG)
