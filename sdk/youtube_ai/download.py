"""

Video download functionality using streaming data from InnerTube.

Supports quality selection, audio-only, and progress reporting.

"""

from __future__ import annotations



import os

import shutil

import subprocess

import time

from enum import Enum

from pathlib import Path

from typing import Callable



from .client import YouTubeClient

from .constants import STREAM_HEADERS





class DownloadError(Exception):

    """Raised when a media download cannot be completed."""





class VideoQuality(str, Enum):

    BEST = "best"

    P144 = "144p"

    P240 = "240p"

    P360 = "360p"

    P480 = "480p"

    P720 = "720p"

    P1080 = "1080p"

    P1440 = "1440p"

    P2160 = "2160p"





class DownloadMode(str, Enum):

    FULL = "full"

    VIDEO_ONLY = "video-only"

    AUDIO_ONLY = "audio-only"





_QUALITY_HEIGHTS = {

    VideoQuality.P144.value: 144,

    VideoQuality.P240.value: 240,

    VideoQuality.P360.value: 360,

    VideoQuality.P480.value: 480,

    VideoQuality.P720.value: 720,

    VideoQuality.P1080.value: 1080,

    VideoQuality.P1440.value: 1440,

    VideoQuality.P2160.value: 2160,

}





_CHUNK_SIZE = 1024 * 1024

_CHUNK_RETRIES = 3

_DOWNLOAD_TIMEOUT = 30





def _format_total(fmt: dict) -> int | None:

    """Read a format's declared byte length when YouTube provides it."""

    try:

        value = int(fmt.get("content_length") or 0)

    except (TypeError, ValueError):

        return None

    return value or None





def _download_ranged(

    session,

    client: YouTubeClient,

    url: str,

    destination: Path,

    total: int | None,

    progress_callback: Callable[[int, int, int], None] | None,

) -> int:

    """Download a media URL in bounded, resumable byte ranges."""

    client._pin_host(url)

    downloaded = destination.stat().st_size if destination.exists() else 0

    if total is not None and downloaded > total:

        destination.unlink()

        downloaded = 0



    mode = "ab" if downloaded else "wb"

    with destination.open(mode) as output:

        while total is None or downloaded < total:

            end = downloaded + _CHUNK_SIZE - 1

            if total is not None:

                end = min(end, total - 1)

            headers = {

                **STREAM_HEADERS,

                "Accept-Encoding": "identity",

                "Range": f"bytes={downloaded}-{end}",

            }

            last_error: Exception | None = None

            for attempt in range(_CHUNK_RETRIES):

                try:

                    response = session.get(

                        url,

                        headers=headers,

                        impersonate=client.impersonate,

                        timeout=_DOWNLOAD_TIMEOUT,

                    )

                    if response.status_code not in (200, 206):

                        raise DownloadError(f"Download failed: HTTP {response.status_code}")

                    content = response.content

                    if response.status_code == 200 and downloaded:

                        raise DownloadError("Server ignored resume range")

                    if response.status_code == 200:



                        output.write(content)

                        downloaded += len(content)

                        if total is None:

                            total = downloaded

                    else:

                        content_range = response.headers.get("content-range", "")

                        expected_prefix = f"bytes {downloaded}-"

                        if not content_range.startswith(expected_prefix):

                            raise DownloadError(

                                f"Invalid range response: {content_range or 'missing Content-Range'}"

                            )

                        if total is None and "/" in content_range:

                            total_text = content_range.rsplit("/", 1)[1]

                            if total_text.isdigit():

                                total = int(total_text)

                        output.write(content)

                        downloaded += len(content)

                    output.flush()

                    break

                except Exception as exc:

                    last_error = exc

                    if attempt + 1 < _CHUNK_RETRIES:

                        client._pin_host(url)

                        time.sleep(attempt + 1)

            else:

                raise DownloadError(

                    f"Chunk {downloaded}-{end} failed after {_CHUNK_RETRIES} retries: {last_error}"

                ) from last_error



            if progress_callback:

                percent = int(downloaded * 100 / total) if total else 0

                progress_callback(downloaded, total or 0, min(percent, 100))

            if not content:

                raise DownloadError("Download returned an empty response")



    if total is not None and downloaded != total:

        raise DownloadError(f"Incomplete download: got {downloaded} of {total} bytes")

    return downloaded





