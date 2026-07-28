"""

Text and data parsing utilities for InnerTube responses.

Handles the various nested renderer structures YouTube returns.

"""

from __future__ import annotations



import re

from typing import Any





def get_text(obj: Any) -> str:

    """Extract text from InnerTube text objects (simpleText, runs, or string)."""

    if isinstance(obj, str):

        return obj

    if isinstance(obj, dict):

        if "simpleText" in obj:

            return obj["simpleText"]

        if "runs" in obj:

            return "".join(run.get("text", "") for run in obj["runs"])

    return ""





def parse_duration(duration_text: str) -> int:

    """Parse '3:45' or '1:02:30' to seconds."""

    if not duration_text:

        return 0

    parts = duration_text.strip().split(":")

    try:

        parts = [int(p) for p in parts]

    except ValueError:

        return 0

    if len(parts) == 2:

        return parts[0] * 60 + parts[1]

    elif len(parts) == 3:

        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    return 0





def parse_number(text: str) -> int:

    """Parse '1.2M views' -> 1200000, '15K' -> 15000."""

    if not text:

        return 0

    text = text.upper().replace(",", "").replace(" ", "")

    match = re.search(r"([\d.]+)\s*([KMB])?", text)

    if not match:

        return 0

    num = float(match.group(1))

    mult = match.group(2)

    if mult == "K":

        return int(num * 1_000)

    elif mult == "M":

        return int(num * 1_000_000)

    elif mult == "B":

        return int(num * 1_000_000_000)

    return int(num)





def get_thumbnail(thumbnails: list[dict] | None, quality: str = "high") -> str | None:

    """Get best thumbnail URL."""

    if not thumbnails:

        return None

    if quality == "high" and thumbnails:

        return thumbnails[-1].get("url")

    elif quality == "medium" and len(thumbnails) > 1:

        return thumbnails[len(thumbnails) // 2].get("url")

    return thumbnails[0].get("url") if thumbnails else None





def parse_video_renderer(renderer: dict) -> dict:

    """Parse a videoRenderer into a clean dict."""

    video_id = renderer.get("videoId", "")

    if not video_id:

        return {}



    title = get_text(renderer.get("title", {}))

    thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])

    thumbnail = get_thumbnail(thumbnails)



    duration_text = get_text(renderer.get("lengthText", {}))

    duration_seconds = parse_duration(duration_text)



    view_count_text = get_text(renderer.get("viewCountText", {}))

    view_count = parse_number(view_count_text)



    published_time = get_text(renderer.get("publishedTimeText", {}))

    channel_name = get_text(renderer.get("ownerText", {}))

    channel_id = ""

    owner = renderer.get("ownerText", {})

    if "runs" in owner:

        runs = owner["runs"]

        if runs and "navigationEndpoint" in runs[0]:

            browse_ep = runs[0]["navigationEndpoint"].get("browseEndpoint", {})

            channel_id = browse_ep.get("browseId", "")



    description = get_text(renderer.get("descriptionSnippet", {}))





    detail_snippets = extract_search_snippets(renderer)

    if detail_snippets and not description:

        description = detail_snippets[0]



    result = {

        "video_id": video_id,

        "title": title,

        "thumbnail": thumbnail,

        "duration": duration_text,

        "duration_seconds": duration_seconds,

        "views": view_count,

        "view_count_text": view_count_text,

        "published": published_time,

        "channel": {"name": channel_name, "id": channel_id},

        "description": description,

        "url": f"https://www.youtube.com/watch?v={video_id}",

    }

    if detail_snippets:

        result["snippets"] = detail_snippets

    return result





def parse_channel_renderer(renderer: dict) -> dict:

    """Parse a channelRenderer."""

    channel_id = renderer.get("channelId", "")

    if not channel_id:

        return {}

    return {

        "channel_id": channel_id,

        "title": get_text(renderer.get("title", {})),

        "thumbnail": get_thumbnail(

            renderer.get("thumbnail", {}).get("thumbnails", [])

        ),

        "subscribers": get_text(renderer.get("subscriberCountText", {})),

        "video_count": get_text(renderer.get("videoCountText", {})),

        "description": get_text(renderer.get("descriptionSnippet", {})),

    }





