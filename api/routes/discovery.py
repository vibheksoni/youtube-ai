"""Popular-video discovery routes."""



from typing import Annotated



from fastapi import APIRouter, Depends, Query



from youtube_ai import YouTubeClient



from ..dependencies import get_youtube_client

from ..schemas import ERROR_RESPONSES



router = APIRouter(tags=["Discovery"])





@router.get(

    "/trending",

    response_model=list[dict],

    responses=ERROR_RESPONSES,

    summary="Get popular videos",

)

def get_trending(

    limit: Annotated[int, Query(ge=1, le=50)] = 20,

    client: YouTubeClient = Depends(get_youtube_client),

) -> list[dict]:

    return client.get_trending(limit=limit)
