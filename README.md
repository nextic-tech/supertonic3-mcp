# supertonic3-mcp

Local, on-device TTS for Claude & Cursor, powered by Supertonic 3. No API key. No cloud. An internal tool open-sourced by [Halozen](https://halozen.ai) — we build AI compliance intelligence for construction.

*Not affiliated with Supertone Inc.*

Expose `speak`, `list_voices`, and `list_expressions` to Claude Desktop, Cursor, or any MCP client over **STDIO**.

## Quick start (TTHW < 3 min)

```bash
git clone https://github.com/nextic-tech/supertonic3-mcp && cd supertonic3-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Optional: pre-download model for offline use (~400MB)
supertonic3-mcp preload

# Run MCP server (STDIO)
supertonic3-mcp
```

### Cursor MCP config

Add to `.cursor/mcp.json` (or Cursor Settings → MCP):

```json
{
  "mcpServers": {
    "supertonic3": {
      "command": "/absolute/path/to/supertonic-tts/.venv/bin/supertonic3-mcp",
      "args": []
    }
  }
}
```

First server start downloads the Supertonic model into `~/.cache/supertonic3/` unless you ran `preload` first.

## Tools

| Tool | Description |
|------|-------------|
| `speak` | Synthesize text to a WAV file; returns absolute path + metadata |
| `list_voices` | Built-in voices (`voice_id`, `gender`) |
| `list_expressions` | Inline tags (`<laugh>`, `<breath>`, …) with descriptions |

### `speak` parameters

- `text` — 1–5000 characters; expression tags allowed
- `voice_id` — optional (`M1`, `F1`, …)
- `language` — ISO 639-1 (`en`, `ko`, `ja`, …). **For non-English text, always set `language=`.** Defaults to `en`.
- `speed` — `0.7` to `2.0` (SDK range)
- `play` — if `true`, plays audio on **this machine** via `afplay` (macOS) or `aplay` (Linux). Unsupported on Windows.

WAV files are written to `/tmp/supertonic_*.wav` (macOS/Linux). Windows is not supported for synthesis output paths in v1.0.

Example return:

```text
Audio saved to /tmp/supertonic_abc123.wav (1.4s, voice: M1, lang: en)
```

## Performance (this repo)

Measured on Apple M3, supertonic 1.3.1 — see [benchmark/results.md](benchmark/results.md).

| Scenario | Median FSL |
|----------|------------|
| Warm (model loaded) | ~0.82s |
| Cold (new `TTS()` per call) | ~0.81s |

FSL = time from `synthesize()` through WAV written (no streaming, no `play=True`).

Re-run: `python benchmark/run.py`

## Offline use

```bash
supertonic3-mcp preload
```

Downloads ONNX weights atomically to `~/.cache/supertonic3/` and prints SHA256 checksums. After preload, synthesis works without network access.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests mock the Supertonic SDK (no network in CI).

## Coming in v1.1

- `listen()` — Whisper speech-to-text (`pip install supertonic3-mcp[stt]`)
- SSE transport + Docker image for remote agents
- PyPI publish workflow

## License

MIT (this package). Supertonic SDK is MIT; model weights use [OpenRAIL-M](https://huggingface.co/Supertone/supertonic-3).

## Disclaimer

AI-generated speech is not a substitute for certified safety, legal, or medical guidance. For demonstration purposes only.