def _is_executable(path: str | Path) -> bool:

    candidate = Path(path)

    return candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK))





def _find_ffmpeg(ffmpeg_path: str | Path | None = None) -> str | None:

    """Resolve FFmpeg from an argument, config, PATH, or bundled binary."""

    configured = str(ffmpeg_path) if ffmpeg_path is not None else os.environ.get("YTAI_FFMPEG_PATH")

    setting_name = "ffmpeg_path" if ffmpeg_path is not None else "YTAI_FFMPEG_PATH"

    if configured:

        configured_path = Path(configured).expanduser()

        resolved = str(configured_path) if _is_executable(configured_path) else shutil.which(configured)

        if not resolved:

            raise DownloadError(

                f"{setting_name} does not point to an executable FFmpeg binary: {configured}"

            )

        return resolved



    system_ffmpeg = shutil.which("ffmpeg")

    if system_ffmpeg:

        return system_ffmpeg



    try:

        import imageio_ffmpeg



        bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    except (ImportError, OSError, RuntimeError):

        return None

    return bundled_ffmpeg if _is_executable(bundled_ffmpeg) else None





def _clip_args(start_time: float | None, end_time: float | None) -> list[str]:

    args: list[str] = []

    if start_time is not None:

        args.extend(["-ss", str(start_time)])

    if end_time is not None:

        duration = end_time - (start_time or 0)

        args.extend(["-t", str(duration)])

    return args





def _run_ffmpeg(command: list[str]) -> None:

    try:

        result = subprocess.run(command, capture_output=True, text=True, timeout=180)

    except (OSError, subprocess.TimeoutExpired) as exc:

        raise DownloadError(f"ffmpeg failed: {exc}") from exc

    if result.returncode != 0:

        detail = (result.stderr or "").strip()[-500:]

        raise DownloadError(f"ffmpeg failed: {detail}")





def _mux_streams(

    ffmpeg: str,

    video: Path,

    audio: Path,

    output: Path,

    start_time: float | None,

    end_time: float | None,

) -> None:

    """Mux separate YouTube streams, optionally clipping the result."""

    command = [

        ffmpeg, "-y", "-loglevel", "error",

        "-i", str(video), "-i", str(audio),

    ]

    command.extend(_clip_args(start_time, end_time))

    command.extend([

        "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", str(output),

    ])

    _run_ffmpeg(command)





def _clip_stream(

    ffmpeg: str,

    source: Path,

    output: Path,

    start_time: float | None,

    end_time: float | None,

) -> None:

    """Clip a single audio-only or video-only stream."""

    command = [ffmpeg, "-y", "-loglevel", "error", "-i", str(source)]

    command.extend(_clip_args(start_time, end_time))

    command.extend(["-c", "copy", str(output)])

    _run_ffmpeg(command)





def _quality_value(quality: VideoQuality | str) -> str:

    value = quality.value if isinstance(quality, VideoQuality) else quality

    allowed = {item.value for item in VideoQuality}

    if value not in allowed:

        raise ValueError(f"Unsupported quality {value!r}; choose one of {sorted(allowed)}")

    return value





def select_best_format(

    streaming_data: dict,

    quality: VideoQuality | str = VideoQuality.BEST,

    audio_only: bool = False,

    video_only: bool = False,

) -> dict | None:

    """Select a stream matching the requested media type and quality."""

    if audio_only and video_only:

        raise ValueError("audio_only and video_only cannot both be enabled")

    quality_value = _quality_value(quality)

    adaptive = streaming_data.get("adaptive_formats", [])

    progressive = streaming_data.get("formats", [])



    if audio_only:

        audio_formats = [

            fmt for fmt in adaptive

            if fmt.get("has_audio") and not fmt.get("has_video")

        ]

        return max(audio_formats, key=lambda fmt: fmt.get("bitrate", 0), default=None)



    if not video_only and quality_value == VideoQuality.BEST.value and progressive:

        return max(progressive, key=lambda fmt: fmt.get("height") or 0)



    video_formats = [fmt for fmt in adaptive if fmt.get("has_video")]

    if not video_only:

        video_formats.extend(fmt for fmt in progressive if fmt.get("has_video"))

    if not video_formats:

        return None

    if quality_value == VideoQuality.BEST.value:

        return max(

            video_formats,

            key=lambda fmt: ((fmt.get("height") or 0), (fmt.get("fps") or 0), fmt.get("bitrate", 0)),

        )



    target_height = _QUALITY_HEIGHTS[quality_value]

    exact = [fmt for fmt in video_formats if fmt.get("height") == target_height]

    if exact:

        return max(exact, key=lambda fmt: ((fmt.get("fps") or 0), fmt.get("bitrate", 0)))

    lower = [fmt for fmt in video_formats if (fmt.get("height") or 0) <= target_height]

    return max(lower, key=lambda fmt: fmt.get("height") or 0, default=None)





