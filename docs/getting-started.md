# Getting Started with YTAI

This guide walks through installing the YTAI Python SDK and using it for the first time.

## Prerequisites

- Python 3.10 or later
- pip (comes with Python)
- ffmpeg (optional; required only for full video+audio downloads and clipping)

## Installation

Install from source:

```bash
git clone https://github.com/vibheksoni/youtube-ai.git
cd youtube-ai
pip install -e .
```

For development (includes pytest and pytest-asyncio):

```bash
pip install -e ".[dev]"
```

Verify the installation:

```bash
python -c "from youtube_ai import YouTubeClient; print('OK')"
```

### ffmpeg (optional)

ffmpeg is only needed when downloading full video+audio (the SDK muxes separate
video-only and audio-only streams) or when using `start_time`/`end_time` clipping.

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

The SDK auto-discovers ffmpeg via `$PATH`.

## Your first search

```python
from youtube_ai import YouTubeClient

client = YouTubeClient()
results = client.search("machine learning", limit=10)

for item in results["results"]:
    if item["type"] == "video":
        print(f"{item['title']} ({item['duration']})")
        print(f"  Channel: {item['channel']['name']}")
        print(f"  Views: {item['views']}")
        print()

client.close()
```

## Using the context manager

The client manages a curlcffi HTTP session. Use it as a context manager to ensure
the session is properly closed:

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    results = client.search("python tutorial", limit=5)
    print(f"Found {results['count']} results")
```

## Getting video details

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    # Full video data: metadata + streaming + captions + related
    video = client.get_video("dQw4w9WgXcQ")
    details = video["details"]

    print(f"Title: {details['title']}")
    print(f"Author: {details['author']}")
    print(f"Views: {details['view_count']}")
    print(f"Likes: {details['likes']}")
    print(f"Duration: {details['length_seconds']}s")
    print(f"Keywords: {', '.join(details['keywords'])}")

    # Streaming formats
    for fmt in video["streaming_data"]["formats"]:
        print(f"  {fmt['quality_label']} ({fmt['mime_type']})")

    # Related videos
    for related in video["related_videos"][:5]:
        print(f"  Related: {related['title']}")
```

## Getting a transcript

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    transcript = client.get_transcript("dQw4w9WgXcQ", language_codes=("en",))

    print(f"Language: {transcript['language']}")
    print(f"Generated: {transcript['is_generated']}")
    print()

    for snippet in transcript["snippets"][:10]:
        print(f"[{snippet['start']:.1f}s] {snippet['text']}")

    # List all available languages
    for track in transcript["available_tracks"]:
        print(f"  {track['language_code']}: {track['name']}")
```

## Getting comments

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    result = client.get_comments("dQw4w9WgXcQ", limit=5)

    for comment in result["comments"]:
        print(f"@{comment['author']} ({comment['published_time']})")
        print(f"  {comment['text']}")
        print(f"  Likes: {comment['likes']}, Replies: {comment['reply_count']}")
        print()

    # Paginate to next page
    if result["continuation_token"]:
        page2 = client.get_comments(
            "dQw4w9WgXcQ",
            continuation_token=result["continuation_token"],
        )
        print(f"Page 2: {len(page2['comments'])} comments")
```

## Downloading a video

```python
from youtube_ai import YouTubeClient, VideoQuality, DownloadMode, download_video, get_download_options

with YouTubeClient() as client:
    # Inspect available qualities and formats first
    options = get_download_options("dQw4w9WgXcQ", client=client)
    print(options["available_qualities"])   # ['144p', '240p', '360p', ...]
    print(options["supported_modes"])       # ['full', 'video-only', 'audio-only']

    # Full video with audio (default mode)
    path = download_video(
        "dQw4w9WgXcQ",
        quality=VideoQuality.P720,
        output_path="./downloads",
        client=client,
    )
    print(f"Saved to: {path}")

    # Video-only (no audio)
    video_path = download_video(
        "dQw4w9WgXcQ",
        quality="144p",
        mode=DownloadMode.VIDEO_ONLY,
        client=client,
    )

    # Audio-only (no video)
    audio_path = download_video(
        "dQw4w9WgXcQ",
        mode=DownloadMode.AUDIO_ONLY,
        client=client,
    )

    # Clipped segment from 30s to 90s
    clip_path = download_video(
        "dQw4w9WgXcQ",
        quality="360p",
        start_time=30,
        end_time=90,
        client=client,
    )

    # With a progress callback
    def on_progress(downloaded, total, percentage):
        print(f"\r{percentage}% ({downloaded}/{total})", end="")

    download_video(
        "dQw4w9WgXcQ",
        quality="720p",
        progress_callback=on_progress,
        client=client,
    )
```