def parse_playlist_renderer(renderer: dict) -> dict:

    """Parse a playlistRenderer."""

    playlist_id = renderer.get("playlistId", "")

    if not playlist_id:

        return {}

    thumbs = renderer.get("thumbnails", [])

    if thumbs and isinstance(thumbs[0], dict):

        thumbs = thumbs[0].get("thumbnails", [])

    return {

        "playlist_id": playlist_id,

        "title": get_text(renderer.get("title", {})),

        "thumbnail": get_thumbnail(thumbs),

        "video_count": get_text(renderer.get("videoCount", {})),

        "channel": get_text(renderer.get("shortBylineText", {})),

    }





def extract_search_results(data: dict, limit: int = 20) -> list[dict]:

    """Extract video/channel/playlist results from a search response."""

    results: list[dict] = []



    contents = data.get("contents", {})

    two_col = contents.get("twoColumnSearchResultsRenderer", {})

    primary = two_col.get("primaryContents", {})

    section_list = primary.get("sectionListRenderer", {})

    sections = section_list.get("contents", [])





    if not sections:

        commands = data.get("onResponseReceivedCommands", [])

        for cmd in commands:

            if "appendContinuationItemsAction" in cmd:

                sections = cmd["appendContinuationItemsAction"].get("continuationItems", [])

                break

            if "reloadContinuationItemsCommand" in cmd:

                sections = cmd["reloadContinuationItemsCommand"].get("continuationItems", [])

                break



    for section in sections:

        items = section.get("itemSectionRenderer", {}).get("contents", [])

        if not items:



            items = [section] if "videoRenderer" in section or "channelRenderer" in section else sections



        for item in items:

            if "videoRenderer" in item:

                parsed = parse_video_renderer(item["videoRenderer"])

                if parsed:

                    results.append({"type": "video", **parsed})

            elif "channelRenderer" in item:

                parsed = parse_channel_renderer(item["channelRenderer"])

                if parsed:

                    results.append({"type": "channel", **parsed})

            elif "playlistRenderer" in item:

                parsed = parse_playlist_renderer(item["playlistRenderer"])

                if parsed:

                    results.append({"type": "playlist", **parsed})

            elif "shelfRenderer" in item:



                shelf = item["shelfRenderer"]

                shelf_items = (

                    shelf.get("content", {})

                    .get("verticalListRenderer", {})

                    .get("items", [])

                )

                for si in shelf_items:

                    if "videoRenderer" in si:

                        parsed = parse_video_renderer(si["videoRenderer"])

                        if parsed:

                            results.append({"type": "video", **parsed})

            if len(results) >= limit:

                return results

    return results





def get_continuation_token(data: dict) -> str | None:

    """Extract continuation token for paginating search results."""

    contents = data.get("contents", {})

    two_col = contents.get("twoColumnSearchResultsRenderer", {})

    primary = two_col.get("primaryContents", {})

    section_list = primary.get("sectionListRenderer", {})

    sections = section_list.get("contents", [])



    for section in sections:

        cont = section.get("continuationItemRenderer", {})

        if cont:

            endpoint = cont.get("continuationEndpoint", {})

            return endpoint.get("continuationCommand", {}).get("token")





    for cmd in data.get("onResponseReceivedCommands", []):

        if "appendContinuationItemsAction" in cmd:

            items = cmd["appendContinuationItemsAction"].get("continuationItems", [])

            for item in items:

                cont = item.get("continuationItemRenderer", {})

                if cont:

                    return cont.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

    return None





def extract_likes(next_data: dict) -> str:

    """Extract like count from the next endpoint response.



    YouTube stores likes in videoPrimaryInfoRenderer -> videoActions -> menuRenderer

    -> topLevelButtons -> segmentedLikeDislikeButtonViewModel -> likeButtonViewModel

    -> ... -> buttonViewModel -> title (e.g. '19M').

    """

    primary = _find_key(next_data, "videoPrimaryInfoRenderer")

    if not primary:

        return ""

    val = primary[0][1]

    top_buttons = val.get("videoActions", {}).get("menuRenderer", {}).get("topLevelButtons", [])

    for btn in top_buttons:



        segmented = btn.get("segmentedLikeDislikeButtonViewModel", {})

        if not segmented:

            continue

        like_vm = segmented.get("likeButtonViewModel", {})



        if "likeButtonViewModel" in like_vm:

            like_vm = like_vm["likeButtonViewModel"]

        if "toggleButtonViewModel" in like_vm:

            like_vm = like_vm["toggleButtonViewModel"]

        if "toggleButtonViewModel" in like_vm:

            like_vm = like_vm["toggleButtonViewModel"]

        default_btn = like_vm.get("defaultButtonViewModel", {})

        button_vm = default_btn.get("buttonViewModel", {})

        title = button_vm.get("title", "")

        if title:

            return title

    return ""