def _format_summary(fmt: dict) -> dict:

    return {

        "itag": fmt.get("itag"),

        "quality": fmt.get("quality"),

        "quality_label": fmt.get("quality_label"),

        "mime_type": fmt.get("mime_type"),

        "bitrate": fmt.get("bitrate"),

        "width": fmt.get("width"),

        "height": fmt.get("height"),

        "fps": fmt.get("fps"),

        "content_length": _format_total(fmt),

        "has_audio": fmt.get("has_audio", False),

        "has_video": fmt.get("has_video", False),

        "is_progressive": fmt.get("is_progressive", False),

    }





def get_download_options(

    video_id: str,

    client: YouTubeClient | None = None,

    use_cache: bool = True,

    ffmpeg_path: str | Path | None = None,

) -> dict:

    """Return video metadata and available download streams without downloading."""

    own_client = client is None

    if own_client:

        client = YouTubeClient()

    try:

        details = client.get_video_info(video_id, use_cache=use_cache)

        streaming = client.get_streaming_data(video_id, use_cache=use_cache)

        formats = streaming.get("formats", []) + streaming.get("adaptive_formats", [])

        video_formats = [fmt for fmt in formats if fmt.get("has_video")]

        audio_formats = [fmt for fmt in formats if fmt.get("has_audio") and not fmt.get("has_video")]

        qualities = sorted(

            {fmt.get("quality_label") for fmt in video_formats if fmt.get("quality_label")},

            key=lambda label: int("".join(char for char in label if char.isdigit()) or 0),

        )

        return {

            "video_id": video_id,

            "title": details.get("title", ""),

            "author": details.get("author", ""),

            "duration_seconds": details.get("length_seconds", 0),

            "view_count": details.get("view_count", 0),

            "available_qualities": qualities,

            "supported_modes": [mode.value for mode in DownloadMode],

            "ffmpeg_available": bool(_find_ffmpeg(ffmpeg_path)),

            "video_formats": [_format_summary(fmt) for fmt in video_formats],

            "audio_formats": [_format_summary(fmt) for fmt in audio_formats],

        }

    finally:

        if own_client:

            client.close()





