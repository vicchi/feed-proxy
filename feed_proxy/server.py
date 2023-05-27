"""
Feed Proxy API: core package; main server module
"""

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
from feed_proxy.routers.routes import router

# HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

logger = logging.getLogger('gunicorn.error')

settings = get_settings()
debug = settings.environment.lower() != 'production'
api = FastAPI(debug=debug, title='status.vicchi.org Feed Proxy API')

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