def extract_comment_token(next_data: dict) -> str | None:

    """Extract the comment section continuation token from a next response."""

    sections = _find_key(next_data, "itemSectionRenderer")

    for _path, val in sections:

        if val.get("sectionIdentifier") == "comment-item-section":

            conts = _find_key(val, "continuationItemRenderer")

            for _cp, cv in conts:

                token = cv.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

                if token:

                    return token

    return None





def extract_comments(comment_data: dict) -> list[dict]:

    """Parse comments from a comment continuation response.



    YouTube returns comments in two parts:

    1. commentThreadRenderer — contains the thread structure and viewModel reference

    2. commentEntityPayload (in frameworkUpdates.entityBatchUpdate.mutations) — contains

       the actual comment data (author, text, likes, reply count)

    """



    entities = _find_key(comment_data, "commentEntityPayload")

    entity_map: dict[str, dict] = {}

    for _path, ent in entities:

        key = ent.get("key", "")

        if key:

            entity_map[key] = ent



    results = []



    threads = _find_key(comment_data, "commentThreadRenderer")

    for _path, thread in threads:

        vm = thread.get("commentViewModel", {})



        inner_vm = vm.get("commentViewModel", vm)

        comment_key = inner_vm.get("commentKey", "")





        ent = entity_map.get(comment_key, {})

        if not ent:



            comment_id = inner_vm.get("commentId", "")

            for ek, ev in entity_map.items():

                if ev.get("properties", {}).get("commentId") == comment_id:

                    ent = ev

                    break



        if not ent:

            continue



        props = ent.get("properties", {})

        author = ent.get("author", {})

        toolbar = ent.get("toolbar", {})



        comment_id = props.get("commentId", "")

        text = props.get("content", {}).get("content", "")

        author_name = author.get("displayName", "")

        author_id = author.get("channelId", "")

        author_avatar = author.get("avatarThumbnailUrl", "")

        is_verified = author.get("isVerified", False)

        published_time = props.get("publishedTime", "")

        like_count = toolbar.get("likeCountNotliked", "")

        reply_count = toolbar.get("replyCount", "")



        results.append({

            "comment_id": comment_id,

            "author": author_name,

            "author_id": author_id,

            "author_avatar": author_avatar,

            "is_verified": is_verified,

            "text": text,

            "published_time": published_time,

            "likes": like_count,

            "reply_count": reply_count,

        })



    return results





def extract_comment_continuation_token(comment_data: dict) -> str | None:

    """Extract continuation token for loading more comments."""

    for cmd in comment_data.get("onResponseReceivedEndpoints", []):

        cont_items = cmd.get("reloadContinuationItemsCommand", {}).get("continuationItems", [])

        if not cont_items:

            cont_items = cmd.get("appendContinuationItemsAction", {}).get("continuationItems", [])

        for item in cont_items:

            cont = item.get("continuationItemRenderer", {})

            if cont:

                token = cont.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

                if token:

                    return token

    return None





def extract_video_details(player_data: dict) -> dict:

    """Extract clean video metadata from player response."""

    details = player_data.get("videoDetails", {})

    playability = player_data.get("playabilityStatus", {})



    return {

        "video_id": details.get("videoId", ""),

        "title": details.get("title", ""),

        "author": details.get("author", ""),

        "channel_id": details.get("channelId", ""),

        "length_seconds": int(details.get("lengthSeconds", 0)),

        "view_count": int(details.get("viewCount", 0)),

        "description": details.get("shortDescription", ""),

        "is_live": details.get("isLiveContent", False),

        "is_private": details.get("isPrivate", False),

        "thumbnails": details.get("thumbnail", {}).get("thumbnails", []),

        "keywords": details.get("keywords", []),

        "average_rating": details.get("averageRating", 0),

        "allow_ratings": details.get("allowRatings", False),

        "playability_status": playability.get("status", ""),

        "playability_reason": playability.get("reason", ""),

    }





