"""
Feed Proxy API: core package; main server module
"""

from contextlib import asynccontextmanager
from http import HTTPStatus
# from http.client import HTTPConnection
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from feed_proxy.common.middleware import RouteLoggerMiddleware, TransactionTimeMiddleware
from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import sessions
from feed_proxy.methods.music import current_music
from feed_proxy.routers.routes import router

# HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

logger = logging.getLogger('gunicorn.error')


@asynccontextmanager
async def lifespan_handler(_app: FastAPI) -> None:
    """
    FastAPI lifespan startup/shutdown handler
    """

    logger.info('lifespan: starting up')
    preload = settings.preload_cache
    if preload:
        logger.info('lifespan: pre-loading music cache')
        current_music(request=None, count=8, sessions=sessions(), preload=preload)
    logger.info('lifespan: initialised ...')
    yield
    logger.info('lifespan: shutting down')


settings = get_settings()
debug = settings.environment.lower() != 'production'
api = FastAPI(debug=debug, lifespan=lifespan_handler, title='status.vicchi.org Feed Proxy API')

api.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET'], allow_headers=['*'])
api.add_middleware(TransactionTimeMiddleware)
api.add_middleware(RouteLoggerMiddleware, level=logging.INFO, skip_regexes=['.*/ping'])
api.add_middleware(ProxyHeadersMiddleware, trusted_hosts='*')

api.include_router(router)
api.mount('/static', StaticFiles(directory=settings.static_path), name='static')


@api.get('/ping')
async def ping() -> JSONResponse:
    """
    Health check ping
    """

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={
            'code': HTTPStatus.OK,
            'message': 'OK'
        }
    )
