"""Tests for tts.py."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from supertonic3_mcp.errors import TextTooLongError, VoiceNotFoundError
from supertonic3_mcp.tts import MAX_TEXT_LENGTH, speak, list_expressions, list_voices


@pytest.mark.asyncio
async def test_speak_happy_path(mock_tts, tmp_audio_dir, monkeypatch):
    monkeypatch.setattr("supertonic3_mcp.audio.TMP_DIR", tmp_audio_dir)
    result = await speak("Hello world")
    assert "Audio saved to" in result
    assert "voice: M1" in result
    assert "lang: en" in result
    mock_tts.synthesize.assert_called_once()
    mock_tts.save_audio.assert_called_once()


@pytest.mark.asyncio
async def test_speak_empty_text_raises():
    with pytest.raises(ValueError, match="non-empty"):
        await speak("   ")


@pytest.mark.asyncio
async def test_speak_text_too_long():
    with pytest.raises(TextTooLongError):
        await speak("x" * (MAX_TEXT_LENGTH + 1))


@pytest.mark.asyncio
async def test_speak_speed_out_of_range():
    with pytest.raises(ValueError, match="speed"):
        await speak("hi", speed=0.5)


@pytest.mark.asyncio
async def test_speak_unknown_voice(mock_tts):
    with pytest.raises(VoiceNotFoundError):
        await speak("hi", voice_id="Z9")


@pytest.mark.asyncio
async def test_speak_play_after_synthesis(mock_tts, tmp_audio_dir, monkeypatch):
    monkeypatch.setattr("supertonic3_mcp.audio.TMP_DIR", tmp_audio_dir)
    order: list[str] = []

    class TrackingLock:
        async def __aenter__(self):
            order.append("lock_enter")
            return self

        async def __aexit__(self, *args):
            order.append("lock_exit")

    monkeypatch.setattr("supertonic3_mcp.tts._onnx_lock", TrackingLock())

    def fake_play(path):
        order.append("play")

    monkeypatch.setattr("supertonic3_mcp.audio.play", fake_play)
    await speak("Hello", play=True)
    assert order.index("lock_exit") < order.index("play")


@pytest.mark.asyncio
async def test_speak_lock_released_on_synthesize_error(mock_tts, tmp_audio_dir, monkeypatch):
    monkeypatch.setattr("supertonic3_mcp.audio.TMP_DIR", tmp_audio_dir)
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("synth failed")
        return (np.zeros((1, 100), dtype=np.float32), 0.5)

    mock_tts.synthesize.side_effect = boom

    with pytest.raises(RuntimeError, match="synth failed"):
        await speak("first")

    result = await speak("second")
    assert "Audio saved to" in result


@pytest.mark.asyncio
async def test_list_voices_json(mock_tts):
    payload = json.loads(await list_voices())
    assert len(payload) == 2
    assert payload[0]["voice_id"] == "M1"


@pytest.mark.asyncio
async def test_list_expressions_json():
    payload = json.loads(await list_expressions())
    tags = {row["tag"] for row in payload}
    assert "<laugh>" in tags
    assert "<pause>" in tags
