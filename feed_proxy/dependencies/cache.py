"""
Feed Proxy API: dependencies package; cache module
"""

import base64
from dataclasses import dataclass
import datetime
from functools import lru_cache
import hashlib
import hmac

import humanfriendly
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession, SQLiteCache
from starlette.datastructures import URL
from urllib3.util.retry import Retry

from feed_proxy.common.settings import get_settings
from feed_proxy.common.version import user_agent


@dataclass
class SessionCaches:
    """
    Categorised remote API session caches
    """

    listens: CachedSession
    stats: CachedSession
    images: CachedSession
    artists: CachedSession
    weather: CachedSession
    checkins: CachedSession


STATUSES = [500, 502, 503, 504]

DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': user_agent()
}

settings = get_settings()
retries = Retry(
    total=settings.api_retries,
    backoff_factor=settings.api_backoff,
    status_forcelist=STATUSES
)
listens = CachedSession(
    settings.cache_listens.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_listens.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_listens_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
listens.mount('https://', HTTPAdapter(max_retries=retries))

stats = CachedSession(
    settings.cache_stats.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_stats.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(seconds=humanfriendly.parse_timespan(settings.cache_stats_expiry))
    },
    headers=DEFAULT_HEADERS
)
stats.mount('https://', HTTPAdapter(max_retries=retries))

images = CachedSession(
    settings.cache_images.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_images.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(seconds=humanfriendly.parse_timespan(settings.cache_images_expiry))
    },
    headers=DEFAULT_HEADERS
)
images.mount('https://', HTTPAdapter(max_retries=retries))

artists = CachedSession(
    settings.cache_artists.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_artists.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_artists_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
artists.mount('https://', HTTPAdapter(max_retries=retries))

weather = CachedSession(
    settings.cache_weather.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_weather.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_weather_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
weather.mount('https://', HTTPAdapter(max_retries=retries))

checkins = CachedSession(
    settings.cache_checkins.as_posix(),
    backend=SQLiteCache(db_path=settings.cache_checkins.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_checkins_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
checkins.mount('https://', HTTPAdapter(max_retries=retries))

caches = SessionCaches(listens, stats, images, artists, weather, checkins)


@lru_cache
def sessions() -> SessionCaches:
    """
    Get and return the cached sessions
    """

    return caches


def signed_cdn_url(url: URL) -> URL:
    """
    Format and sign an image CDN URL
    """

    key = bytes(settings.cdn_secret, 'ascii')
    path = f'{settings.cdn_image_height}x{settings.cdn_image_width}/{str(url)}'
    raw = bytes(bytes(path, 'ascii'))
    hashed = hmac.new(key, raw, hashlib.sha256)
    signature = base64.b64encode(hashed.digest()).decode()
    signed_path = f"{signature[:settings.cdn_hash_size].replace('+', '-').replace('/', '_')}/{path}"
    return URL(f'{settings.cdn_base_url}/{signed_path}')
