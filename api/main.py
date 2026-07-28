"""FastAPI application factory and server entry point."""



import os



from fastapi import FastAPI



from youtube_ai import __version__



from .errors import register_error_handlers

from .routes import channels, discovery, search, system, videos



API_PREFIX = "/api/v1"





def create_app() -> FastAPI:

    app = FastAPI(

        title="YTAI API",

        summary="HTTP access to the YTAI YouTube SDK",

        description=(

            "Search public YouTube data, retrieve metadata and transcripts, "

            "inspect comments, channels, streaming formats, and download options. "

            "No user-supplied YouTube Data API key is required."

        ),

        version=__version__,

        docs_url="/docs",

        redoc_url="/redoc",

        openapi_url="/openapi.json",

        contact={"name": "YTAI", "url": "https://github.com/vibheksoni/youtube-ai"},

        license_info={"name": "MIT"},

        swagger_ui_parameters={

            "displayRequestDuration": True,

            "filter": True,

            "operationsSorter": "method",

            "tagsSorter": "alpha",

        },

    )

    register_error_handlers(app)

    app.include_router(system.router)

    app.include_router(search.router, prefix=API_PREFIX)

    app.include_router(videos.router, prefix=API_PREFIX)

    app.include_router(channels.router, prefix=API_PREFIX)

    app.include_router(discovery.router, prefix=API_PREFIX)

    return app





app = create_app()





def _port_from_env() -> int:

    raw_port = os.getenv("YTAI_API_PORT", "8000")

    try:

        port = int(raw_port)

    except ValueError as exc:

        raise RuntimeError("YTAI_API_PORT must be an integer") from exc

    if not 1 <= port <= 65535:

        raise RuntimeError("YTAI_API_PORT must be between 1 and 65535")

    return port





def run() -> None:

    """Run the development server from the ``ytai-api`` console command."""

    import uvicorn



    uvicorn.run(

        "api.main:app",

        host=os.getenv("YTAI_API_HOST", "127.0.0.1"),

        port=_port_from_env(),

        log_level=os.getenv("YTAI_API_LOG_LEVEL", "info"),

    )





if __name__ == "__main__":

    run()
