"""
Feed Proxy API: core package; main server module
"""

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from feed_proxy.common.settings import get_settings
from feed_proxy.routers.routes import router

logger = logging.getLogger('gunicorn.error')

settings = get_settings()
api = FastAPI(debug=True, title='feeds.vicchi.org Feed Proxy API')
api.include_router(router)
api.mount('/static', StaticFiles(directory=settings.static_path), name='static')
