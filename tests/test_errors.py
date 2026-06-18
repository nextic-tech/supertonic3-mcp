"""Tests for errors.py."""

from supertonic3_mcp.errors import (
    MicrophonePermissionError,
    SpeakError,
    STTError,
    Supertonic3MCPError,
    TextTooLongError,
    VoiceNotFoundError,
    WhisperModelError,
)


def test_speak_error_hierarchy():
    assert issubclass(VoiceNotFoundError, SpeakError)
    assert issubclass(TextTooLongError, SpeakError)
    assert issubclass(SpeakError, Supertonic3MCPError)


def test_stt_error_hierarchy():
    assert issubclass(WhisperModelError, STTError)
    assert issubclass(MicrophonePermissionError, STTError)
    assert issubclass(STTError, Supertonic3MCPError)
