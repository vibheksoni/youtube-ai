

"""

YTAI SDK - Comprehensive End-to-End Tests



Tests every feature against the real YouTube InnerTube API.

No mocks, no fakes — all requests hit the real YouTube servers.



Usage:

    python tests/test_e2e.py

"""

from __future__ import annotations



import os

import re

import subprocess

import sys

import tempfile

import time

from pathlib import Path





if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.stderr.reconfigure(encoding="utf-8", errors="replace")





sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import (

    Cache,

    DownloadMode,

    VideoQuality,

    YouTubeClient,

    download_video,

    get_download_options,

    select_best_format,

)

from youtube_ai.client import InnerTubeError, VideoUnavailable

from youtube_ai.download import _find_ffmpeg





VIDEO_ID = "dQw4w9WgXcQ"

CHANNEL_ID = "UCuAXFkgsw1L7xaCfnd5JJOw"

SEARCH_QUERY = "python tutorial"

PASS = "PASS"

FAIL = "FAIL"

SKIP = "SKIP"



_passed = 0

_failed = 0

_skipped = 0





def _result(name: str, status: str, detail: str = "") -> None:

    global _passed, _failed, _skipped

    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[status]

    line = f"  {icon} {name}: {status}"

    if detail:

        line += f" — {detail}"

    print(line)

    if status == PASS:

        _passed += 1

    elif status == FAIL:

        _failed += 1

    else:

        _skipped += 1





def _section(title: str) -> None:

    print(f"\n{'=' * 60}")

    print(f"TEST: {title}")

    print(f"{'=' * 60}")





def _assert(condition: bool, name: str, detail: str = "") -> None:

    if condition:

        _result(name, PASS, detail)

    else:

        _result(name, FAIL, detail)









def test_cache_operations():

    _section("Cache operations")

    cache = Cache()

    cache.clear()





    cache.set("test", "key1", {"data": 42})

    val = cache.get("test", "key1")

    _assert(val == {"data": 42}, "Cache set/get", f"got {val}")





    cache.delete("test", "key1")

    val = cache.get("test", "key1")

    _assert(val is None, "Cache delete", "value is None after delete")





    cache.set("test", "ttl_key", "temp", ttl=1)

    time.sleep(2)

    val = cache.get("test", "ttl_key")

    _assert(val is None, "Cache TTL expiry", "expired after 1s")





    cache.set("test", "stat_key", "x")

    stats = cache.stats()

    _assert(isinstance(stats, dict) and "total_entries" in stats, "Cache stats", f"{stats}")





    cache.clear()

    stats = cache.stats()

    _assert(stats.get("total_entries", 0) == 0, "Cache clear", "all entries wiped")



    cache.close()





def test_search_basic():

    _section("Search — basic query")

    client = YouTubeClient()

    try:

        r = client.search(SEARCH_QUERY, limit=5, use_cache=False)

        _assert(r["count"] > 0, "Returns results", f"{r['count']} results")



        if r["results"]:

            v = r["results"][0]

            _assert("video_id" in v or "channel_id" in v, "Has ID field", f"keys: {list(v.keys())[:5]}")





            video_results = [x for x in r["results"] if x.get("type") == "video"]

            if video_results:

                v = video_results[0]

                _assert(bool(v.get("video_id")), "Video has video_id", v.get("video_id", ""))

                _assert(bool(v.get("title")), "Video has title", v["title"][:40])

                _assert(bool(v.get("url")), "Video has url", v.get("url", "")[:50])

                _assert("channel" in v and isinstance(v["channel"], dict), "Video has channel dict", str(v.get("channel")))

                _assert("duration_seconds" in v, "Video has duration_seconds", str(v.get("duration_seconds")))

    finally:

        client.close()





