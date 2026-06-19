"""Tests for errors.py."""

from supertonic3_mcp.errors import (
    EmptyTextError,
    SpeakError,
    SpeedOutOfRangeError,
    Supertonic3MCPError,
    TextTooLongError,
    VoiceNotFoundError,
)


def test_speak_error_hierarchy():
    assert issubclass(EmptyTextError, SpeakError)
    assert issubclass(SpeedOutOfRangeError, SpeakError)
    assert issubclass(VoiceNotFoundError, SpeakError)
    assert issubclass(TextTooLongError, SpeakError)
    assert issubclass(SpeakError, Supertonic3MCPError)
