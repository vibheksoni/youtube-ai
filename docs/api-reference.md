# YTAI API Reference

Complete reference for the YTAI Python SDK public API.

## Classes

### YouTubeClient

```python
from youtube_ai import YouTubeClient
```

YouTube InnerTube client with browser impersonation. No user-supplied API key required.

#### Constructor

```python
YouTubeClient(
    client_name: str = "ANDROID",
    cache: Cache | None = None,
    impersonate: str = "chrome131",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client_name` | `str` | `"ANDROID"` | InnerTube client to use. Options: `"WEB"`, `"ANDROID"`, `"IOS"`, `"MWEB"`, `"TV_EMBEDDED"`, `"WEB_EMBEDDED"` |
| `cache` | `Cache \| None` | `None` | Custom cache instance. Creates a default `Cache()` if not provided |
| `impersonate` | `str` | `"chrome131"` | curlcffi browser impersonation target |

#### Methods

##### search

```python
client.search(
    query: str,
    limit: int = 20,
    filter_type: str | None = None,
    continuation_token: str | None = None,
    use_cache: bool = True,
) -> dict
```

Search YouTube for videos, channels, and playlists.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | Search query string |
| `limit` | `int` | `20` | Maximum number of results to return |
| `filter_type` | `str \| None` | `None` | Filter results by type: `"video"`, `"channel"`, `"playlist"`, `"movie"` |
| `continuation_token` | `str \| None` | `None` | Token from a previous search to get the next page |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict`

```python
{
    "results": [
        {
            "type": "video",  # or "channel", "playlist"
            "video_id": "dQw4w9WgXcQ",
            "title": "Video Title",
            "thumbnail": "https://...",
            "duration": "3:33",
            "duration_seconds": 213,
            "views": 1000000,
            "view_count_text": "1M views",
            "published": "12 years ago",
            "channel": {"name": "Channel Name", "id": "UC..."},
            "description": "Snippet text...",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
        # ... more results
    ],
    "continuation_token": "abc123...",  # str | None, for pagination
    "count": 20,
}
```

##### get_video

```python
client.get_video(
    video_id: str,
    use_cache: bool = True,
) -> dict
```

Get full video data including metadata, streaming data, captions, and related videos.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID (11 characters) |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict`

```python
{
    "video_id": "dQw4w9WgXcQ",
    "details": {
        "video_id": "dQw4w9WgXcQ",
        "title": "Video Title",
        "author": "Channel Name",
        "channel_id": "UC...",
        "length_seconds": 213,
        "view_count": 1000000,
        "description": "Full description...",
        "is_live": False,
        "is_private": False,
        "thumbnails": [{"url": "...", "width": 120, "height": 90}],
        "keywords": ["tag1", "tag2"],
        "average_rating": 4.5,
        "allow_ratings": True,
        "playability_status": "OK",
        "playability_reason": "",
        "likes": "19M",
    },
    "streaming_data": {
        "formats": [...],           # progressive (audio+video)
        "adaptive_formats": [...],  # video-only and audio-only
        "hls_manifest_url": "...",  # str | None
        "dash_manifest_url": "...", # str | None
    },
    "captions": [
        {
            "base_url": "https://...",
            "name": "English",
            "language_code": "en",
            "kind": "",
            "is_generated": False,
            "is_translatable": True,
            "track_id": "...",
        },
    ],
    "related_videos": [
        {
            "video_id": "...",
            "title": "...",
            # ... same structure as search video results
        },
    ],
}
```

##### get_video_info

```python
client.get_video_info(
    video_id: str,
    use_cache: bool = True,
) -> dict
```

Get video metadata only (no streaming data, captions, or related videos).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict` -- same structure as `get_video()["details"]`

##### get_streaming_data

```python
client.get_streaming_data(
    video_id: str,
    use_cache: bool = True,
) -> dict
```

Get streaming data (formats and URLs) for a video.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict`

```python
{
    "formats": [
        {
            "itag": 18,
            "url": "https://...",
            "mime_type": "video/mp4",
            "bitrate": 500000,
            "width": 640,
            "height": 360,
            "fps": 30,
            "quality": "medium",
            "quality_label": "360p",
            "duration_ms": 213000,
            "content_length": "12345678",
            "has_audio": True,
            "has_video": True,
            "is_progressive": True,
        },
    ],
    "adaptive_formats": [
        # video-only and audio-only formats
        # same structure as formats above
    ],
    "hls_manifest_url": "https://...",  # str | None
    "dash_manifest_url": "https://...", # str | None
}
```

##### get_transcript

```python
client.get_transcript(
    video_id: str,
    language_codes: tuple[str, ...] = ("en",),
    use_cache: bool = True,
) -> dict
```

Get transcript/captions for a video with timestamps.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID |
| `language_codes` | `tuple[str, ...]` | `("en",)` | Preferred language codes in priority order. Falls back to first available track. |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict`

```python
{
    "video_id": "dQw4w9WgXcQ",
    "language": "English",
    "language_code": "en",
    "is_generated": False,
    "snippets": [
        {
            "text": "We're no strangers to love",
            "start": 1.36,
            "duration": 1.68,
        },
        # ... more snippets
    ],
    "available_tracks": [
        {
            "language_code": "en",
            "name": "English",
            "is_generated": False,
        },
    ],
}
```

**Raises:** `InnerTubeError` if no captions are available for the video.

##### get_comments

```python
client.get_comments(
    video_id: str,
    limit: int = 20,
    continuation_token: str | None = None,
    use_cache: bool = True,
) -> dict
```

Get comments for a YouTube video. Uses a two-step flow: fetches a comment
continuation token from the `next` endpoint, then fetches comments via that
token. Supports pagination with `continuation_token`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID |
| `limit` | `int` | `20` | Maximum comments to return |
| `continuation_token` | `str \| None` | `None` | Token from a previous call for next page |
| `use_cache` | `bool` | `True` | Whether to use the cache (first page only) |

**Returns:** `dict`

```python
{
    "comments": [
        {
            "author": "Username",
            "text": "Comment text...",
            "likes": "1.2K",
            "reply_count": 5,
            "published_time": "2 years ago",
            "is_verified": False,
        },
    ],
    "continuation_token": "abc123...",  # str | None, for next page
}
```

##### get_channel_info

```python
client.get_channel_info(
    channel_id: str,
    use_cache: bool = True,
) -> dict
```

Get channel metadata. Handles both legacy `c4TabbedHeaderRenderer` and newer
`pageHeaderRenderer` / `pageHeaderViewModel` layouts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channel_id` | `str` | required | YouTube channel ID (starts with `UC`) |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `dict`

```python
{
    "channel_id": "UC_x5XG1OVGxI2tPvVMsMvQ",
    "title": "Channel Name",
    "avatar": "https://...",
    "subscribers": "1.5M subscribers",
    "banner": "https://...",
    "video_count": "500 videos",
}
```

##### get_channel_videos

```python
client.get_channel_videos(
    channel_id: str,
    limit: int = 30,
    use_cache: bool = True,
) -> list[dict]
```

Get a channel's uploaded videos. Selects the Videos tab via the
`EgZ2aWRlb3PyBgQKAjoA` browse params and parses `richGridRenderer` /
`lockupViewModel` items.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channel_id` | `str` | required | YouTube channel ID |
| `limit` | `int` | `30` | Maximum number of videos to return |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `list[dict]` -- list of video dicts with the same structure as search video results.

##### get_trending

```python
client.get_trending(
    limit: int = 20,
    use_cache: bool = True,
) -> list[dict]
```

Get current trending videos. YouTube deprecated the `FEtrending` browse
endpoint for unauthenticated InnerTube access, so this method uses the search
endpoint with a video filter as a trending proxy.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `20` | Maximum number of videos to return |
| `use_cache` | `bool` | `True` | Whether to use the cache |

**Returns:** `list[dict]` -- list of video dicts.

##### close

```python
client.close()
```

Close the underlying curlcffi session. Called automatically when used as a context manager.

---

### Cache

```python
from youtube_ai import Cache
```

SQLite-backed cache with orjson serialization and TTL expiry.

#### Constructor

```python
Cache(
    cache_dir: Path | str | None = None,
    ttl: int = 3600,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_dir` | `Path \| str \| None` | `None` | Directory for the SQLite database. Defaults to `~/.cache/youtube-ai/` |
| `ttl` | `int` | `3600` | Default TTL in seconds for cached entries |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get` | `(namespace: str, identifier: str) -> Any \| None` | Retrieve a cached value. Returns `None` if expired or missing. |
| `set` | `(namespace: str, identifier: str, value: Any, ttl: int \| None = None)` | Store a value with optional per-entry TTL. |
| `delete` | `(namespace: str, identifier: str)` | Delete a single cache entry. |
| `clear` | `()` | Delete all cache entries. |
| `cleanup_expired` | `()` | Remove all expired entries from the database. |
| `stats` | `() -> dict` | Return `{"total_entries": int, "expired_entries": int, "active": int}` |

---

## Functions

### download_video

```python
from youtube_ai import DownloadMode, VideoQuality, download_video

download_video(
    video_id: str,
    output_path: str | Path | None = None,
    quality: VideoQuality | str = VideoQuality.BEST,
    audio_only: bool = False,
    video_only: bool = False,
    mode: DownloadMode | str = DownloadMode.FULL,
    start_time: float | None = None,
    end_time: float | None = None,
    client: YouTubeClient | None = None,
    progress_callback: Callable[[int, int, int], None] | None = None,
    ffmpeg_path: str | Path | None = None,
) -> Path
```

Download in resumable ranges. Full mode combines separate video/audio streams
with the bundled `imageio-ffmpeg` executable, or with the binary configured by
`YTAI_FFMPEG_PATH`. Timestamp clipping and audio/video-only modes are opt-in.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | `str` | required | YouTube video ID |
| `output_path` | `str \| Path \| None` | `None` | Directory or full file path |
| `quality` | `VideoQuality \| str` | `VideoQuality.BEST` | `best`, `2160p`, `1440p`, `1080p`, `720p`, `480p`, `360p`, `240p`, or `144p` |
| `audio_only` | `bool` | `False` | Compatibility flag for audio-only output |
| `video_only` | `bool` | `False` | Output video without audio |
| `mode` | `DownloadMode \| str` | `DownloadMode.FULL` | `full`, `video-only`, or `audio-only` |
| `start_time` | `float \| None` | `None` | Optional start offset in seconds |
| `end_time` | `float \| None` | `None` | Optional end offset in seconds |
| `client` | `YouTubeClient \| None` | `None` | Reuse an existing client |
| `progress_callback` | `Callable \| None` | `None` | Called with `(downloaded_bytes, total_bytes, percentage)` |
| `ffmpeg_path` | `str \| Path \| None` | `None` | Optional FFmpeg executable path; overrides environment, PATH, and bundled resolution |

### get_download_options

```python
from youtube_ai import get_download_options

options = get_download_options(video_id, client=client, ffmpeg_path=ffmpeg_path)
```

Returns title, author, duration, available qualities, supported modes, FFmpeg
availability, and summarized video/audio formats without downloading media. Pass
`ffmpeg_path` to validate a specific executable for the options report.

### select_best_format

```python
from youtube_ai import select_best_format

select_best_format(
    streaming_data: dict,
    quality: VideoQuality | str = VideoQuality.BEST,
    audio_only: bool = False,
    video_only: bool = False,
) -> dict | None
```

Select the best format from streaming data without downloading. When a specific
quality is unavailable, falls back to the closest lower resolution.

---

## Enums

### VideoQuality

```python
from youtube_ai import VideoQuality
```

String enum for video quality selection. Accepts either the enum member or its
string value.

| Member | Value |
|--------|-------|
| `VideoQuality.BEST` | `"best"` |
| `VideoQuality.P144` | `"144p"` |
| `VideoQuality.P240` | `"240p"` |
| `VideoQuality.P360` | `"360p"` |
| `VideoQuality.P480` | `"480p"` |
| `VideoQuality.P720` | `"720p"` |
| `VideoQuality.P1080` | `"1080p"` |
| `VideoQuality.P1440` | `"1440p"` |
| `VideoQuality.P2160` | `"2160p"` |

### DownloadMode

```python
from youtube_ai import DownloadMode
```

String enum for download output mode.

| Member | Value | Description |
|--------|-------|-------------|
| `DownloadMode.FULL` | `"full"` | Video and audio combined (default) |
| `DownloadMode.VIDEO_ONLY` | `"video-only"` | Video track only, no audio |
| `DownloadMode.AUDIO_ONLY` | `"audio-only"` | Audio track only, no video |

---

## Version Fetcher

```python
from youtube_ai import fetch_live_config, get_web_client_version, get_api_key, get_signature_timestamp, refresh
```

Functions for dynamically fetching YouTube's live InnerTube configuration.
Results are cached in-memory for 1 hour.

| Function | Returns | Description |
|----------|---------|-------------|
| `fetch_live_config(force=False)` | `dict` | Fetch live `clientVersion`, `apiKey`, `signatureTimestamp`, `visitorData` from YouTube homepage |
| `get_web_client_version()` | `str` | Current live WEB clientVersion |
| `get_api_key()` | `str` | Current live API key |
| `get_signature_timestamp()` | `int \| None` | Current signature timestamp (STS) |
| `refresh()` | `dict` | Force-refresh live config (use after 400 errors) |

---

## Exceptions

| Exception | Base | Description |
|-----------|------|-------------|
| `InnerTubeError` | `Exception` | Base error for all InnerTube operations |
| `VideoUnavailable` | `InnerTubeError` | Raised when a video is unavailable (deleted, private, etc.) |
| `DownloadError` | `Exception` | Raised when a download fails |

---

## Constants

### CLIENTS

Dict of InnerTube client configurations. Keys: `"WEB"`, `"ANDROID"`, `"IOS"`,
`"MWEB"`, `"TV_EMBEDDED"`, `"WEB_EMBEDDED"`. Each value contains `clientName`,
`clientVersion`, `apiKey`, `userAgent`, and optional `androidSdkVersion`/`deviceModel`.

### ITAG_QUALITY

Dict mapping itag integers to `(quality, format, type)` tuples. Example:
`{18: ("360p", "mp4", "video+audio"), 137: ("1080p", "mp4", "video")}`.
