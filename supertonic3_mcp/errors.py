"""Exception hierarchy for supertonic3-mcp."""


class Supertonic3MCPError(Exception):
    """Base error for this package."""


class SpeakError(Supertonic3MCPError):
    """Text-to-speech failures."""


class VoiceNotFoundError(SpeakError):
    """Unknown voice_id."""


class TextTooLongError(SpeakError):
    """Input text exceeds the character limit."""


class STTError(Supertonic3MCPError):
    """Speech-to-text failures (reserved for v1.1)."""


class WhisperModelError(STTError):
    """Whisper model missing or failed to load."""


class MicrophoneError(STTError):
    """Microphone unavailable."""


class MicrophonePermissionError(MicrophoneError):
    """Microphone permission denied."""


class NoAudioDeviceError(Supertonic3MCPError):
    """No suitable audio output device for playback."""
