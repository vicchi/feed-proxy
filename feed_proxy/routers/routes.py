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

logger = logging.getLogger('gunicorn.error')

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

    logger.info('pinging listenbrainz')
    url = f'{settings.listenbrainz_api_url}/user/{settings.listenbrainz_api_user}/listens'
    rsp = session.get(url=url, headers=headers, params=params, timeout=10)
    logger.info('listenbrainz said %s', rsp.status_code)
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
            logger.info('pinging covertart')
            url = f'{settings.coverart_api_url}/release/{caa_mbid}'
            rsp = session.get(url=url, headers=headers, timeout=10)
            logger.info('covertart said %s', rsp.status_code)
            if rsp.status_code == HTTPStatus.OK:
                body = rsp.json()
                for img in body['images']:
                    logger.info(img)
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
