"""

Client configuration constants for YouTube InnerTube API.

"""

from __future__ import annotations

import base64

_WEB_KEY_B64 = "QUl6YVN5QU9fRkoyU2xxVThRNFNURUhMR0NpbHdfWTlfMTFxY1c4"
_ANDROID_KEY_B64 = "QUl6YVN5QThlaVptTTFGYURWalJ5LWRmMktUeVFfdnpfeVlNMzl3"
_IOS_KEY_B64 = "QUl6YVN5Qi02M3ZQcmRUaGhLdWVyYkIyTl9sN0t3d2N4ajZ5VUFj"

WEB_API_KEY = base64.b64decode(_WEB_KEY_B64).decode()
ANDROID_API_KEY = base64.b64decode(_ANDROID_KEY_B64).decode()
IOS_API_KEY = base64.b64decode(_IOS_KEY_B64).decode()


BASE_URL = "https://www.youtube.com/youtubei/v1"

API_BASE = "https://youtubei.googleapis.com/youtubei/v1"














CLIENTS = {

    "WEB": {

        "clientName": "WEB",

        "clientVersion": "2.20260623.01.00",

        "apiKey": WEB_API_KEY,

        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",

        "referer": "https://www.youtube.com/",

    },

    "ANDROID": {

        "clientName": "ANDROID",

        "clientVersion": "21.03.36",

        "apiKey": ANDROID_API_KEY,

        "userAgent": "com.google.android.youtube/21.03.36 (Linux; U; Android 16; en_US; SM-S908E Build/TP1A.220624.014) gzip",

        "androidSdkVersion": 36,

    },

    "IOS": {

        "clientName": "iOS",

        "clientVersion": "20.11.6",

        "apiKey": IOS_API_KEY,

        "userAgent": "com.google.ios.youtube/20.11.6 (iPhone10,4; U; CPU iOS 16_7_7 like Mac OS X)",

        "deviceModel": "iPhone10,4",

    },

    "MWEB": {

        "clientName": "MWEB",

        "clientVersion": "2.20260205.04.01",

        "apiKey": WEB_API_KEY,

        "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",

        "referer": "https://m.youtube.com/",

    },

    "TV_EMBEDDED": {

        "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",

        "clientVersion": "2.0",

        "apiKey": WEB_API_KEY,

        "userAgent": "Mozilla/5.0 (PlayStation 4 5.55) AppleWebKit/601.2 (KHTML, like Gecko)",

    },

    "WEB_EMBEDDED": {

        "clientName": "WEB_EMBEDDED_PLAYER",

        "clientVersion": "1.20260206.01.00",

        "apiKey": WEB_API_KEY,

        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",

        "referer": "https://www.youtube.com/",

    },

}





ENDPOINTS = {

    "search": f"{BASE_URL}/search",

    "player": f"{BASE_URL}/player",

    "next": f"{BASE_URL}/next",

    "browse": f"{BASE_URL}/browse",

    "get_transcript": f"{BASE_URL}/get_transcript",

    "guide": f"{BASE_URL}/guide",

    "get_watch": f"{BASE_URL}/get_watch",

}





DEFAULT_CLIENT = "ANDROID"



SEARCH_CLIENT = "WEB"



PLAYER_CLIENT = "IOS"





SEARCH_FILTERS = {

    "video": "EgIQAQ%3D%3D",

    "channel": "EgIQAg%3D%3D",

    "playlist": "EgIQAw%3D%3D",

    "movie": "EgIQBA%3D%3D",

}





DEFAULT_HEADERS = {

    "Accept": "*/*",

    "Accept-Encoding": "gzip, deflate",

    "Content-Type": "application/json",

    "X-Goog-Api-Format-Version": "1",

    "Origin": "https://www.youtube.com",

}





STREAM_HEADERS = {

    "Accept": "*/*",

    "Origin": "https://www.youtube.com",

    "Referer": "https://www.youtube.com",

}





ITAG_QUALITY = {



    5: ("240p", "flv", "video+audio"),

    17: ("144p", "3gp", "video+audio"),

    18: ("360p", "mp4", "video+audio"),

    22: ("720p", "mp4", "video+audio"),

    36: ("240p", "3gp", "video+audio"),

    43: ("360p", "webm", "video+audio"),



    133: ("240p", "mp4", "video"),

    134: ("360p", "mp4", "video"),

    135: ("480p", "mp4", "video"),

    136: ("720p", "mp4", "video"),

    137: ("1080p", "mp4", "video"),

    140: ("128k", "m4a", "audio"),

    160: ("144p", "mp4", "video"),

    167: ("360p", "webm", "video"),

    168: ("480p", "webm", "video"),

    169: ("1080p", "webm", "video"),

    242: ("240p", "webm", "video"),

    243: ("360p", "webm", "video"),

    244: ("480p", "webm", "video"),

    247: ("720p", "webm", "video"),

    248: ("1080p", "webm", "video"),

    249: ("50k", "webm", "audio"),

    250: ("70k", "webm", "audio"),

    251: ("160k", "webm", "audio"),

    271: ("1440p", "webm", "video"),

    278: ("144p", "webm", "video"),

    298: ("720p60", "mp4", "video"),

    299: ("1080p60", "mp4", "video"),

    302: ("720p60", "webm", "video"),

    303: ("1080p60", "webm", "video"),

    308: ("1440p60", "webm", "video"),

    313: ("2160p", "webm", "video"),

    315: ("720p60", "webm", "video"),

    332: ("2160p60", "webm", "video"),

    333: ("2160p60", "mp4", "video"),

    394: ("144p", "mp4", "video"),

    395: ("240p", "mp4", "video"),

    396: ("360p", "mp4", "video"),

    397: ("480p", "mp4", "video"),

    398: ("720p", "mp4", "video"),

    399: ("1080p", "mp4", "video"),

    400: ("1440p", "mp4", "video"),

    401: ("2160p", "mp4", "video"),

    402: ("48k", "m4a", "audio"),

    403: ("128k", "m4a", "audio"),

    404: ("256k", "m4a", "audio"),

}
