"""Tests for server wiring and preload CLI."""

from __future__ import annotations

import pytest

from supertonic3_mcp.__main__ import run_preload
from supertonic3_mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_registers_tools():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"speak", "list_voices", "list_expressions"}


def test_preload_success(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    onnx = cache / "model.onnx"
    onnx.write_bytes(b"fake-onnx")

    monkeypatch.setattr("supertonic.loader.get_cache_dir", lambda: cache)

    def fake_download(target, model_name=None):
        target.mkdir(parents=True, exist_ok=True)
        (target / "dp.onnx").write_bytes(b"x")

    monkeypatch.setattr("supertonic.loader.download_model", fake_download)
    monkeypatch.setattr(
        "supertonic.loader.has_all_onnx_modules",
        lambda model_dir: True,
    )

    assert run_preload() == 0


def test_preload_incomplete_model(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    monkeypatch.setattr("supertonic.loader.get_cache_dir", lambda: cache)
    monkeypatch.setattr("supertonic.loader.download_model", lambda *a, **k: None)
    monkeypatch.setattr(
        "supertonic.loader.has_all_onnx_modules",
        lambda model_dir: False,
    )
    assert run_preload() == 1


def test_preload_atomic_temp_cleaned_on_download_error(tmp_path, monkeypatch):
    """Atomic preload: if download raises, temp dir is removed and cache_dir has no corrupt content."""
    cache = tmp_path / "cache"
    monkeypatch.setattr("supertonic.loader.get_cache_dir", lambda: cache)

    def fake_download_fails(target, model_name=None):
        target.mkdir(parents=True, exist_ok=True)
        (target / "partial.onnx").write_bytes(b"partial")
        raise OSError("network interrupted")

    monkeypatch.setattr("supertonic.loader.download_model", fake_download_fails)
    monkeypatch.setattr("supertonic.loader.has_all_onnx_modules", lambda *a: True)

    with pytest.raises(OSError, match="network interrupted"):
        run_preload()

    tmp_dir = cache.parent / (cache.name + ".tmp_preload")
    assert not tmp_dir.exists(), "temp dir must be cleaned up after failure"
    assert not cache.exists(), "cache_dir must not contain a partial/corrupt model"


def test_preload_atomic_cache_replaced_on_success(tmp_path, monkeypatch):
    """Atomic preload: on success, cache_dir is fully replaced and temp dir is gone."""
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "old.onnx").write_bytes(b"old")  # simulate pre-existing stale cache

    monkeypatch.setattr("supertonic.loader.get_cache_dir", lambda: cache)

    def fake_download(target, model_name=None):
        target.mkdir(parents=True, exist_ok=True)
        (target / "new.onnx").write_bytes(b"new")

    monkeypatch.setattr("supertonic.loader.download_model", fake_download)
    monkeypatch.setattr("supertonic.loader.has_all_onnx_modules", lambda *a: True)

    assert run_preload() == 0
    tmp_dir = cache.parent / (cache.name + ".tmp_preload")
    assert not tmp_dir.exists(), "temp dir must be removed after successful rename"
    assert (cache / "new.onnx").exists(), "cache_dir must contain new model"
    assert not (cache / "old.onnx").exists(), "stale cache must be replaced"
