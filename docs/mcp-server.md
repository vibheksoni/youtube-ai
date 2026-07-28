# YTAI MCP Server

The YTAI MCP server exposes SDK functionality as tools that AI assistants
can call. It is built on [FastMCP](https://github.com/jlowin/fastmcp) and uses
the same `YouTubeClient` as the SDK and CLI.

## Overview

The MCP server wraps each `YouTubeClient` method as an MCP tool. It exposes
**9 tools**: search, metadata, transcripts, comments, channels, trending, and
streaming data. The `download_video` function is intentionally excluded from
the MCP server to keep it focused on search and metadata operations.

| Tool | SDK Method | Description |
|------|-----------|-------------|
| `search_videos` | `client.search()` | Search YouTube for videos, channels, playlists |
| `get_video` | `client.get_video()` | Full video data: metadata, streaming, captions, related |
| `get_video_info` | `client.get_video_info()` | Video metadata only |
| `get_transcript` | `client.get_transcript()` | Video transcript with timestamps |
| `get_streaming_data` | `client.get_streaming_data()` | Streaming formats with URLs |
| `get_channel_info` | `client.get_channel_info()` | Channel metadata |
| `get_channel_videos` | `client.get_channel_videos()` | Channel's uploaded videos |
| `get_trending` | `client.get_trending()` | Current trending videos |
| `get_comments` | `client.get_comments()` | Paginated comments for a video |

## Running the server

```bash
python -m mcp.server
```

The server starts in stdio mode by default, which is the standard transport for
MCP servers that are launched by a client process.

## Configuration

### Claude Desktop

Add the server to your Claude Desktop configuration file.

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ytai": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/youtube-ai"
    }
  }
}
```

After saving the configuration, restart Claude Desktop. The YTAI tools
will appear in the available tools list.

### Other MCP clients

The server uses stdio transport. Any MCP-compatible client that can spawn a
process and communicate over stdin/stdout can connect. Point your client to:

```
command: python
args: ["-m", "mcp.server"]
cwd: /path/to/youtube-ai
```

## Tool parameters

### search_videos

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | yes | | Search query |
| `limit` | `int` | no | `20` | Max results |
| `filter_type` | `str` | no | `None` | Filter: `video`, `channel`, `playlist`, `movie` |

### get_video

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_id` | `str` | yes | | YouTube video ID |

### get_video_info

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_id` | `str` | yes | | YouTube video ID |

### get_transcript

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_id` | `str` | yes | | YouTube video ID |
| `language` | `str` | no | `"en"` | Preferred language code |

### get_streaming_data

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_id` | `str` | yes | | YouTube video ID |

### get_channel_info

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel_id` | `str` | yes | | YouTube channel ID |

### get_channel_videos

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel_id` | `str` | yes | | YouTube channel ID |
| `limit` | `int` | no | `30` | Max videos to return |

### get_trending

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | `int` | no | `20` | Max videos to return |

### get_comments

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_id` | `str` | yes | | YouTube video ID |
| `limit` | `int` | no | `20` | Max comments to return |
| `continuation_token` | `str` | no | `None` | Token for next page of comments |

## Caching

The MCP server uses the same SQLite cache as the SDK. Cached responses are
served instantly without hitting YouTube. The cache database is at
`~/.cache/youtube-ai/cache.db` by default.

## Error handling

All tools catch exceptions and return a structured error dict instead of
raising:

```python
{"error": "InnerTubeError", "message": "Connection failed after 3 retries: ..."}
```

This allows MCP clients to display errors gracefully without crashing.

## Example usage from a client

See `examples/mcp_client_example.py` for a complete example of connecting to
the server and calling tools programmatically.
