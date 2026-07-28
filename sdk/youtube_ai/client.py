"""

Core InnerTube client using curlcffi for browser-impersonated requests.

No API keys needed — uses YouTube's public InnerTube API.



Fixes curl_cffi DNS issue on Windows by pinning resolved IP addresses

via CURLOPT_RESOLVE, bypassing libcurl's intermittent DNS failures.

"""

from __future__ import annotations



import socket

import time as _time

from urllib.parse import parse_qs, urlencode



import orjson

from curl_cffi import requests as cffi_requests

from curl_cffi import CurlOpt



from .constants import CLIENTS, ENDPOINTS, DEFAULT_CLIENT, SEARCH_CLIENT, PLAYER_CLIENT

from .version_fetcher import fetch_live_config, refresh as refresh_live_config

from .parsers import (

    extract_search_results,

    get_continuation_token,

    extract_video_details,

    extract_streaming_data,

    extract_caption_tracks,

    extract_related_videos,

    extract_channel_info,

    extract_channel_videos,

    extract_likes,

    extract_comment_token,

    extract_comments,

    extract_comment_continuation_token,

    extract_transcript_params,

    parse_transcript_segments,

)

from .cache import Cache





class InnerTubeError(Exception):

    """Base error for InnerTube operations."""





class VideoUnavailable(InnerTubeError):

    pass







_DNS_PIN_DOMAINS = {

    "www.youtube.com",

    "youtubei.googleapis.com",

}





def _should_pin(host: str) -> bool:

    """Check if this host needs IP pinning."""

    if host in _DNS_PIN_DOMAINS:

        return True



    if host.endswith(".googlevideo.com"):

        return True

    return False

_dns_cache: dict[str, str] = {}





def _resolve_host(host: str) -> str | None:

    """Resolve a hostname to an IPv4 address, with caching."""

    if host in _dns_cache:

        return _dns_cache[host]

    try:

        results = socket.getaddrinfo(host, 443, socket.AF_INET)

        if results:

            ip = results[0][4][0]

            _dns_cache[host] = ip

            return ip

    except Exception:

        pass

    return None





def _get_resolve_list(url: str) -> list[str]:

    """Build a CURLOPT_RESOLVE list for known domains in the URL."""

    from urllib.parse import urlparse

    parsed = urlparse(url)

    host = parsed.hostname

    if _should_pin(host):

        ip = _resolve_host(host)

        if ip:

            return [f"{host}:443:{ip}"]

    return []





