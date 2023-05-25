"""
Feed Proxy API: dependencies package; cache module
"""

from dataclasses import dataclass
import datetime

import humanfriendly
from requests.adapters import HTTPAdapter
from requests_cache import CachedSession, SQLiteCache
from urllib3.util.retry import Retry

from feed_proxy.common.settings import get_settings
from feed_proxy.common.version import user_agent


@dataclass
class SessionCaches:
    """
    Categorised remote API session caches
    """

    listens: CachedSession = None
    stats: CachedSession = None
    images: CachedSession = None
    artists: CachedSession = None


TIMEOUT = 10
RETRIES = 5
BACKOFF = 0.1
STATUSES = [500, 502, 503, 504]

DEFAULT_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': user_agent()
}

settings = get_settings()
retries = Retry(total=RETRIES, backoff_factor=BACKOFF, status_forcelist=STATUSES)
caches = SessionCaches()

caches.listens = CachedSession(
    settings.cache_listens,
    backend=SQLiteCache(db_path=settings.cache_listens.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_listens_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
caches.listens.mount('https://', HTTPAdapter(max_retries=retries))

caches.stats = CachedSession(
    settings.cache_stats,
    backend=SQLiteCache(db_path=settings.cache_stats.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(seconds=humanfriendly.parse_timespan(settings.cache_stats_expiry))
    },
    headers=DEFAULT_HEADERS
)
caches.stats.mount('https://', HTTPAdapter(max_retries=retries))

caches.images = CachedSession(
    settings.cache_images,
    backend=SQLiteCache(db_path=settings.cache_images.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(seconds=humanfriendly.parse_timespan(settings.cache_images_expiry))
    },
    headers=DEFAULT_HEADERS
)
caches.images.mount('https://', HTTPAdapter(max_retries=retries))

caches.artists = CachedSession(
    settings.cache_artists,
    backend=SQLiteCache(db_path=settings.cache_artists.absolute()),
    urls_expire_after={
        '*': datetime.timedelta(
            seconds=humanfriendly.parse_timespan(settings.cache_artists_expiry)
        )
    },
    headers=DEFAULT_HEADERS
)
caches.artists.mount('https://', HTTPAdapter(max_retries=retries))


def sessions() -> SessionCaches:
    """
    Get and return the cached sessions
    """

    return caches
