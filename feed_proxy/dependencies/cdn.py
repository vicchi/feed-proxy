"""
Feed Proxy API: dependencies package; CDN-ish module
"""

import logging
from pathlib import Path
from typing import Generator, Optional

from fastapi.requests import Request
from starlette.datastructures import URL

from feed_proxy.common.settings import get_settings

logger = logging.getLogger('gunicorn.error')


class CdnIsh:
    """
    Locally hosted not-really-a-CDN
    """
    def __init__(self, rootdir: Path):
        self._root: Path = rootdir.absolute()

    def get(self, prefix: Path, key: str, request: Request) -> Optional[URL]:
        """
        Get a keyed entry from the CDN as a URL
        """

        candidate_path = self._root / prefix
        candidate_glob = f'{key}.*'
        candidates = list(candidate_path.glob(candidate_glob))
        if candidates:
            url = Path(prefix) / candidates[0].name
            logger.debug('get: url: %s', url)
            return request.url_for('cdn', path=url)

        return None

    def put(self, prefix: Path, key: URL) -> None:
        """
        Put (download) an entry derived from a URL into the CDN
        """


def get_cdn() -> Generator[CdnIsh, None, None]:
    """
    Inject a CdnIsh instance as a dependency
    """

    settings = get_settings()
    cdn = CdnIsh(rootdir=settings.cdn_path)
    yield cdn