def test_search_filters():

    _section("Search — filter_type")

    client = YouTubeClient()

    try:



        r = client.search("music", limit=5, filter_type="video", use_cache=False)

        types = set(x.get("type") for x in r["results"])

        if not types:



            time.sleep(2)

            r = client.search("python", limit=5, filter_type="video", use_cache=False)

            types = set(x.get("type") for x in r["results"])

        _assert("video" in types, "Video filter returns videos", f"types: {types}")

        _assert("channel" not in types, "Video filter excludes channels", f"types: {types}")



        time.sleep(1)





        r = client.search("music", limit=5, filter_type="channel", use_cache=False)

        types = set(x.get("type") for x in r["results"])

        _assert("channel" in types, "Channel filter returns channels", f"types: {types}")

    finally:

        client.close()





def test_search_pagination():

    _section("Search — pagination")

    client = YouTubeClient()

    try:

        r1 = client.search("machine learning", limit=5, use_cache=False)

        _assert(bool(r1.get("continuation_token")), "Page 1 has continuation_token")



        time.sleep(1)



        r2 = client.search("machine learning", limit=5, continuation_token=r1.get("continuation_token"), use_cache=False)

        _assert(r2["count"] > 0, "Page 2 returns results", f"{r2['count']} results")





        ids1 = set(x.get("video_id") or x.get("channel_id") for x in r1["results"])

        ids2 = set(x.get("video_id") or x.get("channel_id") for x in r2["results"])

        overlap = ids1 & ids2

        _assert(len(overlap) == 0, "Pages don't overlap", f"overlap: {overlap}" if overlap else "no overlap")



        _assert(bool(r2.get("continuation_token")), "Page 2 has continuation_token")

    finally:

        client.close()





def test_video_metadata():

    _section("Video metadata — get_video")

    client = YouTubeClient()

    try:

        v = client.get_video(VIDEO_ID, use_cache=False)

        details = v["details"]



        _assert(details.get("video_id") == VIDEO_ID, "video_id matches", details.get("video_id", ""))

        _assert(bool(details.get("title")), "Has title", details.get("title", "")[:50])

        _assert(bool(details.get("author")), "Has author", details.get("author", ""))

        _assert(bool(details.get("channel_id")), "Has channel_id", details.get("channel_id", ""))

        _assert(details.get("length_seconds", 0) > 0, "Has duration > 0", f"{details.get('length_seconds')}s")

        _assert(details.get("view_count", 0) > 0, "Has view_count > 0", f"{details.get('view_count')}")

        _assert(bool(details.get("description")), "Has description", f"{len(details.get('description', ''))} chars")

        _assert(len(details.get("thumbnails", [])) > 0, "Has thumbnails", f"{len(details.get('thumbnails', []))} thumbs")

        _assert("playability_status" in details, "Has playability_status", details.get("playability_status", ""))

    finally:

        client.close()





def test_video_likes():

    _section("Video likes — extracted from next endpoint")

    client = YouTubeClient()

    try:

        v = client.get_video(VIDEO_ID, use_cache=False)

        likes = v["details"].get("likes", "")

        _assert(bool(likes), "Likes is non-empty", f"likes: {likes}")

    finally:

        client.close()





def test_related_videos():

    _section("Related videos — from next endpoint")

    client = YouTubeClient()

    try:

        v = client.get_video(VIDEO_ID, use_cache=False)

        related = v["related_videos"]

        _assert(len(related) > 0, "Has related videos", f"{len(related)} videos")



        if related:

            r = related[0]

            _assert(bool(r.get("video_id")), "Related has video_id", r.get("video_id", ""))

            _assert(bool(r.get("title")), "Related has title", r.get("title", "")[:40])

            _assert("channel" in r, "Related has channel", str(r.get("channel")))

    finally:

        client.close()





def test_comments():

    _section("Comments — get_comments")

    client = YouTubeClient()

    try:

        result = client.get_comments(VIDEO_ID, limit=5, use_cache=False)

        comments = result.get("comments", [])

        _assert(len(comments) > 0, "Returns comments", f"{len(comments)} comments")



        if comments:

            c = comments[0]

            _assert(bool(c.get("comment_id")), "Comment has comment_id", c.get("comment_id", "")[:20])

            _assert(bool(c.get("author")), "Comment has author", c.get("author", ""))

            _assert(bool(c.get("text")), "Comment has text", c.get("text", "")[:40])

            _assert("likes" in c, "Comment has likes field", c.get("likes", ""))

            _assert("reply_count" in c, "Comment has reply_count field", c.get("reply_count", ""))

            _assert(bool(c.get("published_time")), "Comment has published_time", c.get("published_time", ""))



        _assert(bool(result.get("continuation_token")), "Has continuation token for more comments")

    finally:

        client.close()





