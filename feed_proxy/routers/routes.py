"""
Feed Proxy API: routers package; route handlers module
"""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import SessionCaches, sessions as caches
from feed_proxy.methods.checkins import current_checkin
from feed_proxy.methods.music import current_music
from feed_proxy.methods.weather import current_weather
from feed_proxy.models.responses import CurrentMusic, CurrentWeather

STATUSLOG_JSON = 'statuslog.json'

logger = logging.getLogger('gunicorn.error')

settings = get_settings()
router = APIRouter(prefix=f'/{settings.feed_api_version}')


@router.get('/checkin')
async def checkin_handler(
    request: Request,
    sessions: SessionCaches = Depends(caches)
) -> JSONResponse:
    """
    Get the current checkin from Swarm/Foursquare
    """

    return current_checkin(request, sessions)


@router.get('/listening')
async def listening_handler(
    request: Request,
    count: int = Query(default=8),
    sessions: SessionCaches = Depends(caches)
) -> CurrentMusic:
    """
    Get current music listens (AKA scrobbles) and stats from ListenBrainz
    """

    return current_music(request=request, count=count, sessions=sessions)


@router.get('/weather')
async def weather_handler(
    request: Request,
    lng: float = Query(default=None,
                       ge=-180.0,
                       le=180.0),
    lat: float = Query(default=None,
                       ge=-90.0,
                       le=90.0),
    sessions: SessionCaches = Depends(caches)
) -> CurrentWeather:
    """
    Get current weather from OpenMeteo
    """

    if not lng:
        lng = settings.default_lng
    if not lat:
        lat = settings.default_lat

    return current_weather(request=request, lng=lng, lat=lat, sessions=sessions)
