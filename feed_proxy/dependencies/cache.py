"""
Feed Proxy API: dependencies package; cache module
"""

import datetime

from requests.adapters import HTTPAdapter
from requests_cache import CachedSession
from urllib3.util.retry import Retry

from feed_proxy.common.settings import get_settings

RETRIES = 5
BACKOFF = 0.1
STATUSES = [500, 502, 503, 504]

settings = get_settings()
cached_session = CachedSession(
    settings.cache_path,
    backend='filesystem',
    urls_expire_after={'*': datetime.timedelta(minutes=settings.cache_expiration)}
)
retries = Retry(total=RETRIES, backoff_factor=BACKOFF, status_forcelist=STATUSES)
cached_session.mount('https://', HTTPAdapter(max_retries=retries))


def session() -> CachedSession:
    """
    Get and return a cached session object
    """

    return cached_session