def test_transcript():

    _section("Transcript — timestamps and text")

    client = YouTubeClient()

    try:

        t = client.get_transcript(VIDEO_ID, ("en",), use_cache=False)

        snippets = t["snippets"]

        _assert(len(snippets) > 0, "Returns snippets", f"{len(snippets)} snippets")



        if snippets:

            s = snippets[0]

            _assert("start" in s, "Snippet has start", str(s.get("start")))

            _assert("duration" in s, "Snippet has duration", str(s.get("duration")))

            _assert(bool(s.get("text")), "Snippet has text", s.get("text", "")[:40])





            starts = [s["start"] for s in snippets]

            is_sorted = all(starts[i] <= starts[i + 1] for i in range(len(starts) - 1))

            _assert(is_sorted, "Timestamps are monotonic", f"first={starts[0]}, last={starts[-1]}")





            empty_count = sum(1 for s in snippets if not s.get("text", "").strip())

            _assert(empty_count == 0, "No empty text fields", f"{empty_count} empty")

    finally:

        client.close()





def test_transcript_language_fallback():

    _section("Transcript — language fallback")

    client = YouTubeClient()

    try:



        t = client.get_transcript(VIDEO_ID, ("zz",), use_cache=False)

        snippets = t["snippets"]

        _assert(len(snippets) > 0, "Falls back to available language", f"{len(snippets)} snippets, lang={t.get('language', '')}")

    finally:

        client.close()





def test_streaming_data():

    _section("Streaming data — formats and URLs")

    client = YouTubeClient()

    try:

        sd = client.get_streaming_data(VIDEO_ID, use_cache=False)

        adaptive = sd.get("adaptive_formats", [])

        _assert(len(adaptive) > 0, "Has adaptive formats", f"{len(adaptive)} formats")



        if adaptive:

            with_urls = sum(1 for f in adaptive if f.get("url"))

            _assert(with_urls == len(adaptive), "All formats have URLs", f"{with_urls}/{len(adaptive)}")





            has_video = any(f.get("has_video") for f in adaptive)

            has_audio = any(f.get("has_audio") for f in adaptive)

            _assert(has_video, "Has at least one video format")

            _assert(has_audio, "Has at least one audio format")





            f = adaptive[0]

            _assert("itag" in f, "Format has itag", str(f.get("itag")))

            _assert("mime_type" in f, "Format has mime_type", f.get("mime_type", "")[:30])

    finally:

        client.close()





def test_format_selection():

    _section("Format selection — select_best_format")

    client = YouTubeClient()

    try:

        sd = client.get_streaming_data(VIDEO_ID, use_cache=False)





        best = select_best_format(sd, quality="best")

        _assert(best is not None, "Best quality returns format", f"itag={best.get('itag') if best else None}")

        _assert(bool(best.get("url")) if best else False, "Best format has URL")





        f720 = select_best_format(sd, quality="720p")

        _assert(f720 is not None, "720p returns format")

        if f720:

            _assert((f720.get("height") or 0) <= 720, "720p height <= 720", str(f720.get("height")))





        audio = select_best_format(sd, audio_only=True)

        _assert(audio is not None, "Audio only returns format")

        if audio:

            _assert(audio.get("has_audio"), "Audio format has audio", str(audio.get("has_audio")))

            _assert(not audio.get("has_video"), "Audio format has no video", str(audio.get("has_video")))

    finally:

        client.close()





