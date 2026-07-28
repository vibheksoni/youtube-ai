"""

YTAI MCP Server



Exposes the youtube_ai SDK as MCP tools via FastMCP.



Run with:

    python -m mcp.server

    python mcp/server.py

"""



from __future__ import annotations



import sys

from pathlib import Path



















_THIS_DIR = str(Path(__file__).resolve().parent)

_saved_mcp_modules: dict[str, object] = {}

for key in list(sys.modules):

    if key == "mcp" or key.startswith("mcp."):

        mod = sys.modules.pop(key)

        _saved_mcp_modules[key] = mod



_removed_paths: list[tuple[int, str]] = []

for i in range(len(sys.path) - 1, -1, -1):

    p = sys.path[i]

    try:

        if Path(p).resolve() == Path(_THIS_DIR).resolve() or Path(p).resolve() == Path(_THIS_DIR).parent.resolve():

            _removed_paths.append((i, sys.path.pop(i)))

    except (ValueError, OSError):

        pass







_SDK_DIR = Path(__file__).resolve().parent.parent / "sdk"

if str(_SDK_DIR) not in sys.path:

    sys.path.insert(0, str(_SDK_DIR))



from fastmcp import FastMCP







sys.modules.update(_saved_mcp_modules)

for idx, p in _removed_paths:

    if p not in sys.path:

        sys.path.insert(idx, p)



from youtube_ai import YouTubeClient





_client: YouTubeClient | None = None





def _get_client() -> YouTubeClient:

    """Return the shared YouTubeClient, creating it on first use."""

    global _client

    if _client is None:

        _client = YouTubeClient()

    return _client





def _error(exc: Exception) -> dict:

    """Format an exception into a structured error dict."""

    return {

        "error": type(exc).__name__,

        "message": str(exc),

    }





mcp = FastMCP("ytai")





@mcp.tool()

def search_videos(

    query: str,

    limit: int = 20,

    filter_type: str | None = None,

) -> dict:

    """Search YouTube for videos matching *query*.



    Args:

        query: Search term.

        limit: Maximum number of results (default 20).

        filter_type: Optional filter — e.g. "video", "channel", "playlist".



    Returns:

        Dict with ``results``, ``continuation_token``, and ``count`` keys,

        or an ``error`` dict on failure.

    """

    try:

        return _get_client().search(

            query, limit=limit, filter_type=filter_type

        )

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_video(video_id: str) -> dict:

    """Get full video metadata, streaming data, captions, and related videos.



    Args:

        video_id: The 11-character YouTube video ID.



    Returns:

        Full video dict or an ``error`` dict on failure.

    """

    try:

        return _get_client().get_video(video_id)

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_video_info(video_id: str) -> dict:

    """Get lightweight video metadata (title, author, etc.).



    Args:

        video_id: The 11-character YouTube video ID.



    Returns:

        Video info dict or an ``error`` dict on failure.

    """

    try:

        return _get_client().get_video_info(video_id)

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_transcript(video_id: str, language: str = "en") -> dict:

    """Get the transcript / captions for a video.



    Args:

        video_id: The 11-character YouTube video ID.

        language: Preferred language code (default ``"en"``).



    Returns:

        Dict with ``snippets``, ``language``, ``language_code``, etc.,

        or an ``error`` dict on failure.

    """

    try:

        return _get_client().get_transcript(

            video_id, language_codes=(language,)

        )

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_streaming_data(video_id: str) -> dict:

    """Get streaming formats (progressive + adaptive) and manifest URLs.



    Args:

        video_id: The 11-character YouTube video ID.



    Returns:

        Dict with ``formats``, ``adaptive_formats``, ``hls_manifest_url``,

        ``dash_manifest_url``, or an ``error`` dict on failure.

    """

    try:

        return _get_client().get_streaming_data(video_id)

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_channel_info(channel_id: str) -> dict:

    """Get channel metadata (title, avatar, subscriber count, etc.).



    Args:

        channel_id: YouTube channel ID (``UC…``).



    Returns:

        Channel info dict or an ``error`` dict on failure.

    """

    try:

        return _get_client().get_channel_info(channel_id)

    except Exception as exc:

        return _error(exc)





@mcp.tool()

def get_channel_videos(channel_id: str, limit: int = 30) -> list:

    """Get a list of recent videos from a channel.



    Args:

        channel_id: YouTube channel ID (``UC…``).

        limit: Maximum number of videos to return (default 30).



    Returns:

        List of video dicts, or ``[{"error": ...}]`` on failure.

    """

    try:

        return _get_client().get_channel_videos(channel_id, limit=limit)

    except Exception as exc:

        return [_error(exc)]





@mcp.tool()

def get_trending(limit: int = 20) -> list:

    """Get the current trending videos list.



    Args:

        limit: Maximum number of videos to return (default 20).



    Returns:

        List of video dicts, or ``[{"error": ...}]`` on failure.

    """

    try:

        return _get_client().get_trending(limit=limit)

    except Exception as exc:

        return [_error(exc)]





@mcp.tool()

def get_comments(

    video_id: str,

    limit: int = 20,

    continuation_token: str | None = None,

) -> dict:

    """Get comments for a YouTube video.



    Args:

        video_id: The 11-character YouTube video ID.

        limit: Maximum comments to return (default 20).

        continuation_token: Token for next page of comments.



    Returns:

        Dict with ``comments`` list and ``continuation_token``, or an ``error`` dict.

    """

    try:

        return _get_client().get_comments(

            video_id, limit=limit, continuation_token=continuation_token

        )

    except Exception as exc:

        return _error(exc)





def main() -> None:

    """Entry point — starts the MCP server."""

    mcp.run()





if __name__ == "__main__":

    main()
