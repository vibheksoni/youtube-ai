"""Stable public error responses for the HTTP API."""



from fastapi import FastAPI, Request

from fastapi.exceptions import RequestValidationError

from fastapi.responses import JSONResponse



from youtube_ai import InnerTubeError, VideoUnavailable





def _error(status_code: int, code: str, message: str) -> JSONResponse:

    return JSONResponse(

        status_code=status_code,

        content={"error": {"code": code, "message": message}},

    )





def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(VideoUnavailable)

    def video_unavailable(_request: Request, _exc: VideoUnavailable) -> JSONResponse:

        return _error(404, "video_unavailable", "The requested video is unavailable.")



    @app.exception_handler(InnerTubeError)

    def innertube_error(_request: Request, _exc: InnerTubeError) -> JSONResponse:

        return _error(502, "upstream_error", "YouTube could not complete the request.")



    @app.exception_handler(RequestValidationError)

    def validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:

        return _error(422, "validation_error", "The request parameters are invalid.")
