"""Request-scoped dependencies for the HTTP API."""



from collections.abc import Iterator



from youtube_ai import YouTubeClient





def get_youtube_client() -> Iterator[YouTubeClient]:

    """Provide an isolated client and always close its HTTP session."""

    with YouTubeClient() as client:

        yield client
