# YTAI FastAPI Server

The YTAI HTTP API exposes the read-only YouTube SDK through a versioned FastAPI
service. Interactive Swagger UI, ReDoc, and the OpenAPI schema are generated from
the same route definitions and validation models used at runtime.

## Start the API

Install YTAI from the repository:

```bash
git clone https://github.com/vibheksoni/youtube-ai.git
cd youtube-ai
python -m pip install -e .
```

Run the API with the installed command:

```bash
ytai-api
```

The default listener is local-only:

```text
http://127.0.0.1:8000
```

You can also run the module directly:

```bash
python -m api.main
```

## Interactive documentation

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/docs` | Swagger UI for trying requests |
| `http://127.0.0.1:8000/redoc` | ReDoc API reference |
| `http://127.0.0.1:8000/openapi.json` | OpenAPI 3 schema |
| `http://127.0.0.1:8000/health` | Local process health |

## Configuration

The console command accepts configuration through environment variables:

| Variable | Default | Description |
|---|---:|---|
| `YTAI_API_HOST` | `127.0.0.1` | Listener address |
| `YTAI_API_PORT` | `8000` | Listener port from 1 to 65535 |
| `YTAI_API_LOG_LEVEL` | `info` | Uvicorn log level |

PowerShell example:

```powershell
$env:YTAI_API_PORT = "8080"
ytai-api
```

Linux or macOS example:

```bash
YTAI_API_PORT=8080 ytai-api
```

Binding to `0.0.0.0` makes the service reachable from other machines. Add a
reverse proxy, TLS, request limits, authentication, and rate limiting before
exposing it to an untrusted network.

## Endpoints

All data routes use the `/api/v1` prefix.

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service metadata and documentation links |
| `GET` | `/health` | Local process health without a YouTube request |
| `GET` | `/api/v1/search` | Search videos, channels, playlists, or movies |
| `GET` | `/api/v1/videos/{video_id}` | Complete video data |
| `GET` | `/api/v1/videos/{video_id}/info` | Lightweight video metadata |
| `GET` | `/api/v1/videos/{video_id}/transcript` | Timestamped transcript |
| `GET` | `/api/v1/videos/{video_id}/comments` | Paginated comments |
| `GET` | `/api/v1/videos/{video_id}/formats` | Sanitized streaming format metadata |
| `GET` | `/api/v1/videos/{video_id}/download-options` | Download qualities, codecs, modes, and sizes |
| `GET` | `/api/v1/channels/{channel_id}` | Channel metadata |
| `GET` | `/api/v1/channels/{channel_id}/videos` | Recent channel videos |
| `GET` | `/api/v1/trending` | Popular video results |

Media transfer is intentionally not exposed over HTTP. Use `download_video()` or
the `ytai download` CLI command for bounded, resumable downloads.

## Quick examples

Search public videos:

```bash
curl "http://127.0.0.1:8000/api/v1/search?q=python%20tutorial&type=video&limit=5"
```

Get video metadata:

```bash
curl "http://127.0.0.1:8000/api/v1/videos/dQw4w9WgXcQ/info"
```

Get an English transcript:

```bash
curl "http://127.0.0.1:8000/api/v1/videos/dQw4w9WgXcQ/transcript?language=en"
```

Get comments and retain the returned continuation token for another request:

```bash
curl "http://127.0.0.1:8000/api/v1/videos/dQw4w9WgXcQ/comments?limit=10"
```

Inspect available download formats:

```bash
curl "http://127.0.0.1:8000/api/v1/videos/dQw4w9WgXcQ/download-options"
```

Get recent channel uploads:

```bash
curl "http://127.0.0.1:8000/api/v1/channels/UCuAXFkgsw1L7xaCfnd5JJOw/videos?limit=5"
```

## Validation limits

The API rejects invalid or excessive inputs before making a YouTube request:

- Search queries: 1 to 200 characters
- Search, channel, and trending limits: 1 to 50
- Comment limits: 1 to 100
- YouTube video IDs: exactly 11 URL-safe characters
- YouTube channel IDs: `UC` followed by 22 URL-safe characters
- Language codes: 2 to 15 letters, numbers, or hyphens
- Continuation tokens: at most 4096 characters

## Errors

Errors use a stable envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request parameters are invalid."
  }
}
```

| Status | Code | Meaning |
|---:|---|---|
| `404` | `video_unavailable` | The requested video cannot be accessed |
| `422` | `validation_error` | A path or query parameter is invalid |
| `502` | `upstream_error` | YouTube could not complete the request |

Raw upstream response bodies, signed streaming/caption URLs, internal retry
details, and stack traces are not returned to API clients.

## Application integration

Import the ready application:

```python
from api.main import app
```

Or create an independent FastAPI instance for tests or composition:

```python
from api.main import create_app

app = create_app()
```

Each request receives its own `YouTubeClient`. The client is closed after the
response, while the SDK's SQLite cache remains shared across requests.
