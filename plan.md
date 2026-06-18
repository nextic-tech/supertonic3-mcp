# Supertonic 3 MCP Server — Implementation Plan

**Status:** ENG CLEARED. Run spike (T1) first — everything else is gated on it.
**Plan:** `~/.gstack/projects/supertonic-tts/ceo-plans/2026-06-15-supertonic3-mcp.md`

---

## Module Map

```
supertonic3_mcp/
  __init__.py
  __main__.py       ← CLI entry: stdio | sse | preload subcommands
  server.py         ← fastmcp wiring, tool registration
  tts.py            ← speak(), list_voices(), list_expressions(), _onnx_lock
  stt.py            ← listen(), _mic_lock
  lang.py           ← language resolution (explicit only, no langdetect)
  audio.py          ← /tmp sweep, WAV write, afplay/aplay
  errors.py         ← exception hierarchy

tests/
  conftest.py
  test_tts.py
  test_stt.py
  test_lang.py
  test_audio.py
  test_server.py
  test_errors.py

benchmark/
  run.py
  results.md

notes/
  spike-result.md   ← HARD GATE: written before any other code

Dockerfile
.dockerignore
pyproject.toml
.github/workflows/publish.yml
README.md
```

---

## Tasks

### Phase 1 — Spike (hard gate)

#### T1 · P1 · `notes/` · ~20 min
**Run prerequisite spike — validate 9 SDK items, commit `notes/spike-result.md`**

Spike must confirm before any implementation starts:
1. Direct synthesis works without `supertonic serve` (no daemon required)
2. `list_voices()` equivalent exists in SDK — what's the call?
3. `list_expressions()` / expression metadata — what shape does it return?
4. Language selection param (`lang="ko"` or equivalent)
5. Speed control parameter name and range
6. Output format (WAV) and sample rate (Hz)
7. License allows Docker redistribution of ONNX weights
8. SDK thread safety: does `asyncio.Lock` around `synthesize()` prevent crashes under concurrent calls?
9. Cold/warm FSL measurement — 10 iterations each, record median

Write findings to `notes/spike-result.md` and commit. Nothing in Phase 2 starts until that commit exists.

---

### Phase 2 — Core (P1, sequential)

#### T2 · P1 · `supertonic3_mcp/errors.py` · ~5 min
**Exception hierarchy**

```
Supertonic3MCPError (base)
├── SpeakError
│   ├── VoiceNotFoundError
│   └── TextTooLongError
└── STTError
    ├── WhisperModelError
    ├── MicrophoneError
    ├── MicrophonePermissionError
    └── NoAudioDeviceError
```

`ValueError` and `ImportError` are stdlib — do not wrap.

---

#### T3 · P1 · `supertonic3_mcp/tts.py` + `audio.py` · ~20 min
**`speak()` — async def, asyncio.Lock (inference only), empty text guard, /tmp sweep**

Key constraints:
- `_tts = TTS(auto_download=True)` at module level (eager load at import, not first call)
- `_onnx_lock = asyncio.Lock()` at module level
- Lock wraps only `_tts.synthesize(...)` — playback runs OUTSIDE the lock
- `text.strip() == ""` → raise `ValueError("text must be non-empty")` before acquiring lock
- `len(text) > 5000` → raise `TextTooLongError`
- At start of each call: delete `/tmp/supertonic_*.wav` files older than 5 minutes
- Return value: `str` — file path + metadata (MCP-compatible, no bytes/base64)

```python
# module level
_tts = TTS(auto_download=True)
_onnx_lock = asyncio.Lock()

async def speak(text, voice_id=None, language=None, speed=1.0, play=False):
    if not text.strip():
        raise ValueError("text must be non-empty")
    if len(text) > 5000:
        raise TextTooLongError(f"text exceeds 5000 chars ({len(text)})")
    _sweep_tmp()                         # delete stale /tmp/supertonic_*.wav
    lang = resolve_language(language, voice_id)
    async with _onnx_lock:               # lock: inference only
        wav = _tts.synthesize(text, voice=voice_id or lang, speed=speed)
    tmp_path = _write_wav(wav)
    if play:
        audio.play(tmp_path)             # runs AFTER lock released
    return f"{tmp_path} | voice={voice_id or lang} | chars={len(text)}"
```

---

#### T4 · P1 · `supertonic3_mcp/tts.py` · ~10 min
**`list_voices()` and `list_expressions()`**

Both query the SDK at runtime (shape confirmed by spike T1 items 2 & 3). Return `str` (JSON-encoded list). Do not hardcode the lists — call SDK so it stays current.

---

#### T5 · P1 · `supertonic3_mcp/lang.py` · ~5 min
**Language resolution — explicit only, no langdetect**

| `language` param | `voice_id` param | Behavior |
|---|---|---|
| set | set | `voice_id` wins; `language` ignored |
| set | None | auto-select best voice for language |
| None | None | default to `"en"` — deterministic, no inference |

langdetect is permanently removed. Agents must pass `language=` explicitly.

---

#### T6 · P1 · `supertonic3_mcp/stt.py` · ~25 min
**`listen()` — async def, separate `_mic_lock`, sounddevice → Whisper**

```python
_mic_lock = asyncio.Lock()   # separate from _onnx_lock; speak() and listen() can overlap

async def listen(duration=5, language="en"):
    async with _mic_lock:
        audio_data = sounddevice.rec(int(duration * 16000), samplerate=16000, channels=1)
        sounddevice.wait()
    return whisper.transcribe(audio_data, language=language)["text"]
```

