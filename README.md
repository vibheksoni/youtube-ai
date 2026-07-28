# YTAI: Python YouTube SDK, CLI and MCP Server

![YTAI - Python YouTube SDK, CLI and MCP Server](https://github.com/vibheksoni/youtube-ai/raw/main/assets/YTAI.png)

YTAI is a Python SDK, command-line interface, and MCP server for YouTube
search, metadata, transcripts, comments, channels, and media downloads without a
user-supplied YouTube Data API key.

It uses YouTube's public InnerTube interface through `curl_cffi` browser
impersonation, dynamically refreshes web-client configuration, and caches public
responses locally with SQLite and `orjson`.

> YTAI is an independent project. It is not affiliated with or endorsed by
> YouTube or Google. Use it in accordance with applicable terms, copyright law,
> and local regulations.

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Downloads](#downloads)
- [MCP server](#mcp-server)
- [FastAPI server](#fastapi-server)
- [Documentation](#documentation)
- [Testing](#testing)
- [Limitations](#limitations)

## Features

- Search videos, channels, and playlists with filters and pagination
- Retrieve metadata, likes, captions, related videos, and comments
- Fetch timestamped transcripts with language selection and XML fallback
- Inspect channels, recent uploads, and popular videos
- Download full video with audio, video-only, audio-only, or a time range
- Resume interrupted downloads with ranged transfers and per-chunk retries
- Cache responses in SQLite with operation-specific TTLs
- Use the Python SDK, Rich-powered `ytai` CLI, nine read-only MCP tools, or the FastAPI service

## Installation

Requirements:

- Python 3.10 or newer
- No separate FFmpeg installation is required for downloads; YTAI bundles FFmpeg through `imageio-ffmpeg`

Clone and install the project:

```bash
git clone https://github.com/vibheksoni/youtube-ai.git
cd youtube-ai
python -m pip install -e .
```

Install development dependencies when running tests:

```bash
python -m pip install -e ".[dev]"
```

FFmpeg is bundled automatically for Windows, macOS, and Linux when you install YTAI.
If you prefer a system build, it is used when `ffmpeg` is on `PATH`. To pin an
explicit binary, set `YTAI_FFMPEG_PATH` to its full path:

```powershell
$env:YTAI_FFMPEG_PATH = "C:\tools\ffmpeg\bin\ffmpeg.exe"
```

`YTAI_API_KEY` is an optional offline fallback when live configuration cannot be
fetched. It is read from the environment and is never stored in the repository.

For environment setup and first-run guidance, continue with
[Getting Started](docs/getting-started.md).

## Quick start

Use `YouTubeClient` as a context manager so its HTTP session is closed cleanly:

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    results = client.search("python tutorial", limit=5, filter_type="video")
    for item in results["results"]:
        print(item["title"], item["url"])

    video = client.get_video("dQw4w9WgXcQ")
    print(video["details"]["title"])
    print(video["details"]["likes"])

    transcript = client.get_transcript("dQw4w9WgXcQ", language_codes=("en",))
    for segment in transcript["snippets"][:5]:
        print(f"{segment['start']:.1f}s: {segment['text']}")
```

Common CLI commands:

```bash
ytai search "python tutorial" --limit 10 --filter video
ytai video dQw4w9WgXcQ
ytai transcript dQw4w9WgXcQ --lang en
ytai comments dQw4w9WgXcQ --limit 20
```

See the [Python API reference](docs/api-reference.md) and
[CLI reference](docs/cli-reference.md) for complete signatures and commands.

## Downloads

Inspect available qualities, codecs, stream sizes, and modes before downloading:

```bash
ytai download-options dQw4w9WgXcQ
```

Download a full video with audio:

```bash
ytai download dQw4w9WgXcQ --quality 720p --output ./downloads
```

Video-only, audio-only, and clipping are opt-in:

```bash
ytai download dQw4w9WgXcQ --quality 1080p --video-only
ytai download dQw4w9WgXcQ --audio-only
ytai download dQw4w9WgXcQ --quality 360p --start 30 --end 90
```

The SDK also exposes `VideoQuality`, `DownloadMode`, `get_download_options()`,
and `download_video()`. See the [download API](docs/api-reference.md#download_video)
and [download example](examples/download_video.py).

## MCP server

Start the FastMCP server:

```bash
python mcp/server.py
```

It exposes nine read-only tools for search, video data, transcripts, streaming
formats, comments, channels, and popular videos. Media downloading is
intentionally available through the SDK and CLI only.

See [MCP Server Setup](docs/mcp-server.md) for client configuration and tool
parameters.

## FastAPI server

Start the versioned HTTP API:

```bash
ytai-api
```

Swagger UI is available at `http://127.0.0.1:8000/docs`. The API covers search,
video data, transcripts, comments, formats, download options, channels, and
popular videos. See the [FastAPI Server Guide](docs/api-server.md) for routes,
curl examples, configuration, validation, and deployment guidance.

## Documentation

- [Getting Started](docs/getting-started.md): prerequisites, installation, and first workflows
- [API Reference](docs/api-reference.md): public classes, functions, enums, and return shapes
- [CLI Reference](docs/cli-reference.md): every `ytai` command and option
- [MCP Server](docs/mcp-server.md): server setup, tools, parameters, and errors
- [FastAPI Server](docs/api-server.md): HTTP routes, OpenAPI docs, configuration, and examples
- [Examples](examples/): runnable search, metadata, transcript, comment, channel, download, and MCP scripts

## Testing

The end-to-end suite calls the real YouTube InnerTube and Google Video
boundaries. It covers search, transcripts, comments, channels, MCP tools, CLI
commands, download modes, clipping, resumable ranges, and ffmpeg output streams.

```bash
pytest tests/test_e2e.py -v
```

## Limitations

- Private, members-only, and most age-restricted content is unavailable without authentication.
- InnerTube endpoints and renderer structures can change without notice.
- Channel uploads currently return the first available page.
- Adaptive full-video downloads and clipping use the bundled FFmpeg executable (or `YTAI_FFMPEG_PATH` when configured).
- Playlist contents are not currently fetched.

## Credits

YTAI acknowledges these public projects as references for protocol details,
format mappings, and implementation ideas:

- [YouTube.js](https://github.com/LuanRT/YouTube.js)
- [innertube-go](https://github.com/raHULK777/innertube-go)
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

## License

MIT, as declared in `pyproject.toml`.