> **Backward compatibility:** `audio_only=True` still works as an alias for
> `mode=DownloadMode.AUDIO_ONLY`. String quality values (`"720p"`) are accepted
> alongside the `VideoQuality` enum.

## Channel information

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    # Channel metadata
    info = client.get_channel_info("UCuAXFkgsw1L7xaCfnd5JJOw")
    print(f"Channel: {info['title']}")
    print(f"Subscribers: {info['subscribers']}")
    print(f"Videos: {info['video_count']}")

    # Channel's uploaded videos (with limit)
    videos = client.get_channel_videos("UCuAXFkgsw1L7xaCfnd5JJOw", limit=10)
    for v in videos[:5]:
        print(f"  {v['title']} ({v['duration']})")
```

## Trending videos

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    trending = client.get_trending(limit=10)
    for v in trending:
        print(f"  {v['title']} - {v['channel']['name']}")
```

## Search pagination

```python
from youtube_ai import YouTubeClient

with YouTubeClient() as client:
    # First page
    page1 = client.search("react tutorial", limit=20)
    print(f"Page 1: {page1['count']} results")

    # Next page using continuation token
    if page1["continuation_token"]:
        page2 = client.search(
            "react tutorial",
            limit=20,
            continuation_token=page1["continuation_token"],
        )
        print(f"Page 2: {page2['count']} results")
```

## Using the cache

The cache is automatic and on by default. You can customize it:

```python
from youtube_ai import YouTubeClient, Cache

# Custom cache directory and TTL
cache = Cache(cache_dir="./my_cache", ttl=7200)
client = YouTubeClient(cache=cache)

results = client.search("test")  # cached for 7200 seconds

# Disable cache for a single call
results = client.search("test", use_cache=False)

# Inspect cache stats
stats = cache.stats()
print(f"Active entries: {stats['active']}")

# Clear all cached data
cache.clear()

client.close()
```

## Using the CLI

After installation, the `ytai` command is available:

```bash
ytai search "python tutorial" --limit 10
ytai video dQw4w9WgXcQ
ytai transcript dQw4w9WgXcQ --lang en
ytai comments dQw4w9WgXcQ --limit 5
ytai download-options dQw4w9WgXcQ
ytai download dQw4w9WgXcQ --quality 720p --output ./downloads
ytai download dQw4w9WgXcQ --video-only --quality 144p
ytai download dQw4w9WgXcQ --audio-only
ytai download dQw4w9WgXcQ --quality 360p --start 30 --end 90
ytai channel UCuAXFkgsw1L7xaCfnd5JJOw
ytai channel-videos UCuAXFkgsw1L7xaCfnd5JJOw --limit 10
ytai trending --limit 10
ytai formats dQw4w9WgXcQ
```

See [cli-reference.md](cli-reference.md) for all CLI commands and options.

## Using the MCP server

The MCP server exposes SDK functionality as tools for AI assistants:

```bash
python -m mcp.server
```

See [mcp-server.md](mcp-server.md) for setup and configuration details.

## Using the FastAPI server

Start the local HTTP API after installation:

```bash
ytai-api
```

Open `http://127.0.0.1:8000/docs` for interactive Swagger documentation. See
[api-server.md](api-server.md) for all routes, curl examples, validation limits,
and deployment guidance.
