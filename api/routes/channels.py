"""Channel routes."""



from typing import Annotated



from fastapi import APIRouter, Depends, Path, Query



from youtube_ai import YouTubeClient



from ..dependencies import get_youtube_client

from ..schemas import ChannelInfo, ERROR_RESPONSES



router = APIRouter(prefix="/channels", tags=["Channels"])



ChannelId = Annotated[

    str,

    Path(pattern=r"^UC[A-Za-z0-9_-]{22}$", description="YouTube channel ID"),

]





@router.get(

    "/{channel_id}",

    response_model=ChannelInfo,

    responses=ERROR_RESPONSES,

    summary="Get channel metadata",

)

def get_channel_info(

    channel_id: ChannelId,

    client: YouTubeClient = Depends(get_youtube_client),

) -> dict:

    return client.get_channel_info(channel_id)





@router.get(

    "/{channel_id}/videos",

    response_model=list[dict],

    responses=ERROR_RESPONSES,

    summary="Get recent channel videos",

)

def get_channel_videos(

    channel_id: ChannelId,

    limit: Annotated[int, Query(ge=1, le=50)] = 30,

    client: YouTubeClient = Depends(get_youtube_client),

) -> list[dict]:

    return client.get_channel_videos(channel_id, limit=limit)
