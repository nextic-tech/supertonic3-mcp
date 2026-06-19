# Supertonic 3 MCP — FSL Benchmark

**Date:** 2026-06-19  
**Hardware:** macOS-26.5.1-arm64-arm-64bit / Apple M3  
**supertonic:** 1.3.1  
**Python:** 3.12.8

**Metric:** Full Synthesis Latency (FSL) — `synthesize()` + `save_audio()` to WAV (no `play=True`).

**Input:** `Hello, this is a test of Supertonic 3 text to speech.` (53 chars)  
**Voice:** M1 | **Language:** en

## Results

| Scenario | Median (s) | p95 (s) | Min (s) | Max (s) |
|----------|------------|---------|---------|---------|
| Cold (new `TTS()` per iteration) | 0.813 | 0.847 | 0.768 | 0.889 |
| Warm (reuse loaded `TTS`) | 0.822 | 1.218 | 0.787 | 1.766 |

## Notes

- Cold includes per-iteration `TTS()` construction and model load.
- MCP server uses eager `_tts` at import (warm path after first load).
- Compare against HTTP-wrapped alternatives on the same hardware before publishing latency claims.
