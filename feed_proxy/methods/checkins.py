"""
Feed Proxy API: methods package; checkins module
"""

import datetime
from http import HTTPStatus
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import SessionCaches
from feed_proxy.methods.weather import current_weather

logger = logging.getLogger('gunicorn.error')


def current_checkin(request: Request, sessions: SessionCaches) -> JSONResponse:
    """
    Get the current checkin from Swarm/Foursquare
    """

    settings = get_settings()

    params = {
        'user_id': 'self',
        'v': '20230501',
        'oauth_token': settings.foursq_oauth_token,
        'limit': 1
    }

    url = f'{settings.foursq_api_url}/v2/users/self/checkins'
    rsp = sessions.weather.get(url=url, params=params, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code != HTTPStatus.OK:
        details = rsp.json() if rsp.text else {}
        return JSONResponse(
            status_code=rsp.status_code,
            content={
                'code': rsp.status_code,
                'details': details
            }
        )

    body = rsp.json()
    item = body['response']['checkins']['items'][0]
    venue = item['venue']

    icon = venue['categories'][0]['icon']
    size = '32'
    icon_url = f"{icon['prefix']}{size}{icon['suffix']}"
    location = venue['location']
    location.pop('labeledLatLngs')
    location.pop('formattedAddress')
    checkin = {
        'timestamp': str(datetime.datetime.fromtimestamp(item['createdAt'])),
        'name': venue['name'],
        'location': location,
        'icon': icon_url
    }

    coords = venue['location']
    weather = current_weather(
        request=request,
        lng=coords['lng'],
        lat=coords['lat'],
        sessions=sessions
    )
    return JSONResponse(
        status_code=HTTPStatus.OK.value,
        content={
            'checkin': checkin,
            'weather': weather.dict()
        }
    )
