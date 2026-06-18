# Supertonic SDK Spike Result (T1)

**Date:** 2026-06-16  
**SDK version:** supertonic 1.3.1  
**Python:** 3.12.8  
**Platform:** macOS-26.5.1-arm64 (Apple Silicon)

**Gate status:** PASS — direct in-process synthesis works. Proceed with direct-SDK MCP architecture.

---

## 1. Direct synthesis without `supertonic serve`

**PASS.** `TTS(auto_download=True)` + `tts.synthesize(...)` produces audio with no HTTP daemon.

```python
from supertonic import TTS
tts = TTS(auto_download=True)
style = tts.get_voice_style(voice_name="M1")
wav, dur = tts.synthesize("Hello test.", voice_style=style, lang="en", speed=1.0)
```

- `wav`: `numpy.ndarray` shape `(1, N)`, `float32`
- `dur`: duration in seconds (numpy scalar)

---

## 2. Voice list API

**API:** `tts.voice_style_names` (list of str)

**Values (10 built-in):** `F1`, `F2`, `F3`, `F4`, `F5`, `M1`, `M2`, `M3`, `M4`, `M5`

**Style object:** `tts.get_voice_style(voice_name="M1")` → `supertonic.core.Style`

**Note:** SDK does not expose per-voice language/gender metadata. `list_voices()` will return `voice_id` plus inferred gender from name prefix (`M`/`F`) and `language_code: null` unless we add a static map later.

---

## 3. Expression metadata API

**No SDK callable.** `hasattr(tts, "list_expressions")` is false; no expression-related attrs on `TTS`.

**Implementation:** Ship curated list from Supertone docs (10 inline tags). Ground truth in `list_expressions()` module constant, documented as sourced from Supertonic 3 README.

| tag | description |
|-----|-------------|
| `<laugh>` | Natural laugh vocalization |
| `<breath>` | Breath sound |
| `<sigh>` | Sigh vocalization |
| `<gasp>` | Gasp vocalization |
| `<cough>` | Cough vocalization |
| `<hm>` | Thinking hum |
| `<oh>` | Exclamation "oh" |
| `<um>` | Filler "um" |
| `<uh>` | Filler "uh" |
| `<pause>` | Short pause |

---

## 4. Language selection

**API:** `lang="ko"` (and other ISO 639-1 codes) on `synthesize()`.

**Verified:** `lang="ko"` with Korean text succeeds.

**Supported:** 31 language codes + `na` fallback per SDK docs.

---

## 5. Speed control

**Parameter:** `speed: float` on `synthesize()`, default `1.05`

**SDK-enforced range:** **0.7 to 2.0** (0.5 rejected with error)

**Implementation note:** Validate `[0.7, 2.0]` at MCP layer to match SDK (CEO plan said 0.5 but SDK rejects it).

---

## 6. Output format

| Property | Value |
|----------|-------|
| In-memory | `float32` ndarray, shape `(1, samples)` |
| Write | `tts.save_audio(wav, path)` |
| WAV channels | 1 (mono) |
| Sample rate | **44100 Hz** |
| Sample width | 16-bit PCM |

Model cache: `~/.cache/supertonic3/` when `auto_download=True`.

---

## 7. License (Docker redistribution)

| Component | License |
|-----------|---------|
| Python package (supertonic) | MIT (`License-Expression: MIT`) |
| Model weights (HuggingFace `Supertone/supertonic-3`) | **OpenRAIL-M** |

**Docker v1.1:** OpenRAIL-M permits distribution with use restrictions — review full license before baking weights into public image. MIT code is fine to redistribute.

---

## 8. Thread safety

**Spike:** 4 concurrent `synthesize()` calls from `ThreadPoolExecutor(max_workers=2)` completed without errors.

**Production:** Wrap `synthesize()` in `asyncio.Lock` (inference only). ONNX session is serialized per SDK docs for HTTP batch as well.

---

## 9. Cold / warm FSL (58-char benchmark text, M1, en)

Text: `Hello, this is a test of Supertonic 3 text to speech.`

| Scenario | Median (s) | p95 (s) | Min (s) | Max (s) |
|----------|------------|---------|---------|---------|
| Cold (10 runs, model already loaded in process) | 0.880 | 0.986 | 0.827 | 0.987 |
| Warm (10 runs) | 0.908 | 1.121 | 0.871 | 1.606 |

**Note:** Spike reused one `TTS` instance (eager load). True cold-start (new process) will include ~model init on first import; measure separately in `benchmark/run.py`.

---

## Implementation decisions locked by spike

1. Use `get_voice_style(voice_name=...)` + `synthesize(..., voice_style=style, lang=..., speed=...)`
2. `list_voices()` reads `voice_style_names` at runtime
3. `list_expressions()` returns curated JSON (no SDK API)
4. Speed validation: `[0.7, 2.0]`
5. WAV via `tts.save_audio()` at 44100 Hz mono
