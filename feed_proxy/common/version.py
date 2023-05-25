"""
Feed Proxy API: common package; VERSION file module
"""

import os
import sys
from functools import lru_cache

from feed_proxy.common.settings import get_settings

DEFAULT_VERSION_FILE = 'VERSION'


def _walk_to_root(path):
    if not os.path.exists(path):
        raise IOError(f'Start path ({path}) not found')

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir


@lru_cache
def find_version(filename=DEFAULT_VERSION_FILE, raise_on_not_found=False, use_cwd=False):
    """
    Find a VERSION file in the current project hierarchy
    """
    def _is_interactive():
        main = __import__('__main__', None, None, fromlist=['__file__'])
        return not hasattr(main, '__file__')

    if use_cwd or _is_interactive() or getattr(sys, 'frozen', False):
        path = os.getcwd()
    else:
        frame = sys._getframe()    # pylint: disable=protected-access
        current_file = __file__

        while frame.f_code.co_filename == current_file:
            assert frame.f_back is not None
            frame = frame.f_back
        frame_filename = frame.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if os.path.isfile(check_path):
            return check_path

    if raise_on_not_found:
        raise IOError(f'File not found ({filename})')

    return None


@lru_cache
def get_version(filename):
    """
    Get the stripped contents of a VERSION file
    """

    return open(filename, encoding='UTF-8').read().strip()


@lru_cache
def user_agent() -> str:
    """
    Build a versioned user-agent string
    """

    settings = get_settings()

    return f'FeedProxyAPI/{get_version(find_version())} +{settings.site_url} ({settings.site_contact})'
