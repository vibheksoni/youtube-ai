"""

YTAI CLI - command-line interface for the youtube_ai SDK.



Usage:

    python cli/main.py --help

    python cli/main.py search "python tutorial" --limit 10

    python cli/main.py video dQw4w9WgXcQ

    python cli/main.py transcript dQw4w9WgXcQ --lang en

    python cli/main.py download dQw4w9WgXcQ --quality 720p --output ./downloads

    python cli/main.py channel UCxxxxxxxxxxxx

    python cli/main.py channel-videos UCxxxxxxxxxxxx

    python cli/main.py trending

    python cli/main.py formats dQw4w9WgXcQ

"""

from __future__ import annotations



import os

import sys





if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.stderr.reconfigure(encoding="utf-8", errors="replace")





_SDK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sdk")

if _SDK_DIR not in sys.path:

    sys.path.insert(0, _SDK_DIR)



import click

from rich.console import Console

from rich.table import Table

from rich.panel import Panel

from rich.progress import (

    Progress,

    BarColumn,

    DownloadColumn,

    TransferSpeedColumn,

    TimeRemainingColumn,

    TextColumn,

)

from rich.syntax import Syntax



from youtube_ai import (

    DownloadMode,

    VideoQuality,

    YouTubeClient,

    __version__,

    download_video,

    get_download_options,

)

from youtube_ai.client import InnerTubeError, VideoUnavailable



console = Console()







def _format_duration(seconds: float | int | None) -> str:

    """Turn seconds into H:MM:SS or M:SS."""

    if seconds is None:

        return "—"

    seconds = int(seconds)

    h, rem = divmod(seconds, 3600)

    m, s = divmod(rem, 60)

    if h:

        return f"{h}:{m:02d}:{s:02d}"

    return f"{m}:{s:02d}"





def _format_count(n) -> str:

    """Human-friendly view/subscriber counts."""

    if n is None:

        return "—"

    try:

        n = int(n)

    except (TypeError, ValueError):

        return str(n)

    for unit, divisor in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):

        if n >= divisor:

            return f"{n / divisor:.1f}{unit}"

    return str(n)





def _error(message: str) -> None:

    """Print a styled error message."""

    console.print(Panel(f"[bold red]Error[/bold red]\n{message}", border_style="red"))





def _get_client() -> YouTubeClient:

    """Create a fresh client for each command invocation."""

    return YouTubeClient()









@click.group(name="ytai")

@click.version_option(__version__, prog_name="ytai")

def cli():

    """YTAI - search, inspect, transcribe, and download YouTube videos."""

    pass









@cli.command()

@click.argument("query")

@click.option("--limit", default=20, show_default=True, help="Max results to return.")

@click.option(

    "--filter", "filter_type",

    type=click.Choice(["video", "channel", "playlist", "movie"], case_sensitive=False),

    default=None,

    help="Filter search results by type.",

)

