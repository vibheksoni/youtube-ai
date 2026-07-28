"""OpenAPI response models for the YTAI HTTP API."""



from typing import Any



from pydantic import BaseModel, ConfigDict





class ApiModel(BaseModel):

    model_config = ConfigDict(extra="allow")





class ErrorDetail(BaseModel):

    code: str

    message: str





class ErrorResponse(BaseModel):

    error: ErrorDetail





class ServiceLinks(BaseModel):

    docs: str

    redoc: str

    openapi: str





class ServiceResponse(BaseModel):

    name: str

    version: str

    status: str

    api_version: str

    links: ServiceLinks





class HealthResponse(BaseModel):

    status: str

    service: str

    version: str





class SearchResponse(BaseModel):

    results: list[dict[str, Any]]

    continuation_token: str | None = None

    count: int





class VideoDetails(ApiModel):

    video_id: str = ""

    title: str = ""

    author: str = ""

    channel_id: str = ""

    length_seconds: int = 0

    view_count: int = 0

    description: str = ""

    likes: str = ""

    playability_status: str = ""





class StreamFormat(BaseModel):

    itag: int | None = None

    mime_type: str = ""

    bitrate: int = 0

    width: int | None = None

    height: int | None = None

    fps: int | None = None

    quality: str = ""

    quality_label: str = ""

    content_length: int | str | None = None

    has_audio: bool = False

    has_video: bool = False

    is_progressive: bool = False





class StreamingData(BaseModel):

    formats: list[StreamFormat]

    adaptive_formats: list[StreamFormat]





class CaptionTrack(BaseModel):

    name: str = ""

    language_code: str = ""

    is_generated: bool = False





class VideoResponse(BaseModel):

    video_id: str

    details: VideoDetails

    streaming_data: StreamingData

    captions: list[CaptionTrack]

    related_videos: list[dict[str, Any]]





class TranscriptSnippet(BaseModel):

    text: str

    start: float

    duration: float

    start_time: str | None = None





class TranscriptTrack(BaseModel):

    language_code: str

    name: str

    is_generated: bool





class TranscriptResponse(BaseModel):

    video_id: str

    language: str

    language_code: str

    is_generated: bool

    snippets: list[TranscriptSnippet]

    available_tracks: list[TranscriptTrack]





class Comment(ApiModel):

    comment_id: str = ""

    author: str = ""

    author_id: str = ""

    author_avatar: str = ""

    is_verified: bool = False

    text: str = ""

    published_time: str = ""

    likes: str | int = ""

    reply_count: str | int = ""





class CommentsResponse(BaseModel):

    comments: list[Comment]

    continuation_token: str | None = None





class ChannelInfo(ApiModel):

    channel_id: str = ""

    title: str = ""

    avatar: str | None = None

    subscribers: str = ""

    banner: str | None = None

    video_count: str = ""

    description: str = ""





class DownloadOptionsResponse(BaseModel):

    video_id: str

    title: str

    author: str

    duration_seconds: int

    view_count: int

    available_qualities: list[str]

    supported_modes: list[str]

    ffmpeg_available: bool

    video_formats: list[StreamFormat]

    audio_formats: list[StreamFormat]





ERROR_RESPONSES = {

    404: {"model": ErrorResponse, "description": "The requested resource is unavailable."},

    422: {"model": ErrorResponse, "description": "The request parameters are invalid."},

    502: {"model": ErrorResponse, "description": "YouTube could not complete the request."},

}