def extract_streaming_data(player_data: dict) -> dict:

    """Extract streaming formats from player response."""

    sd = player_data.get("streamingData", {})

    formats = sd.get("formats", [])

    adaptive = sd.get("adaptiveFormats", [])



    def parse_fmt(f: dict) -> dict:

        url = f.get("url", "")

        if not url:



            from urllib.parse import parse_qs

            cipher = f.get("signatureCipher", "") or f.get("cipher", "")

            if cipher:

                qs = parse_qs(cipher)

                url = qs.get("url", [""])[0]

        itag = f.get("itag", 0)

        mime = f.get("mimeType", "")

        has_audio = (

            "audio" in mime.lower()

            or bool(f.get("audioQuality"))

            or bool(f.get("audioChannels"))

            or "mp4a" in mime.lower()

            or "opus" in mime.lower()

            or "vorbis" in mime.lower()

        )

        has_video = "video" in mime.lower() or bool(f.get("width")) or bool(f.get("height"))

        return {

            "itag": itag,

            "url": url,

            "mime_type": mime,

            "bitrate": f.get("bitrate", 0),

            "width": f.get("width"),

            "height": f.get("height"),

            "fps": f.get("fps"),

            "quality": f.get("quality", ""),

            "quality_label": f.get("qualityLabel", ""),

            "duration_ms": f.get("approxDurationMs", 0),

            "content_length": f.get("contentLength", ""),

            "last_modified": f.get("lastModified", ""),

            "audio_channels": f.get("audioChannels"),

            "audio_quality": f.get("audioQuality"),

            "audio_sample_rate": f.get("audioSampleRate"),

            "has_audio": has_audio,

            "has_video": has_video,

            "is_progressive": has_audio and has_video,

        }



    return {

        "formats": [parse_fmt(f) for f in formats],

        "adaptive_formats": [parse_fmt(f) for f in adaptive],

        "hls_manifest_url": sd.get("hlsManifestUrl"),

        "dash_manifest_url": sd.get("dashManifestUrl"),

    }





def extract_caption_tracks(player_data: dict) -> list[dict]:

    """Extract caption track info from player response."""

    captions = player_data.get("captions", {})

    renderer = captions.get("playerCaptionsTracklistRenderer", {})

    tracks = renderer.get("captionTracks", [])

    translation_langs = renderer.get("translationLanguages", [])



    result = []

    for track in tracks:

        result.append({

            "base_url": track.get("baseUrl", ""),

            "name": get_text(track.get("name", {})),

            "language_code": track.get("languageCode", ""),

            "kind": track.get("kind", ""),

            "is_generated": track.get("kind", "") == "asr",

            "is_translatable": track.get("isTranslatable", False),

            "track_id": track.get("trackId", ""),

        })



    return result





def _parse_lockup_view_model(lockup: dict) -> dict:

    """Parse a lockupViewModel (newer related-video format)."""

    content_image = lockup.get("contentImage", {})

    thumb_vm = content_image.get("thumbnailViewModel", {})

    image_sources = thumb_vm.get("image", {}).get("sources", [])

    thumbnail = get_thumbnail(image_sources) if image_sources else None





    duration = ""

    video_id = ""

    overlays = thumb_vm.get("overlays", [])

    for overlay in overlays:

        badges = overlay.get("thumbnailBottomOverlayViewModel", {}).get("badges", [])

        for badge in badges:

            tbvm = badge.get("thumbnailBadgeViewModel", {})

            if not duration:

                duration = tbvm.get("text", "")

            target_id = tbvm.get("animationActivationTargetId", "")

            if target_id and not video_id:

                video_id = target_id





    if not video_id:

        _r = _find_key(lockup, "watchEndpoint")

        if _r:

            video_id = _r[0][1].get("videoId", "")





    meta = lockup.get("metadata", {}).get("lockupMetadataViewModel", {})

    title = meta.get("title", {}).get("content", "")





    channel_name = ""

    channel_id = ""

    view_text = ""

    published = ""

    image_obj = meta.get("image", {})

    if "decoratedAvatarViewModel" in image_obj:

        channel_name = image_obj["decoratedAvatarViewModel"].get("a11yLabel", "").replace("Go to channel ", "")

        onTap = image_obj["decoratedAvatarViewModel"].get("rendererContext", {}).get("commandContext", {}).get("onTap", {})

        browse = _find_key(onTap, "browseEndpoint")

        if browse:

            channel_id = browse[0][1].get("browseId", "")





    content_meta = meta.get("metadata", {}).get("contentMetadataViewModel", {})

    for row in content_meta.get("metadataRows", []):

        parts = row.get("metadataParts", [])

        texts = [p.get("text", {}).get("content", "") for p in parts]

        for t in texts:

            if "view" in t.lower():

                view_text = t

            elif any(w in t.lower() for w in ["ago", "day", "week", "month", "year", "hour"]):

                published = t

            elif not channel_name and not any(w in t.lower() for w in ["view", "ago", "subscriber"]):

                pass



    return {

        "video_id": video_id,

        "title": title,

        "thumbnail": thumbnail,

        "duration": duration,

        "duration_seconds": parse_duration(duration),

        "views": parse_number(view_text),

        "view_count_text": view_text,

        "published": published,

        "channel": {"name": channel_name, "id": channel_id},

        "description": "",

        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",

    }





