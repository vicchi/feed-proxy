"""
Feed Proxy API: routers package; route handlers module
"""

from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import URL

from requests_cache import CachedSession

from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import session as cache

STATUSLOG_JSON = 'statuslog.json'

logger = logging.getLogger('gunicorn.error')

WEATHER_CODES = {
    0: {
        'icon': 'clear-{day_night}',
        'descr': 'clear sky'
    },
    1: {
        'icon': 'partly-cloudy-{day_night}-haze',
        'descr': 'mainly clear'
    },
    2: {
        'icon': 'partly-cloudy-{day_night}',
        'descr': 'partly cloudy'
    },
    3: {
        'icon': 'overcast-{day_night}',
        'descr': 'overcast'
    },
    45: {
        'icon': 'fog-{day_night}',
        'descr': 'fog'
    },
    48: {
        'icon': 'extreme-{day_night}-fog',
        'descr': 'depositing rime fog'
    },
    51: {
        'icon': 'partly-cloudy-{day_night}-drizzle',
        'descr': 'light drizzle'
    },
    53: {
        'icon': 'overcast-{day_night}-drizzle',
        'descr': 'moderate drizzle'
    },
    55: {
        'icon': 'extreme-{day_night}-drizzle',
        'descr': 'dense drizzle'
    },
    56: {
        'icon': 'partly-cloudy-{day_night}-sleet',
        'descr': 'light sleet'
    },
    57: {
        'icon': 'extreme-{day_night}-sleet',
        'descr': 'dense sleet'
    },
    61: {
        'icon': 'partly-cloudy-{day_night}-rain',
        'descr': 'slight rain'
    },
    63: {
        'icon': 'overcast-{day_night}-rain',
        'descr': 'moderate rain'
    },
    65: {
        'icon': 'extreme-{day_night}-rain',
        'descr': 'heavy rain'
    },
    66: {
        'icon': 'partly-cloudy-{day_night}-sleet',
        'descr': 'light freezing rain'
    },
    67: {
        'icon': 'extreme-{day_night}-sleet',
        'descr': 'heavy freezing rain'
    },
    71: {
        'icon': 'partly-cloudy-{day_night}-snow',
        'descr': 'slight snow'
    },
    73: {
        'icon': 'overcast-{day_night}-snow',
        'descr': 'moderate snow'
    },
    75: {
        'icon': 'extreme-{day_night}-snow',
        'descr': 'heavy snow'
    },
    77: {
        'icon': 'snowflake',
        'descr': 'snow'
    },
    80: {
        'icon': 'partly-cloudy-{day_night}-rain',
        'descr': 'slight showers'
    },
    81: {
        'icon': 'overcast-{day_night}-rain',
        'descr': 'moderate showers'
    },
    82: {
        'icon': 'extreme-{day_night}-rain',
        'descr': 'violent showers'
    },
    85: {
        'icon': 'overcast-{day_night}-snow',
        'descr': 'slight snow showers'
    },
    86: {
        'icon': 'extreme-{day_night}-snow',
        'descr': 'heavy show showers'
    },
    95: {
        'icon': 'thunderstorms-{day_night}',
        'descr': 'slight or moderate thunderstorms'
    },
    96: {
        'icon': 'thunderstorms-{day_night}-snow',
        'descr': 'thunderstorm and slight hail'
    },
    99: {
        'icon': 'thunderstorms-{day_night}-extreme-snow',
        'descr': 'thunderstorm and heavy hail'
    }
}

settings = get_settings()
router = APIRouter(prefix=f'/{settings.feed_api_version}')


@router.get('/listens')
async def listens_handler(
    request: Request,
    count: int = Query(default=8),
    session: CachedSession = Depends(cache)
) -> JSONResponse:
    """
    Get current music listens (AKA scrobbles) from ListenBrainz
    """

    headers = {
        'Token': settings.listenbrainz_api_token,
        'Accept': 'application/json'
    }
    params = {
        'count': count
    }

    url = f'{settings.listenbrainz_api_url}/user/{settings.listenbrainz_api_user}/listens'
    rsp = session.get(url=url, headers=headers, params=params, timeout=10)
    if rsp.status_code != HTTPStatus.OK:
        return JSONResponse(
            status_code=rsp.status_code,
            content={
                'code': rsp.status_code,
                'details': rsp.json()
            }
        )

    body = rsp.json()

    content = {
        'count': body['payload']['count'],
        'listens': []
    }

    headers.pop('Token', None)
    for entry in body['payload']['listens']:
        meta = entry['track_metadata']

        artwork = None

        if 'mbid_mapping' in meta and 'caa_release_mbid' in meta['mbid_mapping']:
            caa_mbid = meta['mbid_mapping']['caa_release_mbid']
            url = f'{settings.coverart_api_url}/release/{caa_mbid}'
            rsp = session.get(url=url, headers=headers, timeout=10)
            if rsp.status_code == HTTPStatus.OK:
                body = rsp.json()
                for img in body['images']:
                    if img['front']:
                        url = URL(img['thumbnails']['small']).replace(scheme='https')
                        artwork = str(url)
                        break

        if not artwork:
            artwork = str(request.url_for('static', path='/heroicons/24/solid/musical-note.svg'))

        content['listens'].append(
            {
                'artist': meta['artist_name'],
                'track': meta['track_name'],
                'artwork': artwork
            }
        )

    return JSONResponse(status_code=rsp.status_code, content=content)


@router.get('/weather')
async def weather_handler(
    request: Request,
    lng: float = Query(default=None,
                       ge=-180.0,
                       le=180.0),
    lat: float = Query(default=None,
                       ge=-90.0,
                       le=90.0),
    session: CachedSession = Depends(cache)
) -> JSONResponse:
    """
    Get current weather from OpenMeteo
    """

    if not lng:
        lng = settings.default_lng
    if not lat:
        lat = settings.default_lat

    headers = {
        'Token': settings.listenbrainz_api_token,
        'Accept': 'application/json'
    }
    params = {
        'latitude': lat,
        'longitude': lng,
        'current_weather': True
    }

    url = f'{settings.openmeteo_api_url}/forecast'
    rsp = session.get(url=url, headers=headers, params=params, timeout=10)
    if rsp.status_code != HTTPStatus.OK:
        return JSONResponse(
            status_code=rsp.status_code,
            content={
                'code': rsp.status_code,
                'details': rsp.json()
            }
        )

    body = rsp.json()
    day_night = 'day' if body['current_weather']['is_day'] else 'night'
    code = body['current_weather']['weathercode']
    icon = WEATHER_CODES[code]['icon'].format(day_night=day_night)

    content = {
        'temp': body['current_weather']['temperature'],
        'icon': str(request.url_for('static',
                                    path=f'/weather-icons/fill/svg/{icon}.svg')),
        'descr': WEATHER_CODES[code]['descr']
    }

    return JSONResponse(status_code=200, content=content)
