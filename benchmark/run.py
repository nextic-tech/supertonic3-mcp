#!/usr/bin/env python3
"""Measure Full Synthesis Latency (FSL) for speak() on this machine."""

from __future__ import annotations

import importlib.metadata
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

BENCHMARK_TEXT = "Hello, this is a test of Supertonic 3 text to speech."
VOICE = "M1"
LANG = "en"
ITERATIONS = 10


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    idx = max(0, int(len(ordered) * pct) - 1)
    return ordered[idx]


def run_cold_warm() -> tuple[list[float], list[float]]:
    from supertonic import TTS

    cold: list[float] = []
    for _ in range(ITERATIONS):
        tts = TTS(auto_download=True)
        style = tts.get_voice_style(voice_name=VOICE)
        t0 = time.perf_counter()
        wav, _ = tts.synthesize(BENCHMARK_TEXT, voice_style=style, lang=LANG)
        out = Path("/tmp") / f"bench_{time.time_ns()}.wav"
        tts.save_audio(wav, str(out))
        cold.append(time.perf_counter() - t0)
        out.unlink(missing_ok=True)

    tts = TTS(auto_download=True)
    style = tts.get_voice_style(voice_name=VOICE)
    warm: list[float] = []
    for _ in range(ITERATIONS):
        t0 = time.perf_counter()
        wav, _ = tts.synthesize(BENCHMARK_TEXT, voice_style=style, lang=LANG)
        out = Path("/tmp") / f"bench_{time.time_ns()}.wav"
        tts.save_audio(wav, str(out))
        warm.append(time.perf_counter() - t0)
        out.unlink(missing_ok=True)

    return cold, warm


def stats_block(times: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(times),
        "p95": percentile(times, 0.95),
        "min": min(times),
        "max": max(times),
    }


def main() -> int:
    cold, warm = run_cold_warm()
    cold_stats = stats_block(cold)
    warm_stats = stats_block(warm)

    try:
        chip = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        chip = platform.processor() or platform.machine()

    results_path = Path(__file__).parent / "results.md"
    body = f"""# Supertonic 3 MCP — FSL Benchmark

**Date:** {time.strftime('%Y-%m-%d')}  
**Hardware:** {platform.platform()} / {chip}  
**supertonic:** {importlib.metadata.version('supertonic')}  
**Python:** {sys.version.split()[0]}

**Metric:** Full Synthesis Latency (FSL) — `synthesize()` + `save_audio()` to WAV (no `play=True`).

**Input:** `{BENCHMARK_TEXT}` ({len(BENCHMARK_TEXT)} chars)  
**Voice:** {VOICE} | **Language:** {LANG}

## Results

| Scenario | Median (s) | p95 (s) | Min (s) | Max (s) |
|----------|------------|---------|---------|---------|
| Cold (new `TTS()` per iteration) | {cold_stats['median']:.3f} | {cold_stats['p95']:.3f} | {cold_stats['min']:.3f} | {cold_stats['max']:.3f} |
| Warm (reuse loaded `TTS`) | {warm_stats['median']:.3f} | {warm_stats['p95']:.3f} | {warm_stats['min']:.3f} | {warm_stats['max']:.3f} |

## Notes

- Cold includes per-iteration `TTS()` construction and model load.
- MCP server uses eager `_tts` at import (warm path after first load).
- Compare against HTTP-wrapped alternatives on the same hardware before publishing latency claims.
"""
    results_path.write_text(body)
    print(results_path.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
