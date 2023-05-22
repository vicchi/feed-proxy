"""
Feed Proxy API: core package; main server module
"""

from http import HTTPStatus
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from feed_proxy.common.settings import get_settings
from feed_proxy.routers.routes import router

logger = logging.getLogger('gunicorn.error')

settings = get_settings()
api = FastAPI(debug=True, title='feeds.vicchi.org Feed Proxy API')
api.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET'], allow_headers=['*'])
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
