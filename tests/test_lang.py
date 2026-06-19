"""Tests for language and voice resolution in tts.py."""

import pytest

from supertonic3_mcp.errors import VoiceNotFoundError
from supertonic3_mcp.tts import resolve_language, resolve_voice


def test_resolve_language_explicit():
    assert resolve_language("ko") == "ko"


def test_resolve_language_default_en():
    assert resolve_language(None) == "en"


def test_resolve_voice_explicit():
    assert resolve_voice("F1", ["M1", "F1"]) == "F1"


def test_resolve_voice_default_m1():
    assert resolve_voice(None, ["M1", "F1"]) == "M1"


def test_resolve_voice_unknown_raises():
    with pytest.raises(VoiceNotFoundError, match="Z9"):
        resolve_voice("Z9", ["M1", "F1"])