class YouTubeClient:

    """

    YouTube InnerTube client with browser impersonation via curlcffi.

    No API keys required. All data comes from YouTube's internal API.

    """



    def __init__(

        self,

        client_name: str = DEFAULT_CLIENT,

        cache: Cache | None = None,

        impersonate: str = "chrome131",

    ):

        self.client_config = CLIENTS[client_name]

        self.impersonate = impersonate

        self.cache = cache or Cache()

        self._session = cffi_requests.Session(impersonate=impersonate)



        self._refresh_dns_pins()





        self._live_config: dict = {}

        self._fetch_live_config()



    def _refresh_dns_pins(self):

        """Re-resolve and pin IPs for YouTube domains to bypass curl_cffi DNS bugs."""

        resolve_list = []

        for domain in _DNS_PIN_DOMAINS:

            ip = _resolve_host(domain)

            if ip:

                resolve_list.append(f"{domain}:443:{ip}")

        if resolve_list:

            self._session.curl_options = {CurlOpt.RESOLVE: resolve_list}



    def _pin_host(self, url: str):

        """Add an IP pin for a specific URL's host (for dynamic googlevideo domains)."""

        pins = _get_resolve_list(url)

        if not pins:

            return

        existing = dict(self._session.curl_options)

        existing_resolve = list(existing.get(CurlOpt.RESOLVE, []))

        for pin in pins:

            if pin not in existing_resolve:

                existing_resolve.append(pin)

        existing[CurlOpt.RESOLVE] = existing_resolve

        self._session.curl_options = existing



    def _fetch_live_config(self) -> None:

        """Fetch live InnerTube config from YouTube's homepage.



        Updates self._live_config with the current clientVersion, apiKey,

        and visitorData. STS is fetched lazily on first player request.

        Called on init and on 400 errors.

        """

        try:

            self._live_config = fetch_live_config()

        except Exception:

            self._live_config = {}



    def _get_client_config(self, client_name: str | None = None) -> dict:

        """Return the effective client config, merging live values for WEB client."""

        cfg = dict(CLIENTS[client_name] if client_name else self.client_config)



        if (client_name or self.client_config["clientName"]) == "WEB" and self._live_config:
            if "clientVersion" in self._live_config:
                cfg["clientVersion"] = self._live_config["clientVersion"]
            if "apiKey" in self._live_config:
                cfg["apiKey"] = self._live_config["apiKey"]
        return cfg



    def _build_context(self, client_name: str | None = None) -> dict:

        cfg = self._get_client_config(client_name)

        name = client_name or self.client_config["clientName"]

        ctx = {

            "client": {

                "clientName": cfg["clientName"],

                "clientVersion": cfg["clientVersion"],

                "hl": "en",

                "gl": "US",

            }

        }

        if "androidSdkVersion" in cfg:

            ctx["client"]["androidSdkVersion"] = cfg["androidSdkVersion"]

        if "deviceModel" in cfg:

            ctx["client"]["deviceModel"] = cfg["deviceModel"]



        if name == "WEB":

            if self._live_config.get("visitorData"):

                ctx["client"]["visitorData"] = self._live_config["visitorData"]



            ctx["client"]["browserName"] = "Chrome"

            ctx["client"]["browserVersion"] = "131.0.0.0"

            ctx["client"]["platform"] = "DESKTOP"

            ctx["client"]["timeZone"] = "America/Los_Angeles"

            ctx["client"]["utcOffsetMinutes"] = -420

            ctx["client"]["screenDensityFloat"] = "1"

            ctx["client"]["mainAppWebInfo"] = {

                "graftUrl": "https://www.youtube.com/",

                "webDisplayMode": "WEB_DISPLAY_MODE_BROWSER",

            }

        return ctx



    def _get_headers(self, client_name: str | None = None) -> dict:

        cfg = CLIENTS[client_name] if client_name else self.client_config

        return {

            "Accept": "*/*",

            "Content-Type": "application/json",

            "Origin": "https://www.youtube.com",

            "Referer": cfg.get("referer", "https://www.youtube.com/"),

            "X-Goog-Api-Format-Version": "1",

        }



    def _post(

        self,

        endpoint: str,

        body: dict,

        client_name: str | None = None,

    ) -> dict:

        cfg = self._get_client_config(client_name)

        url = ENDPOINTS[endpoint]

        params = {"key": cfg["apiKey"], "alt": "json"}

        full_url = f"{url}?{urlencode(params)}"

        headers = self._get_headers(client_name)

        ua = cfg.get("userAgent", "")





        full_body = {**body, "context": self._build_context(client_name)}

        data = orjson.dumps(full_body)





        last_err = None

        for attempt in range(3):

            try:

                resp = self._session.post(

                    full_url,

                    data=data,

                    headers=headers,

                    impersonate=self.impersonate,

                    timeout=15,

                )

                break

            except Exception as e:

                last_err = e



                _dns_cache.clear()

                self._refresh_dns_pins()

                if attempt < 2:

                    _time.sleep(2 * (attempt + 1))

                else:

                    raise InnerTubeError(f"Connection failed after 3 retries: {e}") from e

        if resp.status_code != 200:



            if resp.status_code == 400 and not getattr(self, '_live_refreshed', False):

                self._live_refreshed = True

                try:

                    self._live_config = refresh_live_config()

                except Exception:

                    pass

                self._live_refreshed = False



                cfg = self._get_client_config(client_name)

                params = {"key": cfg["apiKey"], "alt": "json"}

                full_url = f"{url}?{urlencode(params)}"

                full_body = {**body, "context": self._build_context(client_name)}

                data = orjson.dumps(full_body)

                try:

                    resp = self._session.post(

                        full_url, data=data, headers=headers,

                        impersonate=self.impersonate, timeout=15,

                    )

                except Exception as e:

                    raise InnerTubeError(f"Retry after config refresh failed: {e}") from e

            if resp.status_code in (403, 404) and client_name and client_name != "WEB":
                from .constants import WEB_API_KEY as _fallback_key
                fallback_cfg = dict(cfg)
                fallback_cfg["apiKey"] = _fallback_key
                fallback_params = {"key": _fallback_key, "alt": "json"}
                fallback_url = f"{url}?{urlencode(fallback_params)}"
                fallback_body = {**body, "context": self._build_context("WEB")}
                fallback_data = orjson.dumps(fallback_body)
                fallback_headers = self._get_headers("WEB")
                try:
                    resp = self._session.post(
                        fallback_url, data=fallback_data, headers=fallback_headers,
                        impersonate=self.impersonate, timeout=15,
                    )
                except Exception as e:
                    raise InnerTubeError(f"WEB key fallback failed: {e}") from e

            if resp.status_code != 200:

                raise InnerTubeError(

                    f"InnerTube {endpoint} returned {resp.status_code}: {resp.text[:500]}"

                )

        return resp.json()



    def search(

        self,

        query: str,

        limit: int = 20,

        filter_type: str | None = None,

        continuation_token: str | None = None,

        use_cache: bool = True,

    ) -> dict:

        """

        Search YouTube for videos, channels, and playlists.



        Returns dict with:

            results: list of parsed result dicts

            continuation_token: str | None for next page

        """

        cache_key = f"{query}:{limit}:{filter_type}:{continuation_token}"

        if use_cache:

            cached = self.cache.get("search", cache_key)

            if cached:

                return cached



        body: dict = {"query": query}

        if filter_type and filter_type in ("video", "channel", "playlist", "movie"):

            from .constants import SEARCH_FILTERS

            body["params"] = SEARCH_FILTERS[filter_type]



        if continuation_token:

            body = {"continuation": continuation_token}



        data = self._post("search", body, client_name=SEARCH_CLIENT)

        results = extract_search_results(data, limit=limit)

        next_token = get_continuation_token(data)



        output = {"results": results, "continuation_token": next_token, "count": len(results)}



        if use_cache:

            self.cache.set("search", cache_key, output, ttl=300)



        return output



    def _player_body(self, video_id: str) -> dict:

        """Build a player request body with optional signatureTimestamp."""

        body: dict = {"videoId": video_id, "contentCheckOk": True, "racyCheckOk": True}



        if "signatureTimestamp" not in self._live_config:

            try:

                from .version_fetcher import _fetch_player_sts

                sts = _fetch_player_sts()

                if sts:

                    self._live_config["signatureTimestamp"] = sts

            except Exception:

                pass

        sts = self._live_config.get("signatureTimestamp")

        if sts:

            body["playbackContext"] = {

                "contentPlaybackContext": {"signatureTimestamp": sts}

            }

        return body



    def get_video(

        self,

        video_id: str,

        use_cache: bool = True,

    ) -> dict:

        """

        Get full video metadata including streaming data and captions.



        Uses get_watch combined endpoint when possible (player + watch-next

        in one call), falls back to separate player + next calls.

        """

        if use_cache:

            cached = self.cache.get("video", video_id)

            if cached:

                return cached















        player_data = None

        next_data = None

        try:

            watch_body = self._watch_body(video_id)

            watch_data = self._post("get_watch", watch_body, client_name=PLAYER_CLIENT)



            if isinstance(watch_data, list) and len(watch_data) >= 2:

                player_data = watch_data[0].get("playerResponse")

                next_data = watch_data[1].get("watchNextResponse")

            elif isinstance(watch_data, dict):

                player_data = watch_data.get("0") or watch_data.get("playerResponse")

                next_data = watch_data.get("1") or watch_data.get("watchNextResponse")

        except Exception:

            pass





        if not player_data:

            player_body = self._player_body(video_id)

            player_data = self._post("player", player_body, client_name=PLAYER_CLIENT)



        details = extract_video_details(player_data)

        self._raise_if_unavailable(video_id, details)



        streaming = extract_streaming_data(player_data)

        captions = extract_caption_tracks(player_data)









        likes = ""

        related = []

        if next_data:

            try:

                related = extract_related_videos(next_data)

                likes = extract_likes(next_data)

            except Exception:

                pass



        if not related and not likes:

            try:

                next_body = {"videoId": video_id}

                web_next = self._post("next", next_body, client_name=SEARCH_CLIENT)

                related = extract_related_videos(web_next)

                likes = extract_likes(web_next)

            except Exception:

                pass





        details["likes"] = likes



        result = {

            "video_id": video_id,

            "details": details,

            "streaming_data": streaming,

            "captions": captions,

            "related_videos": related,

        }



        if use_cache:

            self.cache.set("video", video_id, result, ttl=600)



        return result



    def _raise_if_unavailable(self, video_id: str, details: dict) -> None:

        """Raise for terminal player errors while preserving known partial states."""

        status = details.get("playability_status", "")

        if status in ("OK", "UNPLAYABLE", "LIVE_STREAM_OFFLINE"):

            return

        if status == "ERROR":

            reason = details.get("playability_reason", "")

            raise VideoUnavailable(f"Video {video_id} is unavailable: {reason}")



    def _watch_body(self, video_id: str) -> dict:

        """Build a get_watch request body (combined player + next)."""

        player_req = self._player_body(video_id)

        return {

            "playerRequest": player_req,

            "watchNextRequest": {"videoId": video_id},

        }



    def get_video_info(self, video_id: str, use_cache: bool = True) -> dict:

        """Get just video metadata (no streaming data)."""

        if use_cache:

            cached = self.cache.get("video_info", video_id)

            if cached:

                return cached



        player_body = self._player_body(video_id)

        player_data = self._post("player", player_body, client_name=PLAYER_CLIENT)

        details = extract_video_details(player_data)

        self._raise_if_unavailable(video_id, details)



        if use_cache:

            self.cache.set("video_info", video_id, details, ttl=600)



        return details



    def get_streaming_data(self, video_id: str, use_cache: bool = True) -> dict:

        """Get streaming data (formats, URLs) for a video."""

        if use_cache:

            cached = self.cache.get("streaming", video_id)

            if cached:

                return cached



        player_body = self._player_body(video_id)

        player_data = self._post("player", player_body, client_name=PLAYER_CLIENT)

        details = extract_video_details(player_data)

        self._raise_if_unavailable(video_id, details)

        streaming = extract_streaming_data(player_data)



        if use_cache:

            self.cache.set("streaming", video_id, streaming, ttl=300)



        return streaming



    def get_transcript(

        self,

        video_id: str,

        language_codes: tuple[str, ...] = ("en",),

        use_cache: bool = True,

    ) -> dict:

        """

        Get transcript/captions for a video.



        Tries the native InnerTube get_transcript endpoint first (structured

        segments with startMs/endMs), falls back to XML timedtext if that fails.



        Returns dict with:

            language: str

            language_code: str

            is_generated: bool

            snippets: list[{text, start, duration}]

            available_tracks: list of available caption tracks

        """

        if use_cache:

            cached = self.cache.get("transcript", f"{video_id}:{language_codes}")

            if cached:

                return cached





        try:

            result = self._get_transcript_native(video_id, language_codes)

            if result and result["snippets"]:

                if use_cache:

                    self.cache.set("transcript", f"{video_id}:{language_codes}", result, ttl=3600)

                return result

        except Exception:

            pass





        return self._get_transcript_xml(video_id, language_codes, use_cache)



    def _get_transcript_native(

        self,

        video_id: str,

        language_codes: tuple[str, ...],

    ) -> dict | None:

        """Fetch transcript via native InnerTube get_transcript endpoint.



        Flow:

        1. Call next endpoint to get transcript params from engagement panel

        2. Call get_transcript endpoint with those params

        3. Parse transcriptSegmentRenderer segments

        """



        next_body = {"videoId": video_id}

        next_data = self._post("next", next_body, client_name=SEARCH_CLIENT)

        transcript_params = extract_transcript_params(next_data)

        if not transcript_params:

            return None





        body = {"params": transcript_params}

        transcript_data = self._post("get_transcript", body, client_name=SEARCH_CLIENT)





        snippets = parse_transcript_segments(transcript_data)

        if not snippets:

            return None









        lang_code = language_codes[0] if language_codes else "en"

        lang_name = "English" if lang_code.startswith("en") else lang_code





        tracks_info = []

        try:

            player_body = self._player_body(video_id)

            player_data = self._post("player", player_body, client_name=PLAYER_CLIENT)

            tracks = extract_caption_tracks(player_data)

            tracks_info = [

                {"language_code": t["language_code"], "name": t["name"], "is_generated": t["is_generated"]}

                for t in tracks

            ]



            for t in tracks:

                if t["language_code"].startswith(lang_code):

                    lang_name = t["name"]

                    lang_code = t["language_code"]

                    break

        except Exception:

            pass



        return {

            "video_id": video_id,

            "language": lang_name,

            "language_code": lang_code,

            "is_generated": "asr" in lang_code or "auto" in lang_name.lower(),

            "snippets": snippets,

            "available_tracks": tracks_info,

        }



    def _get_transcript_xml(

        self,

        video_id: str,

        language_codes: tuple[str, ...],

        use_cache: bool = True,

    ) -> dict:

        """Fetch transcript via XML timedtext fallback."""



        player_body = self._player_body(video_id)

        player_data = self._post("player", player_body, client_name=PLAYER_CLIENT)

        tracks = extract_caption_tracks(player_data)



        if not tracks:

            raise InnerTubeError(f"No captions available for video {video_id}")





        selected = None

        for lang in language_codes:

            for track in tracks:

                if track["language_code"].startswith(lang):

                    selected = track

                    break

            if selected:

                break



        if not selected:

            selected = tracks[0]





        base_url = selected["base_url"].replace("&fmt=srv3", "")

        headers = self._get_headers(PLAYER_CLIENT)

        transcript_url = base_url + "&fmt=srv3"

        resp = self._session.get(

            transcript_url,

            headers=headers,

            impersonate=self.impersonate,

            timeout=15,

        )

        if resp.status_code != 200:

            raise InnerTubeError(f"Failed to fetch transcript: {resp.status_code}")



        snippets = self._parse_transcript_xml(resp.text)



        result = {

            "video_id": video_id,

            "language": selected["name"],

            "language_code": selected["language_code"],

            "is_generated": selected["is_generated"],

            "snippets": snippets,

            "available_tracks": [

                {"language_code": t["language_code"], "name": t["name"], "is_generated": t["is_generated"]}

                for t in tracks

            ],

        }



        if use_cache:

            self.cache.set("transcript", f"{video_id}:{language_codes}", result, ttl=3600)



        return result



    def _parse_transcript_xml(self, xml_text: str) -> list[dict]:

        """Parse YouTube's XML transcript format (timedtext).

        Structure: <timedtext><body><p t="1360" d="1680">text</p>...</body></timedtext>

        """

        from html import unescape

        import re

        from defusedxml import ElementTree as ET



        snippets = []

        try:

            root = ET.fromstring(xml_text)



            body = root.find("body")

            if body is None:

                body = root

            for elem in body:

                if elem.tag != "p":

                    continue



                raw_text = "".join(elem.itertext())

                if not raw_text:

                    continue

                text = unescape(re.sub(r"<[^>]*>", "", raw_text))

                start = float(elem.attrib.get("t", "0")) / 1000.0

                duration = float(elem.attrib.get("d", "0")) / 1000.0

                snippets.append({

                    "text": text.strip(),

                    "start": start,

                    "duration": duration,

                })

        except Exception as e:

            raise InnerTubeError(f"Failed to parse transcript XML: {e}")

        return snippets



    def get_channel_info(self, channel_id: str, use_cache: bool = True) -> dict:

        """Get channel metadata."""

        if use_cache:

            cached = self.cache.get("channel", channel_id)

            if cached:

                return cached



        body = {"browseId": channel_id}

        data = self._post("browse", body, client_name=SEARCH_CLIENT)

        info = extract_channel_info(data)



        if use_cache:

            self.cache.set("channel", channel_id, info, ttl=1800)



        return info



    def get_channel_videos(

        self,

        channel_id: str,

        limit: int = 30,

        use_cache: bool = True,

    ) -> list[dict]:

        """Get a channel's uploaded videos."""

        cache_key = f"{channel_id}:videos:{limit}"

        if use_cache:

            cached = self.cache.get("channel_videos", cache_key)

            if cached:

                return cached





        VIDEOS_TAB_PARAMS = "EgZ2aWRlb3PyBgQKAjoA"

        body = {"browseId": channel_id, "params": VIDEOS_TAB_PARAMS}

        data = self._post("browse", body, client_name=SEARCH_CLIENT)

        videos = extract_channel_videos(data)



        if limit and len(videos) > limit:

            videos = videos[:limit]



        if use_cache:

            self.cache.set("channel_videos", cache_key, videos, ttl=600)



        return videos



    def get_trending(

        self,

        limit: int = 20,

        use_cache: bool = True,

    ) -> list[dict]:

        """Get trending/popular videos.



        YouTube deprecated the FEtrending browse endpoint for unauthenticated

        InnerTube access. We use the search endpoint with a broad query and

        the video filter, which returns currently popular videos.

        """

        cache_key = f"trending:{limit}"

        if use_cache:

            cached = self.cache.get("trending", cache_key)

            if cached:

                return cached





        result = self.search("", limit=limit, filter_type="video", use_cache=False)



        if not result.get("results"):

            result = self.search("most popular videos 2024", limit=limit, filter_type="video", use_cache=False)

        results = result.get("results", [])



        if limit and len(results) > limit:

            results = results[:limit]



        if use_cache:

            self.cache.set("trending", cache_key, results, ttl=600)



        return results



    def get_comments(

        self,

        video_id: str,

        limit: int = 20,

        continuation_token: str | None = None,

        use_cache: bool = True,

    ) -> dict:

        """

        Get comments for a YouTube video.



        Args:

            video_id: YouTube video ID

            limit: Maximum comments to return

            continuation_token: Token for paginating to next page of comments

            use_cache: Whether to use cache



        Returns:

            Dict with 'comments' list and 'continuation_token' for next page.

        """

        cache_key = f"{video_id}:{continuation_token or 'first'}"

        if use_cache and continuation_token is None:

            cached = self.cache.get("comments", cache_key)

            if cached:

                return cached



        if continuation_token is None:



            next_body = {"videoId": video_id}

            next_data = self._post("next", next_body, client_name=SEARCH_CLIENT)

            comment_token = extract_comment_token(next_data)

            if not comment_token:

                return {"comments": [], "continuation_token": None}

        else:

            comment_token = continuation_token





        comment_body = {"continuation": comment_token}

        comment_data = self._post("next", comment_body, client_name=SEARCH_CLIENT)



        comments = extract_comments(comment_data)

        if len(comments) > limit:

            comments = comments[:limit]



        next_token = extract_comment_continuation_token(comment_data)



        result = {"comments": comments, "continuation_token": next_token}



        if use_cache and continuation_token is None:

            self.cache.set("comments", cache_key, result, ttl=300)



        return result



    def close(self):

        self._session.close()



    def __enter__(self):

        return self



    def __exit__(self, *args):

        self.close()