def search(query, limit, filter_type):

    """Search YouTube for videos, channels, and playlists."""

    try:

        client = _get_client()

        result = client.search(query, limit=limit, filter_type=filter_type)

    except InnerTubeError as exc:

        _error(f"Search failed: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    results = result.get("results", [])

    if not results:

        console.print("[yellow]No results found.[/yellow]")

        return



    table = Table(

        title=f"[bold]Search: \"{query}\"[/bold]  ({result.get('count', len(results))} results)",

        show_lines=False,

        header_style="bold cyan",

    )

    table.add_column("#", style="dim", width=4)

    table.add_column("Type", style="magenta", width=8)

    table.add_column("Title", style="white", max_width=50, no_wrap=False)

    table.add_column("Channel", style="green", max_width=25)

    table.add_column("Duration", justify="right", style="yellow", width=10)

    table.add_column("Views", justify="right", style="blue", width=9)



    for i, item in enumerate(results, 1):

        kind = item.get("type", "video")

        title = item.get("title", "—")

        ch = item.get("channel", item.get("author", "—"))

        channel = ch.get("name", "—") if isinstance(ch, dict) else ch

        duration = _format_duration(item.get("duration_seconds"))

        views = _format_count(item.get("views"))

        table.add_row(str(i), kind, title, channel, duration, views)



    console.print(table)



    token = result.get("continuation_token")

    if token:

        console.print(f"\n[dim]More results available (continuation token: {token[:40]}…)[/dim]")









@cli.command()

@click.argument("video_id")

def video(video_id):

    """Show detailed metadata for a video."""

    try:

        client = _get_client()

        data = client.get_video(video_id)

    except VideoUnavailable as exc:

        _error(f"Video unavailable: {exc}")

        return

    except InnerTubeError as exc:

        _error(f"Failed to fetch video: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    info = data.get("details", {})





    title = info.get("title", "—")

    author = info.get("author", "—")

    channel_id = info.get("channel_id", "—")

    length = _format_duration(info.get("length_seconds"))

    views = _format_count(info.get("view_count"))

    likes = info.get("likes", "")

    is_live = info.get("is_live", False)



    header_text = (

        f"[bold white]{title}[/bold white]\n\n"

        f"[green]Channel:[/green]  {author}  [dim]({channel_id})[/dim]\n"

        f"[yellow]Length:[/yellow]  {length}\n"

        f"[blue]Views:[/blue]    {views}"

    )

    if likes:

        header_text += f"\n[red]Likes:[/red]    {likes}"

    if is_live:

        header_text += "  [bold red]● LIVE[/bold red]"



    console.print(Panel(header_text, title=f"[bold cyan]Video {video_id}[/bold cyan]", border_style="cyan"))





    thumbnails = info.get("thumbnails", [])

    if thumbnails:

        thumb_table = Table.grid(padding=(0, 1))

        thumb_table.add_column(style="bold")

        thumb_table.add_column()

        for t in thumbnails[:4]:

            thumb_table.add_row(t.get("label", "?"), t.get("url", "—"))

        console.print(Panel(thumb_table, title="[bold]Thumbnails[/bold]", border_style="dim"))





    desc = info.get("description", "")

    if desc:

        max_lines = 30

        desc_lines = desc.split("\n")

        if len(desc_lines) > max_lines:

            desc_display = "\n".join(desc_lines[:max_lines]) + f"\n… ({len(desc_lines) - max_lines} more lines)"

        else:

            desc_display = desc

        console.print(Panel(desc_display, title="[bold]Description[/bold]", border_style="green"))





    keywords = info.get("keywords", [])

    if keywords:

        kw = "  ".join(f"[dim]#{k}[/dim]" for k in keywords)

        console.print(Panel(kw, title="[bold]Keywords[/bold]", border_style="magenta"))





    related = data.get("related_videos", [])

    if related:

        console.print()

        rel_table = Table(

            title=f"[bold green]Related Videos ({len(related)})[/bold green]",

            show_lines=False,

            header_style="bold green",

        )

        rel_table.add_column("#", style="dim", width=4)

        rel_table.add_column("Title", style="white", width=50)

        rel_table.add_column("Channel", style="cyan", width=20)

        rel_table.add_column("Duration", style="yellow", width=10)

        for i, r in enumerate(related[:10], 1):

            rel_table.add_row(

                str(i),

                r.get("title", "—")[:50],

                r.get("channel", {}).get("name", "—")[:20],

                r.get("duration", "—"),

            )

        console.print(rel_table)









@cli.command()

@click.argument("video_id")

@click.option("--lang", "language_codes", multiple=True, default=("en",), show_default=True,

              help="Preferred language codes (can specify multiple).")

def transcript(video_id, language_codes):

    """Show the transcript / captions for a video with timestamps."""

    try:

        client = _get_client()

        result = client.get_transcript(video_id, language_codes=tuple(language_codes))

    except InnerTubeError as exc:

        _error(f"Transcript failed: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    snippets = result.get("snippets", [])

    lang_name = result.get("language", "—")

    lang_code = result.get("language_code", "—")

    is_generated = result.get("is_generated", False)



    header = (

        f"[bold]{lang_name}[/bold] [dim]({lang_code})[/dim]  "

        f"{'[yellow]auto-generated[/yellow]' if is_generated else '[green]manual[/green]'}  "

        f"[dim]{len(snippets)} segments[/dim]"

    )

    console.print(Panel(header, title=f"[bold cyan]Transcript — {video_id}[/bold cyan]", border_style="cyan"))



    if not snippets:

        console.print("[yellow]No transcript segments found.[/yellow]")

        return



    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))

    table.add_column("Time", style="cyan", width=10)

    table.add_column("Text", style="white")

    for s in snippets:

        timestamp = _format_duration(s.get("start", 0))

        text = s.get("text", "")

        table.add_row(timestamp, text)



    console.print(table)





    tracks = result.get("available_tracks", [])

    if len(tracks) > 1:

        console.print("\n[bold dim]Other available tracks:[/bold dim]")

        for t in tracks:

            marker = " ← selected" if t["language_code"] == lang_code else ""

            kind = "auto" if t.get("is_generated") else "manual"

            console.print(f"  [dim]{t['language_code']}[/dim]  {t['name']}  [{kind}]{marker}")









@cli.command()

@click.argument("video_id")

@click.option(

    "--quality",

    type=click.Choice([quality.value for quality in VideoQuality]),

    default=VideoQuality.BEST.value,

    show_default=True,

    help="Video quality.",

)

@click.option("--output", "-o", default="./downloads", show_default=True,

              help="Output directory or file path.")

@click.option("--audio-only", is_flag=True, default=False, help="Download audio without video.")

@click.option("--video-only", is_flag=True, default=False, help="Download video without audio.")

@click.option("--start", "start_time", type=click.FloatRange(min=0), default=None,

              help="Optional clip start in seconds.")

@click.option("--end", "end_time", type=click.FloatRange(min=0, min_open=True), default=None,

              help="Optional clip end in seconds.")

@click.option("--ffmpeg-path", type=click.Path(exists=True, dir_okay=False), default=None,

              help="Use this FFmpeg executable instead of PATH or the bundled binary.")

def download(video_id, quality, output, audio_only, video_only, start_time, end_time, ffmpeg_path):

    """Download full video, audio-only, or video-only media."""

    if audio_only and video_only:

        raise click.UsageError("--audio-only and --video-only cannot be used together")

    if start_time is not None and end_time is not None and end_time <= start_time:

        raise click.UsageError("--end must be greater than --start")

    output_path = os.path.abspath(output)

    mode = (

        DownloadMode.AUDIO_ONLY if audio_only

        else DownloadMode.VIDEO_ONLY if video_only

        else DownloadMode.FULL

    )



    clip_label = ""

    if start_time is not None or end_time is not None:

        clip_label = f" [dim]({start_time or 0:g}s to {end_time if end_time is not None else 'end'})[/dim]"

    console.print(

        f"[bold cyan]Downloading[/bold cyan] [white]{video_id}[/white] "

        f"at [yellow]{quality}[/yellow] [magenta]({mode.value})[/magenta]{clip_label}"

    )



    progress = Progress(

        TextColumn("[bold blue]{task.description}"),

        BarColumn(bar_width=None),

        DownloadColumn(),

        TransferSpeedColumn(),

        TimeRemainingColumn(),

        console=console,

    )



    task_id_holder = {}



    def progress_callback(downloaded: int, total: int, pct: int):

        if "id" not in task_id_holder:

            task_id_holder["id"] = progress.add_task(

                "Downloading", total=total if total else None,

            )

        task_id = task_id_holder["id"]

        if total:

            progress.update(task_id, completed=downloaded, total=total)

        else:

            progress.update(task_id, completed=downloaded)



    try:

        with progress:

            saved_path = download_video(

                video_id,

                output_path=output_path,

                quality=VideoQuality(quality),

                mode=mode,

                start_time=start_time,

                end_time=end_time,

                progress_callback=progress_callback,

                ffmpeg_path=ffmpeg_path,

            )

        console.print(f"\n[bold green]Saved to[/bold green] [white]{saved_path}[/white]")

    except Exception as exc:

        _error(f"Download failed: {exc}")





@cli.command(name="download-options")

@click.argument("video_id")

@click.option("--ffmpeg-path", type=click.Path(exists=True, dir_okay=False), default=None,

              help="Use this FFmpeg executable instead of PATH or the bundled binary.")

def download_options(video_id, ffmpeg_path):

    """Show metadata and available qualities before downloading."""

    try:

        options = get_download_options(video_id, ffmpeg_path=ffmpeg_path)

    except InnerTubeError as exc:

        _error(f"Failed to inspect download options: {exc}")

        return



    summary = (

        f"[bold white]{options['title']}[/bold white]\n"

        f"[green]Author:[/green] {options['author']}\n"

        f"[yellow]Duration:[/yellow] {_format_duration(options['duration_seconds'])}\n"

        f"[blue]Views:[/blue] {_format_count(options['view_count'])}\n"

        f"[magenta]Modes:[/magenta] {', '.join(options['supported_modes'])}\n"

        f"[cyan]ffmpeg:[/cyan] {'available' if options['ffmpeg_available'] else 'missing'}"

    )

    console.print(Panel(summary, title=f"[bold cyan]Download options - {video_id}[/bold cyan]"))



    table = Table(header_style="bold cyan")

    table.add_column("Itag", justify="right")

    table.add_column("Quality")

    table.add_column("Resolution")

    table.add_column("FPS", justify="right")

    table.add_column("Type")

    table.add_column("Size", justify="right")

    for fmt in options["video_formats"]:

        size = f"{fmt['content_length'] / 1_000_000:.1f} MB" if fmt.get("content_length") else "-"

        resolution = f"{fmt.get('width') or '?'}x{fmt.get('height') or '?'}"

        media_type = "video+audio" if fmt.get("has_audio") else "video"

        table.add_row(

            str(fmt.get("itag") or ""), fmt.get("quality_label") or fmt.get("quality") or "-",

            resolution, str(fmt.get("fps") or "-"), media_type, size,

        )

    console.print(table)



    audio_table = Table(title="Audio streams", header_style="bold magenta")

    audio_table.add_column("Itag", justify="right")

    audio_table.add_column("Codec")

    audio_table.add_column("Bitrate", justify="right")

    audio_table.add_column("Size", justify="right")

    for fmt in options["audio_formats"]:

        size = f"{fmt['content_length'] / 1_000_000:.1f} MB" if fmt.get("content_length") else "-"

        audio_table.add_row(

            str(fmt.get("itag") or ""), fmt.get("mime_type") or "-",

            f"{(fmt.get('bitrate') or 0) // 1000} kbps", size,

        )

    console.print(audio_table)









@cli.command()

@click.argument("channel_id")

def channel(channel_id):

    """Show channel information."""

    try:

        client = _get_client()

        info = client.get_channel_info(channel_id)

    except InnerTubeError as exc:

        _error(f"Failed to fetch channel: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    title = info.get("title", "—")

    subs = _format_count(info.get("subscribers"))

    vid_count = _format_count(info.get("video_count"))

    avatar = info.get("avatar", "—")

    banner = info.get("banner", "—")



    body = (

        f"[bold white]{title}[/bold white]\n\n"

        f"[blue]Subscribers:[/blue]  {subs}\n"

        f"[green]Videos:[/green]       {vid_count}\n"

        f"[magenta]Avatar:[/magenta]      {avatar}\n"

        f"[dim]Banner:[/dim]       {banner}"

    )

    console.print(Panel(body, title=f"[bold cyan]Channel {channel_id}[/bold cyan]", border_style="cyan"))









@cli.command(name="channel-videos")

@click.argument("channel_id")

@click.option("--limit", default=30, show_default=True, help="Max videos to return.")

def channel_videos(channel_id, limit):

    """List a channel's uploaded videos."""

    try:

        client = _get_client()

        videos = client.get_channel_videos(channel_id, limit=limit)

    except InnerTubeError as exc:

        _error(f"Failed to fetch channel videos: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    if not videos:

        console.print("[yellow]No videos found for this channel.[/yellow]")

        return



    table = Table(

        title=f"[bold]Channel videos — {channel_id}[/bold]  ({len(videos)} videos)",

        show_lines=False,

        header_style="bold cyan",

    )

    table.add_column("#", style="dim", width=4)

    table.add_column("Title", style="white", max_width=55, no_wrap=False)

    table.add_column("Duration", justify="right", style="yellow", width=10)

    table.add_column("Views", justify="right", style="blue", width=9)



    for i, v in enumerate(videos, 1):

        title = v.get("title", "—")

        duration = _format_duration(v.get("duration_seconds"))

        views = _format_count(v.get("views"))

        table.add_row(str(i), title, duration, views)



    console.print(table)









@cli.command()

@click.option("--limit", default=20, show_default=True, help="Max videos to return.")

def trending(limit):

    """Show currently trending videos."""

    try:

        client = _get_client()

        videos = client.get_trending(limit=limit)

    except InnerTubeError as exc:

        _error(f"Failed to fetch trending: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    if not videos:

        console.print("[yellow]No trending videos found.[/yellow]")

        return



    table = Table(

        title="[bold]🔥 Trending[/bold]",

        show_lines=False,

        header_style="bold cyan",

    )

    table.add_column("#", style="dim", width=4)

    table.add_column("Title", style="white", max_width=50, no_wrap=False)

    table.add_column("Channel", style="green", max_width=25)

    table.add_column("Duration", justify="right", style="yellow", width=10)

    table.add_column("Views", justify="right", style="blue", width=9)



    for i, v in enumerate(videos, 1):

        title = v.get("title", "—")

        ch = v.get("channel", v.get("author", "—"))

        channel = ch.get("name", "—") if isinstance(ch, dict) else ch

        duration = _format_duration(v.get("duration_seconds"))

        views = _format_count(v.get("views"))

        table.add_row(str(i), title, channel, duration, views)



    console.print(table)









@cli.command()

@click.argument("video_id")

def formats(video_id):

    """Show available streaming formats and qualities."""

    try:

        client = _get_client()

        data = client.get_streaming_data(video_id)

    except InnerTubeError as exc:

        _error(f"Failed to fetch formats: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    progressive = data.get("formats", [])

    adaptive = data.get("adaptive_formats", [])

    hls = data.get("hls_manifest_url")

    dash = data.get("dash_manifest_url")





    if progressive:

        table = Table(

            title="[bold green]Progressive Formats[/bold green] (audio + video combined)",

            show_lines=False,

            header_style="bold green",

        )

        table.add_column("Itag", style="dim", width=6)

        table.add_column("Quality", style="yellow", width=10)

        table.add_column("Type", style="magenta", width=18)

        table.add_column("Size", justify="right", style="blue", width=12)

        table.add_column("Has Audio", justify="center", width=10)



        for f in progressive:

            itag = f.get("itag", "—")

            quality = f.get("quality_label") or f.get("quality", "—")

            mime = f.get("mime_type", "—")

            size_mb = ""

            if f.get("content_length"):

                size_mb = f"{int(f['content_length']) / 1_000_000:.1f} MB"

            has_audio = "✓" if f.get("has_audio") else "✗"

            table.add_row(str(itag), quality, mime, size_mb, has_audio)



        console.print(table)

    else:

        console.print("[dim]No progressive formats available.[/dim]")





    if adaptive:

        console.print()

        table = Table(

            title="[bold magenta]Adaptive Formats[/bold magenta] (separate audio / video)",

            show_lines=False,

            header_style="bold magenta",

        )

        table.add_column("Itag", style="dim", width=6)

        table.add_column("Type", style="cyan", width=10)

        table.add_column("Quality", style="yellow", width=12)

        table.add_column("Codec", style="magenta", width=20)

        table.add_column("Bitrate", justify="right", style="blue", width=12)

        table.add_column("Size", justify="right", style="green", width=12)



        for f in adaptive:

            itag = f.get("itag", "—")

            ftype = "video" if f.get("has_video") else "audio"

            quality = f.get("quality_label") or f.get("quality", "—")

            mime = f.get("mime_type", "—")

            bitrate = f"{f.get('bitrate', 0) // 1000} kbps" if f.get("bitrate") else "—"

            size_mb = ""

            if f.get("content_length"):

                size_mb = f"{int(f['content_length']) / 1_000_000:.1f} MB"

            table.add_row(str(itag), ftype, quality, mime, bitrate, size_mb)



        console.print(table)

    else:

        console.print("[dim]No adaptive formats available.[/dim]")





    if hls or dash:

        console.print()

        if hls:

            console.print(f"[bold]HLS Manifest:[/bold] [dim]{hls}[/dim]")

        if dash:

            console.print(f"[bold]DASH Manifest:[/bold] [dim]{dash}[/dim]")





@cli.command()

@click.argument("video_id")

@click.option("--limit", default=20, help="Max comments to show (default 20)")

def comments(video_id, limit):

    """Show comments for a video."""

    try:

        client = _get_client()

        result = client.get_comments(video_id, limit=limit)

    except InnerTubeError as exc:

        _error(f"Failed to fetch comments: {exc}")

        return

    finally:

        try:

            client.close()

        except NameError:

            pass



    comments_list = result.get("comments", [])

    if not comments_list:

        console.print("[dim]No comments found.[/dim]")

        return



    console.print(f"\n[bold green]Comments ({len(comments_list)})[/bold green]\n")

    for i, c in enumerate(comments_list, 1):

        author = c.get("author", "?")

        text = c.get("text", "")

        likes = c.get("likes", "")

        replies = c.get("reply_count", "")

        published = c.get("published_time", "")

        verified = " ✓" if c.get("is_verified") else ""



        console.print(f"  [bold cyan]{i}. @{author}{verified}[/bold cyan] [dim]({published})[/dim]")

        console.print(f"  {text}")

        meta_parts = []

        if likes:

            meta_parts.append(f"👍 {likes}")

        if replies:

            meta_parts.append(f"💬 {replies} replies")

        if meta_parts:

            meta_str = "  ".join(meta_parts)

            console.print(f"  [dim]{meta_str}[/dim]")

        console.print()



    if result.get("continuation_token"):

        console.print("[dim]More comments available (use --continuation-token)[/dim]")









if __name__ == "__main__":

    cli()
