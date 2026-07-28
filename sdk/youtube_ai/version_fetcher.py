"""

Dynamic version fetcher — keeps InnerTube client configs up-to-date.



YouTube rotates clientVersion on every deploy (often daily). Hardcoding it

means requests eventually break with 400 INVALID_ARGUMENT or similar.



This module fetches the YouTube homepage HTML, extracts the live

ytcfg.set({...}) config block, and returns:

  - clientVersion (e.g. "2.20260724.01.01")

  - apiKey       (the current live client key)

  - signatureTimestamp / STS (e.g. 20655) — needed for player requests

  - visitorData  — per-session visitor ID (optional, improves reliability)



The result is cached in-memory with a 1-hour TTL. On failure, falls back

to the last known-good values from constants.py.

"""

from __future__ import annotations



import os
import re

import time

import threading

from typing import Any



from .constants import CLIENTS, WEB_API_KEY





_HOMEPAGE_URL = "https://www.youtube.com/"

_FETCH_TIMEOUT = 15

_CACHE_TTL = 3600



_lock = threading.Lock()

_cache: dict[str, Any] | None = None

_cache_ts: float = 0.0





def _extract_ytcfg(html: str) -> dict[str, Any]:

    """Extract InnerTube config values from YouTube homepage HTML.



    YouTube's HTML contains ``ytcfg.set({...})`` calls with live config.

    We regex for the specific keys we need rather than parsing the full

    JS object (which would require a JS parser).

    """

    result: dict[str, Any] = {}





    m = re.search(r'"INNERTUBE_CLIENT_VERSION"\s*:\s*"([^"]+)"', html)

    if m:

        result["clientVersion"] = m.group(1)





    m = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html)

    if m:

        result["apiKey"] = m.group(1)





    m = re.search(r'"STS"\s*:\s*(\d+)', html)

    if m:

        result["signatureTimestamp"] = int(m.group(1))





    m = re.search(r'"visitorData"\s*:\s*"([^"]+)"', html)

    if m:

        result["visitorData"] = m.group(1)





    m = re.search(r'"INNERTUBE_CLIENT_NAME"\s*:\s*"([^"]+)"', html)

    if m:

        result["clientName"] = m.group(1)



    return result





def _fetch_homepage_html() -> str:

    """Fetch the YouTube homepage HTML (first ~300KB is enough for ytcfg)."""

    import requests as std_requests



    resp = std_requests.get(

        _HOMEPAGE_URL,

        headers={

            "User-Agent": CLIENTS["WEB"]["userAgent"],

            "Accept": "text/html,application/xhtml+xml",

            "Accept-Language": "en-US,en;q=0.9",

        },

        timeout=_FETCH_TIMEOUT,

    )

    resp.raise_for_status()

    return resp.text[:300_000]





def _fetch_player_config() -> dict[str, Any]:
    """Fetch current client values from the player JavaScript bundle."""
    import requests as std_requests

    html = _fetch_homepage_html()
    match = re.search(r'"jsUrl"\s*:\s*"([^"]+)"', html)
    if not match:
        match = re.search(r'(/s/player/[a-f0-9]+/player_\w+\.js)', html)
    if not match:
        return {}

    player_js_url = match.group(1)
    if not player_js_url.startswith("http"):
        player_js_url = "https://www.youtube.com" + player_js_url
    response = std_requests.get(
        player_js_url,
        headers={"User-Agent": CLIENTS["WEB"]["userAgent"]},
        timeout=_FETCH_TIMEOUT,
    )
    response.raise_for_status()
    js = response.text
    config: dict[str, Any] = {}
    for key, pattern in {
        "apiKey": r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"',
        "clientVersion": r'"INNERTUBE_CLIENT_VERSION"\s*:\s*"([^"]+)"',
    }.items():
        value = re.search(pattern, js)
        if value:
            config[key] = value.group(1)
    sts = re.search(r'"STS"\s*:\s*(\d+)', js) or re.search(
        r'signatureTimestamp\s*:\s*(\d+)', js
    )
    if sts:
        config["signatureTimestamp"] = int(sts.group(1))
    return config


def _fetch_player_sts() -> int | None:
    """Fetch the current player signature timestamp."""
    try:
        return _fetch_player_config().get("signatureTimestamp")
    except (OSError, RuntimeError, ValueError):
        return None


def fetch_live_config(force: bool = False) -> dict[str, Any]:

    """Fetch live InnerTube config from YouTube's homepage.



    Returns a dict with keys:

      - clientVersion: str

      - apiKey: str

      - signatureTimestamp: int

      - visitorData: str (may be absent)

      - clientName: str



    Results are cached for 1 hour. On failure, returns the last cached

    result or falls back to the YTAI_API_KEY environment variable.



    Args:

        force: Bypass cache and force a fresh fetch.

    """

    global _cache, _cache_ts



    with _lock:

        now = time.time()

        if _cache and not force and (now - _cache_ts) < _CACHE_TTL:

            return _cache



        try:

            html = _fetch_homepage_html()

            config = _extract_ytcfg(html)
            if not config.get("apiKey"):
                config.update(_fetch_player_config())

            if config.get("clientVersion") and config.get("apiKey"):

                _cache = config

                _cache_ts = now

                return config

        except Exception:

            pass





        if _cache:

            return _cache



        return {

            "clientVersion": CLIENTS["WEB"]["clientVersion"],

            "apiKey": WEB_API_KEY,

            "clientName": "WEB",

        }





def get_web_client_version() -> str:

    """Convenience: return the current live WEB clientVersion."""

    return fetch_live_config().get("clientVersion", CLIENTS["WEB"]["clientVersion"])





def get_api_key() -> str:

    """Convenience: return the current live API key."""

    return fetch_live_config().get("apiKey", WEB_API_KEY)





def get_signature_timestamp() -> int | None:

    """Convenience: return the current signature timestamp (STS)."""

    return fetch_live_config().get("signatureTimestamp")





def get_visitor_data() -> str | None:

    """Convenience: return the current visitorData token."""

    return fetch_live_config().get("visitorData")





def refresh() -> dict[str, Any]:

    """Force-refresh the live config. Useful after a 400 error."""

    return fetch_live_config(force=True)
