"""Tests for audio.py."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from supertonic3_mcp.audio import make_tmp_wav_path, play, sweep_tmp, write_wav
from supertonic3_mcp.errors import NoAudioDeviceError


def test_sweep_tmp_removes_old_files(tmp_audio_dir):
    old = tmp_audio_dir / "supertonic_old.wav"
    old.write_bytes(b"wav")
    past = time.time() - 600
    import os

    os.utime(old, (past, past))
    fresh = tmp_audio_dir / "supertonic_new.wav"
    fresh.write_bytes(b"wav")

    removed = sweep_tmp(max_age_seconds=300)
    assert removed == 1
    assert not old.exists()
    assert fresh.exists()


def test_write_wav_delegates_to_engine(tmp_audio_dir):
    engine = MagicMock()
    path = tmp_audio_dir / "out.wav"
    wav = object()
    write_wav(engine, wav, path)
    engine.save_audio.assert_called_once_with(wav, str(path))


def test_make_tmp_wav_path_under_tmp(tmp_audio_dir, monkeypatch):
    monkeypatch.setattr("supertonic3_mcp.audio.TMP_DIR", tmp_audio_dir)
    path = make_tmp_wav_path()
    assert path.parent == tmp_audio_dir
    assert path.name.startswith("supertonic_")


@patch("supertonic3_mcp.audio.subprocess.run")
@patch("supertonic3_mcp.audio.platform.system", return_value="Darwin")
def test_play_afplay_on_macos(mock_system, mock_run, tmp_path):
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"x")
    play(wav)
    mock_run.assert_called_once_with(["afplay", str(wav)], check=True)


@patch("supertonic3_mcp.audio.platform.system", return_value="Windows")
def test_play_unsupported_platform(mock_system, tmp_path):
    with pytest.raises(NoAudioDeviceError):
        play(tmp_path / "x.wav")
