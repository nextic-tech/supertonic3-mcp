"""Language and voice resolution — explicit only, no langdetect."""

from __future__ import annotations

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


def resolve_language(language: str | None, voice_id: str | None) -> str:
    """Return ISO 639-1 language code for synthesize().

    voice_id does not change the resolved language when language is omitted —
    we default to English. Agents must pass language= for non-English text.
    """
    if language is not None and language.strip():
        return language.strip().lower()
    return DEFAULT_LANGUAGE


def resolve_voice_id(
    voice_id: str | None,
    language: str | None,
    available_voices: list[str],
) -> str:
    """Pick a voice name. voice_id wins when set."""
    if voice_id is not None:
        return voice_id
    if DEFAULT_VOICE in available_voices:
        return DEFAULT_VOICE
    if available_voices:
        return available_voices[0]
    return DEFAULT_VOICE
