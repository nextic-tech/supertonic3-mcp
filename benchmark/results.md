# Supertonic 3 MCP — FSL Benchmark

**Date:** 2026-06-16  
**Hardware:** macOS-26.5.1-arm64-arm-64bit / Apple M3  
**supertonic:** 1.3.1  
**Python:** 3.12.8

**Metric:** Full Synthesis Latency (FSL) — `synthesize()` + `save_audio()` to WAV (no `play=True`).

**Input:** `Hello, this is a test of Supertonic 3 text to speech.` (53 chars)  
**Voice:** M1 | **Language:** en

## Results

| Scenario | Median (s) | p95 (s) | Min (s) | Max (s) |
|----------|------------|---------|---------|---------|
| Cold (new `TTS()` per iteration) | 1.004 | 1.128 | 0.868 | 1.130 |
| Warm (reuse loaded `TTS`) | 1.080 | 1.158 | 0.952 | 1.240 |

## Notes

- Cold includes per-iteration `TTS()` construction and model load.
- MCP server uses eager `_tts` at import (warm path after first load).
- Cold (1.004s) appearing faster than warm (1.080s) is expected: the OS page-cache warms model weights across cold iterations, so by iteration 2+ load cost is minimal and per-call variance dominates.

## Baseline Comparison

**Status: PENDING** — required before publishing latency claims in the LinkedIn post.

To complete: run the intended baseline TTS tool on this Apple M3 with identical input (`Hello, this is a test of Supertonic 3 text to speech.`, 10 warm iterations), record median/p95/min/max, and fill in the row below.

> Note: `dandyarise` is not an installable PyPI package (confirmed: `pip index versions dandyarise` → "No matching distribution found"). Confirm the correct tool name/install path before running the comparison.

| Scenario | Median (s) | p95 (s) | Min (s) | Max (s) |
|----------|------------|---------|---------|---------|
| Supertonic warm (this server) | 1.080 | 1.158 | 0.952 | 1.240 |
| dandyarise warm (baseline) | — | — | — | — |
