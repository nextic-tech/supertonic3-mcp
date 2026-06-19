"""MCP server wiring — fastmcp tools."""

from __future__ import annotations

from fastmcp import FastMCP

from supertonic3_mcp import tts

mcp = FastMCP(
    "supertonic3-mcp",
    instructions=(
        "On-device Supertonic 3 text-to-speech. "
        "For non-English text you MUST pass language= (ISO 639-1, e.g. ko, es). "
        "Call list_voices() and list_expressions() before speak()."
    ),
)


@mcp.tool
async def speak(
    text: str,
    voice_id: str | None = None,
    language: str | None = None,
    speed: float = 1.0,
    play: bool = False,
) -> str:
    """Convert text to speech and save a WAV file. Returns the absolute path and metadata.

    Args:
        text: 1–5000 characters; may include expression tags from list_expressions().
        voice_id: Built-in voice (M1–M5, F1–F5). See list_voices().
        language: ISO 639-1 code (en, ko, ja, …). Required for reliable non-English output.
        speed: Playback speed in [0.7, 2.0].
        play: If true, play audio on this machine (STDIO/local use only).
    """
    return await tts.speak(
        text=text,
        voice_id=voice_id,
        language=language,
        speed=speed,
        play=play,
    )


@mcp.tool
async def list_voices() -> list[dict[str, str | None]]:
    """List built-in Supertonic voice styles."""
    return await tts.list_voices()


@mcp.tool
async def list_expressions() -> list[dict[str, str]]:
    """List inline expression tags (e.g. <laugh>) usable inside speak() text."""
    return await tts.list_expressions()