def download_video(

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

) -> Path:

    """Download full video, video-only, or audio-only media with resume support.



    ``audio_only`` remains supported for compatibility. New callers may use

    ``mode`` or ``video_only``. ``start_time`` and ``end_time`` are optional

    seconds from the beginning of the video and are disabled by default.

    """

    mode_value = mode.value if isinstance(mode, DownloadMode) else mode

    try:

        selected_mode = DownloadMode(mode_value)

    except ValueError as exc:

        raise ValueError(f"Unsupported download mode {mode_value!r}") from exc

    if audio_only and video_only:

        raise ValueError("audio_only and video_only cannot both be enabled")

    if audio_only:

        if selected_mode not in (DownloadMode.FULL, DownloadMode.AUDIO_ONLY):

            raise ValueError("audio_only conflicts with the selected mode")

        selected_mode = DownloadMode.AUDIO_ONLY

    if video_only:

        if selected_mode not in (DownloadMode.FULL, DownloadMode.VIDEO_ONLY):

            raise ValueError("video_only conflicts with the selected mode")

        selected_mode = DownloadMode.VIDEO_ONLY

    if start_time is not None and start_time < 0:

        raise ValueError("start_time must be zero or greater")

    if end_time is not None and end_time <= 0:

        raise ValueError("end_time must be greater than zero")

    if start_time is not None and end_time is not None and end_time <= start_time:

        raise ValueError("end_time must be greater than start_time")



    own_client = client is None

    if own_client:

        client = YouTubeClient()



    try:

        streaming_data = client.get_streaming_data(video_id)

        selected_fmt = select_best_format(

            streaming_data,

            quality=quality,

            audio_only=selected_mode == DownloadMode.AUDIO_ONLY,

            video_only=selected_mode == DownloadMode.VIDEO_ONLY,

        )

        if not selected_fmt or not selected_fmt.get("url"):

            raise DownloadError(f"No suitable format found for {video_id}")



        if output_path is None:

            output = Path.cwd()

        else:

            output = Path(output_path)

        if output.is_dir() or not output.suffix:

            output.mkdir(parents=True, exist_ok=True)

            ext = _ext_for_mime(selected_fmt.get("mime_type", "video/mp4"))

            output = output / f"{video_id}.{ext}"

        output.parent.mkdir(parents=True, exist_ok=True)



        clipping = start_time is not None or end_time is not None

        ffmpeg = _find_ffmpeg(ffmpeg_path) if clipping else None

        audio_fmt = None

        if selected_mode == DownloadMode.FULL and not selected_fmt.get("has_audio"):

            audio_candidates = [

                fmt for fmt in streaming_data.get("adaptive_formats", [])

                if fmt.get("has_audio") and not fmt.get("has_video") and fmt.get("url")

            ]

            audio_fmt = max(audio_candidates, key=lambda fmt: fmt.get("bitrate", 0), default=None)

            if not audio_fmt:

                raise DownloadError("YouTube returned video without a usable audio stream")

            ffmpeg = ffmpeg or _find_ffmpeg(ffmpeg_path)

        if (audio_fmt or clipping) and not ffmpeg:

            raise DownloadError("ffmpeg is required to combine or clip YouTube streams")



        selected_part = (

            output.with_name(output.name + ".video.part")

            if audio_fmt else output.with_name(output.name + ".part")

        )

        audio_part = output.with_name(output.name + ".audio.part") if audio_fmt else None

        completed = False

        try:

            selected_total = _format_total(selected_fmt)

            audio_total = _format_total(audio_fmt) if audio_fmt else None

            combined_total = (selected_total or 0) + (audio_total or 0)



            def selected_progress(done: int, _total: int, _percent: int) -> None:

                if progress_callback:

                    total = combined_total or selected_total or 0

                    percent = int(done * 100 / total) if total else 0

                    progress_callback(done, total, min(percent, 100))



            def audio_progress(done: int, _total: int, _percent: int) -> None:

                if progress_callback:

                    combined_done = (selected_total or selected_part.stat().st_size) + done

                    percent = int(combined_done * 100 / combined_total) if combined_total else 0

                    progress_callback(combined_done, combined_total, min(percent, 100))



            _download_ranged(

                client._session,

                client,

                selected_fmt["url"],

                selected_part,

                selected_total,

                selected_progress,

            )

            if audio_fmt:

                _download_ranged(

                    client._session,

                    client,

                    audio_fmt["url"],

                    audio_part,

                    audio_total,

                    audio_progress,

                )

                _mux_streams(ffmpeg, selected_part, audio_part, output, start_time, end_time)

            elif clipping:

                _clip_stream(ffmpeg, selected_part, output, start_time, end_time)

            else:

                os.replace(selected_part, output)

            if progress_callback:

                final_total = combined_total or selected_total or output.stat().st_size

                progress_callback(final_total, final_total, 100)

            completed = True

            return output

        finally:

            if completed:

                for part in (selected_part, audio_part):

                    if part and part.exists():

                        part.unlink()

    finally:

        if own_client:

            client.close()





def _ext_for_mime(mime: str) -> str:

    """Get file extension for a MIME type."""

    if "webm" in mime:

        return "webm"

    if "mp4" in mime or "m4a" in mime:

        return "mp4" if "video" in mime else "m4a"

    if "flv" in mime:

        return "flv"

    if "3gp" in mime:

        return "3gp"

    return "mp4"