def _find_key(d: dict, key: str, path: str = "") -> list[tuple[str, Any]]:

    """Recursively find all occurrences of a key in a nested dict/list."""

    results = []

    if isinstance(d, dict):

        for k, v in d.items():

            if k == key:

                results.append((path + "." + k, v))

            results.extend(_find_key(v, key, path + "." + k))

    elif isinstance(d, list):

        for i, item in enumerate(d):

            results.extend(_find_key(item, key, path + f"[{i}]"))

    return results





def extract_related_videos(next_data: dict) -> list[dict]:

    """Extract related/recommended videos from next response.



    Handles both older compactVideoRenderer and newer lockupViewModel formats.

    """

    results = []



    contents = next_data.get("contents", {})

    two_col = contents.get("twoColumnWatchNextResults", {})

    secondary = two_col.get("secondaryResults", {})

    sec_results = secondary.get("secondaryResults", {})

    items = sec_results.get("results", [])





    if not items:

        for cmd in next_data.get("onResponseReceivedCommands", []):

            if "appendContinuationItemsAction" in cmd:

                items = cmd["appendContinuationItemsAction"].get("continuationItems", [])



    for item in items:

        if "compactVideoRenderer" in item:

            cvr = item["compactVideoRenderer"]

            parsed = parse_video_renderer({

                "videoId": cvr.get("videoId", ""),

                "title": cvr.get("title", {}),

                "thumbnail": cvr.get("thumbnail", {}),

                "lengthText": cvr.get("lengthText", {}),

                "viewCountText": cvr.get("viewCountText", {}),

                "publishedTimeText": cvr.get("publishedTimeText", {}),

                "ownerText": cvr.get("shortBylineText", {}),

                "descriptionSnippet": cvr.get("descriptionSnippet", {}),

            })

            if parsed:

                results.append(parsed)

        elif "lockupViewModel" in item:

            parsed = _parse_lockup_view_model(item["lockupViewModel"])

            if parsed and parsed["video_id"]:

                results.append(parsed)

        elif "continuationItemRenderer" in item:

            pass



    return results





