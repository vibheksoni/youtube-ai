"""FastAPI contract tests, including live YouTube-backed routes."""



from fastapi.testclient import TestClient



from api.main import app

from youtube_ai import __version__



VIDEO_ID = "dQw4w9WgXcQ"

CHANNEL_ID = "UCuAXFkgsw1L7xaCfnd5JJOw"



client = TestClient(app)





def test_service_metadata_and_openapi():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json()["name"] == "YTAI"



    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {

        "status": "ok",

        "service": "ytai-api",

        "version": __version__,

    }



    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "YTAI API"

    assert "/api/v1/search" in schema["paths"]

    assert "/api/v1/videos/{video_id}/transcript" in schema["paths"]





def test_request_validation_is_bounded_and_sanitized():

    response = client.get("/api/v1/search", params={"q": ""})

    assert response.status_code == 422

    assert response.json() == {

        "error": {

            "code": "validation_error",

            "message": "The request parameters are invalid.",

        }

    }



    assert client.get("/api/v1/search", params={"q": "test", "limit": 51}).status_code == 422

    assert client.get("/api/v1/videos/bad/info").status_code == 422

    assert client.get(f"/api/v1/videos/{VIDEO_ID}/transcript", params={"language": "!"}).status_code == 422

    assert client.get(f"/api/v1/channels/{CHANNEL_ID}/videos", params={"limit": 51}).status_code == 422





def test_live_youtube_routes():

    response = client.get("/api/v1/search", params={"q": "python tutorial", "limit": 2, "type": "video"})

    assert response.status_code == 200

    assert response.json()["count"] == 2



    response = client.get(f"/api/v1/videos/{VIDEO_ID}/info")

    assert response.status_code == 200

    assert response.json()["video_id"] == VIDEO_ID



    response = client.get(f"/api/v1/videos/{VIDEO_ID}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["details"]["title"]

    assert all("url" not in stream for stream in payload["streaming_data"]["adaptive_formats"])

    assert "hls_manifest_url" not in payload["streaming_data"]

    assert "dash_manifest_url" not in payload["streaming_data"]

    assert all("base_url" not in track for track in payload["captions"])



    response = client.get(f"/api/v1/videos/{VIDEO_ID}/transcript", params={"language": "en"})

    assert response.status_code == 200

    assert response.json()["snippets"]



    response = client.get(f"/api/v1/videos/{VIDEO_ID}/comments", params={"limit": 3})

    assert response.status_code == 200

    assert len(response.json()["comments"]) == 3



    response = client.get(f"/api/v1/videos/{VIDEO_ID}/formats")

    assert response.status_code == 200

    formats = response.json()["adaptive_formats"]

    assert formats

    assert all("url" not in stream for stream in formats)

    assert "hls_manifest_url" not in response.json()

    assert "dash_manifest_url" not in response.json()



    response = client.get(f"/api/v1/videos/{VIDEO_ID}/download-options")

    assert response.status_code == 200

    assert "144p" in response.json()["available_qualities"]



    response = client.get(f"/api/v1/channels/{CHANNEL_ID}")

    assert response.status_code == 200

    assert response.json()["title"]



    response = client.get(f"/api/v1/channels/{CHANNEL_ID}/videos", params={"limit": 3})

    assert response.status_code == 200

    assert len(response.json()) == 3



    response = client.get("/api/v1/trending", params={"limit": 3})

    assert response.status_code == 200

    assert len(response.json()) == 3
