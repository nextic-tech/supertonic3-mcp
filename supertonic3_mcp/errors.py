"""Exception hierarchy for supertonic3-mcp."""


class Supertonic3MCPError(Exception):
    """Base error for this package."""


class SpeakError(Supertonic3MCPError):
    """Text-to-speech failures."""


class EmptyTextError(SpeakError):
    """Input text is empty or whitespace-only."""


class TextTooLongError(SpeakError):
    """Input text exceeds the character limit."""


class SpeedOutOfRangeError(SpeakError):
    """Playback speed is outside the allowed range."""


class VoiceNotFoundError(SpeakError):
    """Unknown voice_id."""


class NoAudioDeviceError(Supertonic3MCPError):
    """No suitable audio output device for playback."""
