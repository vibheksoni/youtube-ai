"""YouTube search routes."""



from typing import Annotated, Literal



from fastapi import APIRouter, Depends, Query



from youtube_ai import YouTubeClient



from ..dependencies import get_youtube_client

from ..schemas import ERROR_RESPONSES, SearchResponse



router = APIRouter(prefix="/search", tags=["Search"])





@router.get(

    "",

    response_model=SearchResponse,

    responses=ERROR_RESPONSES,

    summary="Search YouTube",

    description="Search public videos, channels, playlists, or movies.",

)

def search(

    q: Annotated[str, Query(min_length=1, max_length=200, description="Search query")],

    limit: Annotated[int, Query(ge=1, le=50)] = 20,

    filter_type: Annotated[

        Literal["video", "channel", "playlist", "movie"] | None,

        Query(alias="type", description="Optional result type"),

    ] = None,

    continuation_token: Annotated[

        str | None,

        Query(max_length=4096, description="Token returned by a previous search"),

    ] = None,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.search(

        q,

        limit=limit,

        filter_type=filter_type,

        continuation_token=continuation_token,

    )