def extract_channel_info(browse_data: dict) -> dict:

    """Extract channel metadata from browse response."""

    header = browse_data.get("header", {})

    c2v_header = header.get("c4TabbedHeaderRenderer", {})

    page_header = header.get("pageHeaderRenderer", {})





    if c2v_header:

        return {

            "channel_id": c2v_header.get("channelId", ""),

            "title": get_text(c2v_header.get("title", {})),

            "avatar": get_thumbnail(

                c2v_header.get("avatar", {}).get("thumbnails", [])

            ),

            "subscribers": get_text(c2v_header.get("subscriberCountText", {})),

            "banner": get_thumbnail(

                c2v_header.get("banner", {}).get("thumbnails", [])

            ),

            "video_count": get_text(c2v_header.get("videosCountText", {})),

        }





    if page_header:

        content = page_header.get("content", {})

        vm = content.get("pageHeaderViewModel", {})





        title_obj = vm.get("title", {})

        title = ""

        if "dynamicTextViewModel" in title_obj:

            title = title_obj["dynamicTextViewModel"].get("text", {}).get("content", "")

        else:

            title = get_text(title_obj)





        image_obj = vm.get("image", {})

        avatar = None

        if "decoratedAvatarViewModel" in image_obj:

            avatar_sources = (

                image_obj["decoratedAvatarViewModel"]

                .get("avatar", {})

                .get("avatarViewModel", {})

                .get("image", {})

                .get("sources", [])

            )

            avatar = get_thumbnail(avatar_sources)

        elif "contentImageViewModel" in image_obj:

            avatar = get_thumbnail(

                image_obj["contentImageViewModel"].get("image", {}).get("sources", [])

            )





        metadata = vm.get("metadata", {})

        content_meta_vm = metadata.get("contentMetadataViewModel", {})

        metadata_rows = content_meta_vm.get("metadataRows", [])

        subscribers = ""

        video_count = ""

        for row in metadata_rows:

            parts = row.get("metadataParts", [])

            for part in parts:

                cell_text = part.get("text", {}).get("content", "")

                if "subscriber" in cell_text.lower():

                    subscribers = cell_text

                elif "video" in cell_text.lower():

                    video_count = cell_text





        if not subscribers and not video_count:

            old_rows = metadata.get("metadataViewModel", {}).get("metadataRows", [])

            for row in old_rows:

                cells = row.get("metadataCells", [])

                for cell in cells:

                    cell_text = get_text(cell.get("text", {}))

                    if "subscriber" in cell_text.lower():

                        subscribers = cell_text

                    elif "video" in cell_text.lower():

                        video_count = cell_text





        description = get_text(vm.get("description", {}))



        return {

            "channel_id": "",

            "title": title,

            "avatar": avatar,

            "subscribers": subscribers,

            "banner": None,

            "video_count": video_count,

            "description": description,

        }



    return {}





def extract_transcript_params(next_data: dict) -> str | None:

    """Extract the get_transcript params token from a next/watch response.



    YouTube embeds the transcript params inside the engagement panel

    ``engagement-panel-searchable-transcript`` → ``continuationItemRenderer``

    → ``continuationEndpoint`` → ``getTranscriptEndpoint`` → ``params``.

    """

    panels = _find_key(next_data, "engagementPanelSectionListRenderer")

    for _path, panel in panels:

        target_id = panel.get("targetId", "")

        if target_id != "engagement-panel-searchable-transcript":

            continue

        endpoints = _find_key(panel, "getTranscriptEndpoint")

        for _ep, ep_val in endpoints:

            params = ep_val.get("params", "")

            if params:

                return params

    return None





def parse_transcript_segments(transcript_data: dict) -> list[dict]:

    """Parse segments from a get_transcript InnerTube response.



    Response structure:

      actions[0].updateEngagementPanelAction.content.transcriptRenderer

        .content.transcriptSearchPanelRenderer.body.transcriptSegmentListRenderer

        .initialSegments[]



    Each segment has transcriptSegmentRenderer with:

      startMs (string, ms), endMs (string, ms),

      snippet.runs[].text (array), startTimeText.simpleText ("0:00")

    """

    segments = []

    initial = _find_key(transcript_data, "initialSegments")

    for _path, seg_list in initial:

        items = seg_list if isinstance(seg_list, list) else []

        for item in items:

            renderer = item.get("transcriptSegmentRenderer", {})

            if not renderer:

                continue

            start_ms = int(renderer.get("startMs", "0"))

            end_ms = int(renderer.get("endMs", "0"))

            snippet = renderer.get("snippet", {})

            runs = snippet.get("runs", [])

            text = "".join(r.get("text", "") for r in runs) if runs else ""

            start_time_text = renderer.get("startTimeText", {}).get("simpleText", "")

            segments.append({

                "text": text.strip(),

                "start": start_ms / 1000.0,

                "duration": (end_ms - start_ms) / 1000.0,

                "start_time": start_time_text,

            })

        if segments:

            break

    return segments





def extract_search_snippets(renderer: dict) -> list[str]:

    """Extract detailedMetadataSnippets from a videoRenderer.



    YouTube includes content preview snippets that show relevant text

    from the video description or content.

    """

    snippets = []

    detailed = renderer.get("detailedMetadataSnippets", [])

    for d in detailed:

        snippet_text = get_text(d.get("snippetText", {}))

        if snippet_text:

            snippets.append(snippet_text)

    return snippets





