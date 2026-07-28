"""

YTAI SDK - no user-supplied API key required.



Public API:

    from youtube_ai import YouTubeClient, download_video, Cache



    client = YouTubeClient()

    results = client.search("python tutorial")

    video = client.get_video("dQw4w9WgXcQ")

    transcript = client.get_transcript("dQw4w9WgXcQ")

    download_video("dQw4w9WgXcQ", quality="720p")

"""

from .client import YouTubeClient, InnerTubeError, VideoUnavailable

from .cache import Cache

from .download import (

    DownloadError,

    DownloadMode,

    VideoQuality,

    download_video,

    get_download_options,

    select_best_format,

)

from .constants import CLIENTS, ITAG_QUALITY

from .version_fetcher import fetch_live_config, get_web_client_version, get_api_key, get_signature_timestamp, refresh

from .parsers import extract_transcript_params, parse_transcript_segments



__version__ = "0.2.2"

__all__ = [

    "YouTubeClient",

    "InnerTubeError",

    "VideoUnavailable",

    "Cache",

    "download_video",

    "get_download_options",

    "select_best_format",

    "DownloadError",

    "DownloadMode",

    "VideoQuality",

    "CLIENTS",

    "ITAG_QUALITY",

    "fetch_live_config",

    "get_web_client_version",

    "get_api_key",

    "get_signature_timestamp",

    "refresh",

    "extract_transcript_params",

    "parse_transcript_segments",

]