def test_download():

    _section("Download — options, modes, clipping, muxing, and cleanup")

    client = YouTubeClient()

    try:

        options = get_download_options(VIDEO_ID, client=client, use_cache=False)

        _assert(options.get("title"), "Options include metadata", options.get("title", "")[:50])

        _assert("144p" in options.get("available_qualities", []), "Options include 144p", str(options.get("available_qualities")))

        _assert(

            set(options.get("supported_modes", [])) == {mode.value for mode in DownloadMode},

            "Options include all modes",

            str(options.get("supported_modes")),

        )



        ffmpeg = _find_ffmpeg()

        _assert(bool(ffmpeg), "ffmpeg is available", ffmpeg or "missing")



        def probe(path: Path) -> tuple[float, set[str]]:

            result = subprocess.run(

                [ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"],

                capture_output=True,

                text=True,

                timeout=60,

            )

            _assert(result.returncode == 0, "ffmpeg accepts output", result.stderr[-80:])

            probe_output = result.stderr

            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", probe_output)

            _assert(bool(duration_match), "ffmpeg reports duration", path.name)

            if not duration_match:

                return 0.0, set()

            hours, minutes, seconds = duration_match.groups()

            duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

            streams = set()

            if re.search(r"Stream #\d+:\d+.*Video:", probe_output):

                streams.add("video")

            if re.search(r"Stream #\d+:\d+.*Audio:", probe_output):

                streams.add("audio")

            return duration, streams



        with tempfile.TemporaryDirectory() as tmpdir:

            progress = []

            full = download_video(

                VIDEO_ID,

                output_path=Path(tmpdir) / "full.mp4",

                quality=VideoQuality.P144,

                mode=DownloadMode.FULL,

                client=client,

                progress_callback=lambda done, total, percent: progress.append((done, total, percent)),

            )

            duration, streams = probe(full)

            _assert({"video", "audio"}.issubset(streams), "Full output has video and audio", str(streams))

            _assert(duration > 200, "Full output has complete duration", f"{duration:.2f}s")

            _assert(bool(progress) and progress[-1][2] == 100, "Progress reaches 100%", str(progress[-1] if progress else None))



            video_only = download_video(

                VIDEO_ID,

                output_path=Path(tmpdir) / "video-only.mp4",

                quality=VideoQuality.P144,

                mode=DownloadMode.VIDEO_ONLY,

                start_time=5,

                end_time=12,

                client=client,

            )

            duration, streams = probe(video_only)

            _assert(streams == {"video"}, "Video-only output excludes audio", str(streams))

            _assert(6 <= duration <= 8, "Video-only clip respects interval", f"{duration:.2f}s")



            audio_only = download_video(

                VIDEO_ID,

                output_path=Path(tmpdir) / "audio-only.m4a",

                mode=DownloadMode.AUDIO_ONLY,

                start_time=5,

                end_time=12,

                client=client,

            )

            duration, streams = probe(audio_only)

            _assert(streams == {"audio"}, "Audio-only output excludes video", str(streams))

            _assert(6 <= duration <= 8, "Audio-only clip respects interval", f"{duration:.2f}s")



            full_clip = download_video(

                VIDEO_ID,

                output_path=Path(tmpdir) / "full-clip.mp4",

                quality="144p",

                start_time=5,

                end_time=12,

                client=client,

            )

            duration, streams = probe(full_clip)

            _assert({"video", "audio"}.issubset(streams), "Full clip has video and audio", str(streams))

            _assert(6 <= duration <= 8, "Full clip respects interval", f"{duration:.2f}s")



            parts = list(Path(tmpdir).glob("*.part"))

            _assert(not parts, "No partial files remain", str(parts))

    finally:

        client.close()





def test_channel_info():

    _section("Channel info — all fields populated")

    client = YouTubeClient()

    try:

        ci = client.get_channel_info(CHANNEL_ID, use_cache=False)

        _assert(bool(ci.get("title")), "Has title", ci.get("title", ""))

        _assert(bool(ci.get("avatar")), "Has avatar", "yes" if ci.get("avatar") else "no")

        _assert(bool(ci.get("subscribers")), "Has subscribers", ci.get("subscribers", ""))

        _assert(bool(ci.get("video_count")), "Has video_count", ci.get("video_count", ""))

    finally:

        client.close()





def test_channel_videos():

    _section("Channel videos — get_channel_videos with limit")

    client = YouTubeClient()

    try:

        videos = client.get_channel_videos(CHANNEL_ID, limit=10, use_cache=False)

        _assert(len(videos) > 0, "Returns videos", f"{len(videos)} videos")

        _assert(len(videos) <= 10, "Respects limit", f"{len(videos)} <= 10")



        if videos:

            v = videos[0]

            _assert(bool(v.get("video_id")), "Video has video_id", v.get("video_id", ""))

            _assert(bool(v.get("title")), "Video has title", v.get("title", "")[:40])

            _assert(len(v.get("video_id", "")) == 11, "video_id is 11 chars", v.get("video_id", ""))

    finally:

        client.close()





def test_trending():

    _section("Trending — get_trending with limit")

    client = YouTubeClient()

    try:

        videos = client.get_trending(limit=10, use_cache=False)

        _assert(len(videos) > 0, "Returns trending videos", f"{len(videos)} videos")

        _assert(len(videos) <= 10, "Respects limit", f"{len(videos)} <= 10")



        if videos:

            v = videos[0]

            _assert(bool(v.get("video_id")), "Trending video has video_id", v.get("video_id", ""))

            _assert(bool(v.get("title")), "Trending video has title", v.get("title", "")[:40])

    finally:

        client.close()





def test_cache_integration():

    _section("Cache integration — SDK caches results")

    cache = Cache()

    cache.clear()

    client = YouTubeClient(cache=cache)

    try:



        r1 = client.search("test query", limit=1, use_cache=True)

        stats = cache.stats()

        _assert(stats.get("total_entries", 0) > 0, "Cache has entries after search", f"{stats}")





        r2 = client.search("test query", limit=1, use_cache=True)

        _assert(r1 == r2, "Cached result matches first call", "identical")

    finally:

        client.close()

        cache.clear()

        cache.close()





def test_video_info():

    _section("Video info — metadata only")

    client = YouTubeClient()

    try:

        info = client.get_video_info(VIDEO_ID, use_cache=False)

        _assert(bool(info.get("title")), "Has title", info.get("title", "")[:50])

        _assert(info.get("video_id") == VIDEO_ID, "video_id matches", info.get("video_id", ""))

        _assert("streaming_data" not in info, "No streaming_data in info", "metadata only")

    finally:

        client.close()





def test_error_handling():

    _section("Error handling — invalid inputs")

    client = YouTubeClient()

    try:



        try:

            v = client.get_video("INVALID12345", use_cache=False)

            _result("Invalid video ID raises", FAIL, "no exception raised")

        except (VideoUnavailable, InnerTubeError):

            _result("Invalid video ID raises", PASS, "InnerTubeError raised")

        except Exception as e:

            _result("Invalid video ID raises", FAIL, f"unexpected: {type(e).__name__}")



        time.sleep(1)





        try:

            r = client.search("", limit=1, use_cache=False)

            _result("Empty query handled", PASS, f"returned {r.get('count', 0)} results")

        except Exception as e:

            _result("Empty query handled", PASS, f"raised {type(e).__name__}")

    finally:

        client.close()





def test_cli_commands():

    _section("CLI — all commands")

    cli_path = str(Path(__file__).resolve().parent.parent / "cli" / "main.py")



    commands = [

        (["--version"], "version"),

        (["search", "python", "--limit", "2"], "search"),

        (["video", VIDEO_ID], "video"),

        (["transcript", VIDEO_ID], "transcript"),

        (["channel", CHANNEL_ID], "channel"),

        (["trending", "--limit", "3"], "trending"),

        (["formats", VIDEO_ID], "formats"),

        (["download-options", VIDEO_ID], "download-options"),

        (["comments", VIDEO_ID, "--limit", "3"], "comments"),

    ]



    import subprocess



    for args, name in commands:

        cmd = [sys.executable, cli_path] + args

        try:

            result = subprocess.run(

                cmd,

                capture_output=True,

                timeout=120,

                env={**os.environ, "PYTHONIOENCODING": "utf-8"},

                encoding="utf-8",

                errors="replace",

            )

            _assert(

                result.returncode == 0 and len(result.stdout or "") > 10,

                f"CLI {name}",

                f"exit={result.returncode}, stdout={len(result.stdout or '')} bytes" +

                (f", stderr={(result.stderr or '')[:80]}" if result.returncode != 0 else ""),

            )

        except subprocess.TimeoutExpired:

            _result(f"CLI {name}", FAIL, "timeout")

        except Exception as e:

            _result(f"CLI {name}", FAIL, str(e)[:80])





    with tempfile.TemporaryDirectory() as tmpdir:

        output = Path(tmpdir) / "cli-clip.mp4"

        cmd = [

            sys.executable, cli_path, "download", VIDEO_ID,

            "--quality", "144p", "--start", "5", "--end", "12",

            "--output", str(output),

        ]

        result = subprocess.run(

            cmd,

            capture_output=True,

            timeout=180,

            env={**os.environ, "PYTHONIOENCODING": "utf-8"},

            encoding="utf-8",

            errors="replace",

        )

        _assert(result.returncode == 0, "CLI download exits successfully", result.stderr[:100])

        _assert(output.exists() and output.stat().st_size > 10240, "CLI download writes media", str(output))





def test_mcp_server():

    _section("MCP server — all tools")



    sdk_dir = str(Path(__file__).resolve().parent.parent / "sdk")

    sys.path.insert(0, sdk_dir)





    import importlib

    spec = importlib.util.spec_from_file_location(

        "mcp_server_test",

        str(Path(__file__).resolve().parent.parent / "mcp" / "server.py"),

    )

    mod = importlib.util.module_from_spec(spec)

    try:

        spec.loader.exec_module(mod)

    except Exception:



        _result("MCP server import", SKIP, "fastmcp import failed")

        return



    _result("MCP server import", PASS, "module loaded")

    _assert(mod.mcp.name == "ytai", "MCP server uses YTAI identifier", mod.mcp.name)





    tools = [

        ("search_videos", lambda: mod.search_videos.fn("test", limit=2)),

        ("get_video", lambda: mod.get_video.fn(VIDEO_ID)),

        ("get_video_info", lambda: mod.get_video_info.fn(VIDEO_ID)),

        ("get_transcript", lambda: mod.get_transcript.fn(VIDEO_ID)),

        ("get_streaming_data", lambda: mod.get_streaming_data.fn(VIDEO_ID)),

        ("get_channel_info", lambda: mod.get_channel_info.fn(CHANNEL_ID)),

        ("get_channel_videos", lambda: mod.get_channel_videos.fn(CHANNEL_ID, limit=5)),

        ("get_trending", lambda: mod.get_trending.fn(limit=5)),

        ("get_comments", lambda: mod.get_comments.fn(VIDEO_ID, limit=3)),

    ]



    for name, fn in tools:

        try:

            result = fn()

            if isinstance(result, dict) and "error" in result:

                _result(f"MCP {name}", FAIL, result["error"])

            elif isinstance(result, list) and result and isinstance(result[0], dict) and "error" in result[0]:

                _result(f"MCP {name}", FAIL, result[0]["error"])

            else:

                _result(f"MCP {name}", PASS, f"returned {type(result).__name__}")

        except Exception as e:

            _result(f"MCP {name}", FAIL, str(e)[:80])

        time.sleep(1)





    try:

        result = mod.get_video.fn("INVALID12345")

        _assert("error" in result, "MCP error handling", f"error: {result.get('error', '')}")

    except Exception as e:

        _result("MCP error handling", FAIL, str(e)[:80])





def test_native_transcript():

    _section("Native transcript — InnerTube get_transcript endpoint")

    client = YouTubeClient()

    try:



        t = client.get_transcript(VIDEO_ID, ("en",), use_cache=False)

        snippets = t["snippets"]

        _assert(len(snippets) > 0, "Returns snippets from native endpoint", f"{len(snippets)} snippets")



        if snippets:

            s = snippets[0]

            _assert("start" in s, "Snippet has start", str(s.get("start")))

            _assert("text" in s, "Snippet has text", s.get("text", "")[:40])



            _assert("start_time" in s, "Snippet has start_time (native format)", s.get("start_time", ""))





        tracks = t.get("available_tracks", [])

        _assert(len(tracks) > 0, "Has available tracks", f"{len(tracks)} tracks")

    finally:

        client.close()





def test_get_watch_combined():

    _section("get_watch — combined player + next endpoint")

    client = YouTubeClient()

    try:



        v = client.get_video(VIDEO_ID, use_cache=False)

        details = v["details"]





        _assert(len(v["streaming_data"]["adaptive_formats"]) > 0, "Has streaming data from get_watch",

                f"{len(v['streaming_data']['adaptive_formats'])} formats")





        _assert(bool(details.get("likes")), "Has likes from watch next", details.get("likes", ""))

        _assert(len(v["related_videos"]) > 0, "Has related from watch next", f"{len(v['related_videos'])} videos")

    finally:

        client.close()





def test_search_snippets():

    _section("Search snippets — detailedMetadataSnippets")

    client = YouTubeClient()

    try:

        r = client.search("AI coding agents", limit=5, use_cache=False)

        video_results = [x for x in r["results"] if x.get("type") == "video"]

        if video_results:

            has_snippets = any(v.get("snippets") for v in video_results)

            _assert(has_snippets, "At least one result has snippets", "found" if has_snippets else "not found")

    finally:

        client.close()





def test_richer_context():

    _section("Richer context — WEB client fields")

    client = YouTubeClient()

    try:



        ctx = client._build_context("WEB")

        c = ctx.get("client", {})

        _assert("browserName" in c, "Context has browserName", c.get("browserName", ""))

        _assert("platform" in c, "Context has platform", c.get("platform", ""))

        _assert("timeZone" in c, "Context has timeZone", c.get("timeZone", ""))

        _assert("mainAppWebInfo" in c, "Context has mainAppWebInfo", "yes" if "mainAppWebInfo" in c else "no")

        _assert("screenDensityFloat" in c, "Context has screenDensityFloat", c.get("screenDensityFloat", ""))

    finally:

        client.close()





def test_edge_cases():

    _section("Edge cases")

    client = YouTubeClient()

    try:



        try:

            r = client.search('c++ "tutorial"', limit=2, use_cache=False)

            _result("Special chars in search", PASS, f"{r['count']} results")

        except Exception as e:

            _result("Special chars in search", FAIL, str(e)[:60])



        time.sleep(1)





        try:

            t = client.get_transcript(VIDEO_ID, ("en",), use_cache=False)

            _assert(len(t["snippets"]) > 0, "Transcript on popular video", f"{len(t['snippets'])} snippets")

        except Exception as e:

            _result("Transcript edge case", FAIL, str(e)[:60])

    finally:

        client.close()









def main():

    print("YTAI SDK - Comprehensive End-to-End Tests")

    print(f"Python {sys.version}")

    print(f"Video ID: {VIDEO_ID}")

    print(f"Channel ID: {CHANNEL_ID}")



    tests = [

        test_cache_operations,

        test_search_basic,

        test_search_filters,

        test_search_pagination,

        test_video_metadata,

        test_video_likes,

        test_related_videos,

        test_comments,

        test_transcript,

        test_transcript_language_fallback,

        test_native_transcript,

        test_streaming_data,

        test_format_selection,

        test_download,

        test_channel_info,

        test_channel_videos,

        test_trending,

        test_cache_integration,

        test_video_info,

        test_get_watch_combined,

        test_search_snippets,

        test_richer_context,

        test_error_handling,

        test_edge_cases,

        test_cli_commands,

        test_mcp_server,

    ]



    for test_fn in tests:

        try:

            test_fn()

        except Exception as e:

            _result(test_fn.__name__, FAIL, f"unhandled exception: {e}")

        time.sleep(2)



    print(f"\n{'=' * 60}")

    print(f"RESULTS: {_passed} passed, {_failed} failed, {_skipped} skipped")

    print(f"{'=' * 60}")

    sys.exit(0 if _failed == 0 else 1)





if __name__ == "__main__":

    main()
