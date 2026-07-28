"""Video, transcript, comment, and format routes."""



from typing import Annotated



from fastapi import APIRouter, Depends, Path, Query



from youtube_ai import YouTubeClient, get_download_options



from ..dependencies import get_youtube_client

from ..schemas import (

    CommentsResponse,

    DownloadOptionsResponse,

    ERROR_RESPONSES,

    StreamingData,

    TranscriptResponse,

    VideoDetails,

    VideoResponse,

)



router = APIRouter(prefix="/videos", tags=["Videos"])



VideoId = Annotated[

    str,

    Path(pattern=r"^[A-Za-z0-9_-]{11}$", description="Eleven-character YouTube video ID"),

]





@router.get(

    "/{video_id}",

    response_model=VideoResponse,

    responses=ERROR_RESPONSES,

    summary="Get complete video data",

    description="Return metadata, likes, streaming formats, captions, and related videos.",

)

def get_video(

    video_id: VideoId,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_video(video_id)





@router.get(

    "/{video_id}/info",

    response_model=VideoDetails,

    responses=ERROR_RESPONSES,

    summary="Get lightweight video metadata",

)

def get_video_info(

    video_id: VideoId,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_video_info(video_id)





@router.get(

    "/{video_id}/transcript",

    response_model=TranscriptResponse,

    responses=ERROR_RESPONSES,

    summary="Get a timestamped transcript",

)

def get_transcript(

    video_id: VideoId,

    language: Annotated[

        str,

        Query(min_length=2, max_length=15, pattern=r"^[A-Za-z0-9-]+$"),

    ] = "en",

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_transcript(video_id, language_codes=(language,))





@router.get(

    "/{video_id}/comments",

    response_model=CommentsResponse,

    responses=ERROR_RESPONSES,

    summary="Get paginated video comments",

)

def get_comments(

    video_id: VideoId,

    limit: Annotated[int, Query(ge=1, le=100)] = 20,

    continuation_token: Annotated[str | None, Query(max_length=4096)] = None,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_comments(

        video_id,

        limit=limit,

        continuation_token=continuation_token,

    )





@router.get(

    "/{video_id}/formats",

    response_model=StreamingData,

    responses=ERROR_RESPONSES,

    summary="Get streaming formats",

    description="Return sanitized progressive and adaptive stream metadata without signed URLs.",

)

def get_formats(

    video_id: VideoId,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_streaming_data(video_id)





@router.get(

    "/{video_id}/download-options",

    response_model=DownloadOptionsResponse,

    responses=ERROR_RESPONSES,

    summary="Inspect download options",

    description="Return metadata, qualities, codecs, sizes, and supported download modes.",

)

def download_options(

    video_id: VideoId,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return get_download_options(video_id, client=client)
