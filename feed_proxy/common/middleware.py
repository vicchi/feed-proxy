"""
Feed Proxy API: common package; middleware module
"""

import logging
import re
import time
from typing import List, Optional

from fastapi import FastAPI
from starlette.datastructures import MutableHeaders, URL
from starlette.types import Message, Receive, Scope, Send

# CODE HEALTH WARNING:
#
# This module uses "pure" ASGI Starlette middleware and not FastAPI middleware.
# See https://www.starlette.io/middleware/#pure-asgi-middleware and
# https://fastapi.tiangolo.com/advanced/middleware/
#
# This is due to a known bug/limitation in Starlette's BaseHTTPMiddleware which is very unlikely
# to be fixed.
#
# See https://www.starlette.io/middleware/#limitations and also
# https://github.com/encode/starlette/pull/1441 and https://github.com/encode/starlette/issues/1438
#
# tl;dr - It's not possible to use BackgroundTasks with BaseHTTPMiddleware.
#
# This means the addition of any middleware based on BaseHTTPMiddleware will mean that where there
# are multiple Depends() dependencies injected, only the last dependency will be garbage collected,
# which will mean memory leaks and/or database connections not being closed/cleaned up. What's
# *not* made clear in the documentation, apart from an aside, is that BackgroundTasks are created
# to handle each dependency's cleanup and thus garbage collection behind the scenes. Sigh.

logger = logging.getLogger('gunicorn.error')


class RouteLoggerMiddleware:    # pylint: disable=too-few-public-methods
    """
    ASGI middleware to log all API routes accessed
    """
    def __init__(
        self,
        app: FastAPI,
        *,
        route_logger: Optional[logging.Logger] = None,
        level: Optional[int] = None,
        skip_routes: Optional[List[str]] = None,
        skip_regexes: Optional[List[str]] = None
    ) -> None:
        self._app = app
        self._logger = route_logger if route_logger else logging.getLogger('gunicorn.error')
        self._level = level if level else logging.DEBUG
        self._skip_routes = skip_routes if skip_routes else []
        self._skip_regexes = (
            list(map(lambda regex: re.compile(regex),   # pylint: disable=unnecessary-lambda
                     skip_regexes)) if skip_regexes else []
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        if scope['type'] not in ('http', 'websocket'):
            await self._app(scope, receive, send)

        url = URL(scope=scope)
        client_ip, _client_port = scope['client']
        status = 500
        start_time = time.perf_counter()
        query_params = f'?{url.query}' if url.query else ''

        async def receive_wrapper() -> Message:
            message = await receive()
            return message

        async def send_wrapper(message: Message) -> None:
            # Code Health Warning
            # Note the use of nonlocal below so send_wrapper inherits the status and
            # start_time variables from the containing scope of __call__
            nonlocal status
            nonlocal start_time
            if message['type'] == 'http.response.start':
                status = message['status']

            await send(message)

            if message['type'] == 'http.response.body':
                if not self._skip_this_route(url):
                    elapsed = time.perf_counter() - start_time
                    logger.info(
                        '%s - %s %s%s, %s, took=%s',
                        client_ip,
                        scope['method'],
                        url.path,
                        query_params,
                        status,
                        f'{elapsed:0.4f}s'
                    )

        await self._app(scope, receive_wrapper, send_wrapper)

    def _skip_this_route(self, url: URL) -> bool:
        return any(
            [True for path in self._skip_routes if url.path.startswith(path)] +    # noqa: W504
            [True for regex in self._skip_regexes if regex.match(url.path)]
        )


class TransactionTimeMiddleware:    # pylint: disable=too-few-public-methods
    """
    ASGI middleware to report elapsed request response time as the X-Transaction-Time header
    """
    def __init__(self, app: FastAPI) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            return await self._app(scope, receive, send)

        async def send_wrapper(message: Message) -> None:
            if message['type'] == 'http.response.start':
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                headers = MutableHeaders(scope=message)
                headers.append('X-Transaction-Time', f'{elapsed:0.4f}s')

            await send(message)

        start_time = time.perf_counter()
        await self._app(scope, receive, send_wrapper)
