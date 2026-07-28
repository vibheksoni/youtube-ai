# YTAI CLI Reference

The `ytai` command-line tool provides access to YTAI functionality
from the terminal. It uses Click for command parsing and Rich for formatted
output (tables, panels, progress bars).

## Installation

After `pip install -e .`, the `ytai` command is available:

```bash
ytai --help
```

You can also run it directly:

```bash
python cli/main.py --help
```

## Commands

### search

Search YouTube for videos, channels, and playlists.

```bash
ytai search QUERY [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | `int` | `20` | Maximum number of results |
| `--filter` | `str` | `None` | Filter by type: `video`, `channel`, `playlist`, `movie` |

**Examples:**

```bash
ytai search "python tutorial" --limit 10
ytai search "cooking" --filter video --limit 5
```

### video

Get full video data: metadata (title, views, likes), streaming formats, captions,
related videos, and description.

```bash
ytai video VIDEO_ID
```

**Examples:**

```bash
ytai video dQw4w9WgXcQ
```

### transcript

Get the transcript/captions for a video with timestamps.

```bash
ytai transcript VIDEO_ID [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--lang` | `str` (repeatable) | `en` | Preferred language code (can be specified multiple times) |

**Examples:**

```bash
ytai transcript dQw4w9WgXcQ
ytai transcript dQw4w9WgXcQ --lang en --lang es
```

### download

Download full video, video-only, or audio-only media with optional clipping.

```bash
ytai download VIDEO_ID [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--quality` | `str` | `best` | Quality: `best`, `2160p`, `1440p`, `1080p`, `720p`, `480p`, `360p`, `240p`, `144p` |
| `--output` / `-o` | `str` | `./downloads` | Output directory or file path |
| `--audio-only` | `flag` | `False` | Download audio without video |
| `--video-only` | `flag` | `False` | Download video without audio |
| `--start` | `float` | `None` | Clip start time in seconds |
| `--end` | `float` | `None` | Clip end time in seconds |
| `--ffmpeg-path` | `str` | `None` | Use a specific FFmpeg executable instead of PATH or the bundled binary |

`--audio-only` and `--video-only` are mutually exclusive. If neither is given,
the default is full mode (video + audio). When `--start` and/or `--end` are
supplied, the bundled FFmpeg executable trims the output to the specified range.
Use `--ffmpeg-path` to override it for one command.

**Examples:**

```bash
# Full video with audio at 720p
ytai download dQw4w9WgXcQ --quality 720p --output ./downloads

# Video-only at 144p
ytai download dQw4w9WgXcQ --quality 144p --video-only

# Audio-only
ytai download dQw4w9WgXcQ --audio-only --output ./music

# Clipped segment from 30s to 90s
ytai download dQw4w9WgXcQ --quality 360p --start 30 --end 90
```

### download-options

Inspect video metadata, available qualities, codecs, file sizes, and supported
download modes before downloading.

```bash
ytai download-options VIDEO_ID
```

**Examples:**

```bash
ytai download-options dQw4w9WgXcQ
```

### channel

Get channel metadata (title, avatar, subscriber count, video count).

```bash
ytai channel CHANNEL_ID
```

**Examples:**

```bash
ytai channel UCuAXFkgsw1L7xaCfnd5JJOw
```

### channel-videos

List a channel's uploaded videos.

```bash
ytai channel-videos CHANNEL_ID [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | `int` | `30` | Maximum number of videos to return |

**Examples:**

```bash
ytai channel-videos UCuAXFkgsw1L7xaCfnd5JJOw --limit 10
```

### trending

Show currently trending videos.

```bash
ytai trending [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | `int` | `20` | Maximum number of videos to return |

**Examples:**

```bash
ytai trending --limit 10
```

### formats

List all available streaming formats (progressive and adaptive) for a video,
including itag, quality, codec, bitrate, and file size.

```bash
ytai formats VIDEO_ID
```

**Examples:**

```bash
ytai formats dQw4w9WgXcQ
```

### comments

Show comments for a video with author, text, likes, reply count, and publish time.

```bash
ytai comments VIDEO_ID [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | `int` | `20` | Maximum number of comments to show |

**Examples:**

```bash
ytai comments dQw4w9WgXcQ --limit 5
```

## Global options

| Option | Description |
|--------|-------------|
| `--help` | Show help for any command |
| `--version` | Show the CLI version |
