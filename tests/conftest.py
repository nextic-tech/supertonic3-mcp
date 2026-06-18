"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def mock_tts(monkeypatch):
    engine = MagicMock()
    engine.voice_style_names = ["M1", "F1"]
    engine.get_voice_style.return_value = SimpleNamespace(name="M1")
    engine.synthesize.return_value = (np.zeros((1, 1000), dtype=np.float32), 1.5)
    engine.save_audio = MagicMock()

    import supertonic3_mcp.tts as tts_mod

    monkeypatch.setattr(tts_mod, "_tts", engine)
    return engine


@pytest.fixture
def tmp_audio_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("supertonic3_mcp.audio.TMP_DIR", tmp_path)
    return tmp_path
