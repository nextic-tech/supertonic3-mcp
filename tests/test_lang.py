"""Tests for lang.py."""

from supertonic3_mcp.lang import resolve_language, resolve_voice_id


def test_resolve_language_explicit():
    assert resolve_language("ko", None) == "ko"


def test_resolve_language_default_en():
    assert resolve_language(None, None) == "en"


def test_resolve_language_ignores_voice_for_lang_default():
    assert resolve_language(None, "F1") == "en"


def test_resolve_voice_id_explicit():
    assert resolve_voice_id("F1", "ko", ["M1", "F1"]) == "F1"


def test_resolve_voice_id_default_m1():
    assert resolve_voice_id(None, "en", ["M1", "F1"]) == "M1"
