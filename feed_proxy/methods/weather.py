"""
Feed Proxy API: methods package; weather module
"""

from http import HTTPStatus
import logging

from fastapi import Request
from fastapi.exceptions import HTTPException

from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import SessionCaches
from feed_proxy.models.responses import CurrentWeather

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


def current_weather(
    request: Request,
    lng: float,
    lat: float,
    sessions: SessionCaches
) -> CurrentWeather:
    """
    Get current weather from OpenMeteo
    """

    settings = get_settings()

    params = {
        'latitude': lat,
        'longitude': lng,
        'current_weather': True
    }

    url = f'{settings.openmeteo_api_url}/forecast'
    rsp = sessions.weather.get(url=url, params=params, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code != HTTPStatus.OK:
        details = rsp.json() if rsp.text else {}
        raise HTTPException(status_code=rsp.status_code, detail=details)

    body = rsp.json()
    day_night = 'day' if body['current_weather']['is_day'] else 'night'
    code = body['current_weather']['weathercode']
    icon = WEATHER_CODES[code]['icon'].format(day_night=day_night)

    weather = CurrentWeather(
        temp=body['current_weather']['temperature'],
        icon=str(request.url_for('static',
                                 path=f'/weather-icons/fill/svg/{icon}.svg')),
        descr=WEATHER_CODES[code]['descr']
    )
    return weather
