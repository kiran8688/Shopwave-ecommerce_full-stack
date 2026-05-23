# mcp-servers/custom_player/server.py
# ─────────────────────────────────────────────────────────────────────────────
# MCP Custom Player Server
# Provides tools to control and interface with a custom media/video player
# for product demonstrations and rich media on the ShopWave platform.
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="shopwave-custom-player", dependencies=["asyncpg"])

# In-memory mock state for the player
_player_state = {
    "status": "stopped",
    "current_media_id": None,
    "volume": 50,
    "playback_speed": 1.0,
    "timestamp": 0.0
}

@mcp.tool()
async def play_media(media_id: str) -> Dict[str, Any]:
    """
    Start playback of a specific media asset (e.g., product showcase video).
    
    Args:
        media_id: Unique identifier for the media asset.
    """
    _player_state["current_media_id"] = media_id
    _player_state["status"] = "playing"
    return {
        "action": "play",
        "media_id": media_id,
        "status": "success",
        "state": _player_state
    }

@mcp.tool()
async def pause_media() -> Dict[str, Any]:
    """
    Pause the currently playing media.
    """
    if _player_state["status"] == "playing":
        _player_state["status"] = "paused"
    return {
        "action": "pause",
        "status": "success",
        "state": _player_state
    }

@mcp.tool()
async def stop_media() -> Dict[str, Any]:
    """
    Stop playback and reset the timestamp.
    """
    _player_state["status"] = "stopped"
    _player_state["timestamp"] = 0.0
    return {
        "action": "stop",
        "status": "success",
        "state": _player_state
    }

@mcp.tool()
async def get_player_state() -> Dict[str, Any]:
    """
    Retrieve the current status, volume, and playback state of the custom player.
    """
    return {
        "action": "get_state",
        "state": _player_state
    }

@mcp.tool()
async def set_volume(level: int) -> Dict[str, Any]:
    """
    Set the audio volume of the player.
    
    Args:
        level: Integer between 0 (mute) and 100.
    """
    clamped_level = max(0, min(100, level))
    _player_state["volume"] = clamped_level
    return {
        "action": "set_volume",
        "volume": clamped_level,
        "status": "success"
    }

@mcp.tool()
async def seek_media(timestamp_seconds: float) -> Dict[str, Any]:
    """
    Seek to a specific timestamp in the media.
    
    Args:
        timestamp_seconds: The time in seconds to jump to.
    """
    _player_state["timestamp"] = max(0.0, timestamp_seconds)
    return {
        "action": "seek",
        "timestamp": _player_state["timestamp"],
        "status": "success"
    }


if __name__ == "__main__":
    port_str = os.environ.get("PORT", "8007")
    try:
        port = int(port_str)
    except ValueError:
        port = 8007
    mcp.run(transport="sse", host="0.0.0.0", port=port)
