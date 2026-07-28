"""Service metadata and health routes."""



from fastapi import APIRouter



from youtube_ai import __version__



from ..schemas import HealthResponse, ServiceResponse



router = APIRouter(tags=["Service"])





@router.get(

    "/",

    response_model=ServiceResponse,

    summary="Describe the service",

    include_in_schema=False,

)

def service_index() -> ServiceResponse:

    return ServiceResponse(

        name="YTAI",

        version=__version__,

        status="ok",

        api_version="v1",

        links={"docs": "/docs", "redoc": "/redoc", "openapi": "/openapi.json"},

    )





@router.get(

    "/health",

    response_model=HealthResponse,

    summary="Check service health",

    description="Local process health check. This endpoint does not call YouTube.",

)

def health() -> HealthResponse:

    return HealthResponse(status="ok", service="ytai-api", version=__version__)