def extract_channel_videos(browse_data: dict) -> list[dict]:

    """Extract video list from a channel's videos tab.



    Handles multiple response formats:

    - richGridRenderer with richItemRenderer containing videoRenderer or lockupViewModel

    - sectionListRenderer with itemSectionRenderer containing gridVideoRenderer

    - singleColumnBrowseResultsRenderer (mobile) and twoColumnBrowseResultsRenderer (desktop)

    """

    results = []

    contents = browse_data.get("contents", {})





    for renderer_key in ("singleColumnBrowseResultsRenderer", "twoColumnBrowseResultsRenderer"):

        container = contents.get(renderer_key, {})

        tabs = container.get("tabs", [])

        if not tabs:

            continue



        for tab in tabs:

            tab_renderer = tab.get("tabRenderer", {})

            if not tab_renderer.get("selected", False):

                continue

            content = tab_renderer.get("content", {})





            if "richGridRenderer" in content:

                rich_items = content["richGridRenderer"].get("contents", [])

                for ri in rich_items:

                    if "richItemRenderer" in ri:

                        rc = ri["richItemRenderer"].get("content", {})

                        if "videoRenderer" in rc:

                            parsed = parse_video_renderer(rc["videoRenderer"])

                            if parsed:

                                results.append(parsed)

                        elif "lockupViewModel" in rc:

                            parsed = _parse_lockup_view_model(rc["lockupViewModel"])

                            if parsed and parsed["video_id"]:

                                results.append(parsed)





            section_list = content.get("sectionListRenderer", {})

            sections = section_list.get("contents", [])

            for section in sections:



                if "richItemRenderer" in section:

                    rich = section["richItemRenderer"]

                    rc = rich.get("content", {})

                    if "videoRenderer" in rc:

                        parsed = parse_video_renderer(rc["videoRenderer"])

                        if parsed:

                            results.append(parsed)

                    elif "lockupViewModel" in rc:

                        parsed = _parse_lockup_view_model(rc["lockupViewModel"])

                        if parsed and parsed["video_id"]:

                            results.append(parsed)

                elif "itemSectionRenderer" in section:

                    items = section["itemSectionRenderer"].get("contents", [])

                    for item in items:

                        if "gridVideoRenderer" in item:

                            gvr = item["gridVideoRenderer"]

                            parsed = parse_video_renderer({

                                "videoId": gvr.get("videoId", ""),

                                "title": gvr.get("title", {}),

                                "thumbnail": gvr.get("thumbnail", {}),

                                "lengthText": gvr.get("thumbnailOverlays", [{}])[0]

                                .get("thumbnailOverlayTimeStatusRenderer", {})

                                .get("text", {}),

                                "viewCountText": gvr.get("viewCountText", {}),

                                "publishedTimeText": gvr.get("publishedTimeText", {}),

                                "ownerText": gvr.get("shortBylineText", {}),

                            })

                            if parsed:

                                results.append(parsed)

                        elif "videoRenderer" in item:

                            parsed = parse_video_renderer(item["videoRenderer"])

                            if parsed:

                                results.append(parsed)

                        elif "lockupViewModel" in item:

                            parsed = _parse_lockup_view_model(item["lockupViewModel"])

                            if parsed and parsed["video_id"]:

                                results.append(parsed)

                        elif "shelfRenderer" in item:



                            shelf = item["shelfRenderer"]

                            hlist = shelf.get("content", {}).get("horizontalListRenderer", {}).get("items", [])

                            for hitem in hlist:

                                if "lockupViewModel" in hitem:

                                    parsed = _parse_lockup_view_model(hitem["lockupViewModel"])

                                    if parsed and parsed["video_id"]:

                                        results.append(parsed)

                                elif "gridVideoRenderer" in hitem:

                                    gvr = hitem["gridVideoRenderer"]

                                    parsed = parse_video_renderer({

                                        "videoId": gvr.get("videoId", ""),

                                        "title": gvr.get("title", {}),

                                        "thumbnail": gvr.get("thumbnail", {}),

                                        "lengthText": gvr.get("thumbnailOverlays", [{}])[0]

                                        .get("thumbnailOverlayTimeStatusRenderer", {})

                                        .get("text", {}),

                                        "viewCountText": gvr.get("viewCountText", {}),

                                        "publishedTimeText": gvr.get("publishedTimeText", {}),

                                        "ownerText": gvr.get("shortBylineText", {}),

                                    })

                                    if parsed:

                                        results.append(parsed)



    return results