`_mic_lock` and `_onnx_lock` are independent — concurrent speak()+listen() is safe.

---

#### T7 · P1 · `supertonic3_mcp/stt.py` + `__main__.py` · ~5 min
**macOS mic permission check at startup**

On server start, call `sounddevice.query_devices()`. If it raises `PortAudioError` (permission denied), raise `MicrophonePermissionError` with human-readable instructions: "Grant microphone access in System Settings → Privacy & Security → Microphone."

---

#### T8 · P1 · `supertonic3_mcp/server.py` + `__main__.py` · ~15 min
**Server wiring — fastmcp, CLI subcommands, atomic preload**

`__main__.py` subcommands:
- `supertonic3-mcp` (no args) → STDIO transport
- `supertonic3-mcp --sse` → SSE transport on `0.0.0.0:8000`
- `supertonic3-mcp preload` → atomic model download (temp path → `os.replace()` on success), print checksums

`server.py`: register `speak`, `listen`, `list_voices`, `list_expressions` as fastmcp tools. All tool functions are `async def`.

---

### Phase 3 — Tests + Benchmark (P1)

#### T10 · P1 · `tests/` · ~25 min
**Full pytest suite — 42+ paths, 2 critical-gap tests**

All tests mock the supertonic SDK (no network in CI). Framework: pytest + pytest-asyncio.

Fixtures in `conftest.py`:
- `mock_tts` — patches `supertonic3_mcp.tts._tts`
- `mock_sounddevice` — patches sounddevice.rec / wait
- `mock_whisper` — patches whisper.transcribe
- `tmp_dir` — isolated /tmp
- `offline` — blocks all network calls

Critical-gap tests (must pass before ship):
1. `speak()` raises inside `_onnx_lock` → lock released → second call completes (no deadlock)
2. `preload` interrupted → no corrupt model in cache (atomic write verified)

Coverage target: 100% of 42 planned codepaths.

---

#### T9 · P1 · `benchmark/` · ~30 min
**FSL benchmark — 10 iterations, write `benchmark/results.md`**

Measure Full Synthesis Latency (time from `speak()` call to WAV written and str returned — no streaming):
- 10 cold-start iterations
- 10 warm iterations
- Record median, p95, min, max
- Compare vs dandyarise baseline (local TTS alternative)
- Update README with real numbers
- Required before LinkedIn post

---

### Phase 4 — Packaging (P2)

#### T11 · P2 · `Dockerfile` · ~15 min
**Docker — multi-stage, ffmpeg, /health, SSE default**

Use case: remote SSE agent deployment (speak() returns file path on server). NOT for local voice demo (use STDIO on host for that).

- Multi-stage build: builder → runtime
- Install ffmpeg in runtime stage
- `HEALTHCHECK` hits `GET /health`
- Atomic model download at container startup via `preload` subcommand
- Default CMD: `supertonic3-mcp --sse`

---

#### T12 · P2 · `pyproject.toml` + `publish.yml` · ~10 min
**Packaging + CI/CD**

- `pyproject.toml`: package name `supertonic3-mcp`, split extras `[stt]` for whisper+sounddevice deps, ffmpeg noted as system prereq
- `.github/workflows/publish.yml`: trigger on `v*` tag push, PyPI via trusted publisher (no API key stored)

---

#### T13 · P2 · `README.md` + `server.py` · ~15 min
**SSE transport + /health + README**

README structure:
1. STDIO user journey first (local voice demo, TTHW < 3 min)
2. Docker SSE journey second (remote agent deployment)
3. SSE warning: "listen() and play=True use the server's microphone/speakers, not the caller's. For voice I/O loops, use STDIO."
4. OSHA demo disclaimer

---

## Sequencing

```
T1 (spike)
  └── T2 (errors.py)
        └── T3 (speak)
              ├── T4 (list_voices/expressions)
              ├── T5 (lang.py)
              └── T6 (listen)
                    └── T7 (mic permission)
                          └── T8 (server + CLI)
                                ├── T10 (tests)     ← run after T2-T8 complete
                                └── T9 (benchmark)  ← run after T3 complete
T11, T12, T13 unblock after T8 + T10 pass
```

LinkedIn post only after `benchmark/results.md` is committed.

---

## Critical Failure Modes (must address in implementation)

| Failure | Fix |
|---|---|
| `speak()` raises inside `_onnx_lock` → deadlock | `async with` releases on exception; add `try/finally` to clean partial WAV |
| `preload` interrupted → partial model on disk | Download to temp path; `os.replace()` atomically on success |
| `listen()` wrong sample rate → garbled transcription | sounddevice 16kHz mono matches Whisper native format — document in conftest |
| `list_expressions()` SDK API changes → wrong shape | Spike item 3; verify shape in tests |

---

## Key Decisions (locked, do not re-litigate)

- **langdetect**: REMOVED. `language=None` → `"en"`. Agents pass `language=` explicitly.
- **asyncio.Lock scope**: inference only. Playback runs outside the lock.
- **`_mic_lock`**: separate from `_onnx_lock`. `speak()` and `listen()` can run concurrently.
- **`speak()`/`listen()` must be `async def`**: asyncio.Lock semantics require it.
- **Eager model load**: `_tts = TTS()` at module import, not first call.
- **Return type**: `str` (path + metadata), not bytes. MCP tools return `TextContent`.
- **FSL** (Full Synthesis Latency), not TTFA — no streaming.
- **Docker**: SSE transport for remote agents. STDIO for local voice demo.
- **CI/CD**: publish.yml on `v*` tag, trusted publisher, no stored API key.
