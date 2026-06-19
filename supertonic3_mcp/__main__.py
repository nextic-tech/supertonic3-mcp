"""CLI entry: STDIO MCP server and preload subcommand."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

from supertonic3_mcp import audio
from supertonic3_mcp.server import mcp


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_preload() -> int:
    """Download TTS model atomically and print checksums."""
    from supertonic.loader import download_model, get_cache_dir, has_all_onnx_modules

    cache_dir = get_cache_dir()
    tmp_dir = cache_dir.parent / (cache_dir.name + ".tmp_preload")

    # Clean up any stale temp dir from a previous interrupted run
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    print(f"Preloading Supertonic model to {cache_dir} ...")
    try:
        download_model(tmp_dir)
        if not has_all_onnx_modules(tmp_dir):
            print("ERROR: Model download incomplete — ONNX modules missing.", file=sys.stderr)
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return 1
        # Atomic: replace any existing cache_dir with the newly downloaded one
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        os.rename(tmp_dir, cache_dir)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    print("Checksums:")
    for path in sorted(cache_dir.rglob("*")):
        if not path.is_file():
            continue
        size = path.stat().st_size
        print(f"  {path.relative_to(cache_dir)}  {size} bytes  sha256={_sha256(path)}")

    print("Preload complete.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="supertonic3-mcp")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("preload", help="Download TTS model weights for offline use")

    args = parser.parse_args()
    if args.command == "preload":
        raise SystemExit(run_preload())

    audio.sweep_tmp()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
