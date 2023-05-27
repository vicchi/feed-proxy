"""
Feed Proxy API: methods package; music module
"""

from http import HTTPStatus
import logging
import os

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.datastructures import URL

from feed_proxy.common.settings import get_settings
from feed_proxy.dependencies.cache import SessionCaches, signed_cdn_url

logger = logging.getLogger('gunicorn.error')


def current_music(
    request: Request,
    count: int,
    sessions: SessionCaches,
    preload: bool = False
) -> JSONResponse:
    """
    Get current music listening from ListenBrainz/MusicBrainz/Discogs
    """

    settings = get_settings()
    listening = {
        'tracks': [],
        'artists': [],
        'releases': []
    }

    listens = listenbrainz_listens(sessions, count)
    if 'payload' in listens and 'listens' in listens['payload']:
        for track in listens['payload']['listens']:
            if 'track_metadata' in track:
                meta = track['track_metadata']
                image_url = None
                track_url = None
                if 'mbid_mapping' in meta:
                    if 'caa_release_mbid' in meta['mbid_mapping']:
                        caa_mbid = meta['mbid_mapping']['caa_release_mbid']
                        image_url = coverart_image(
                            mbid=caa_mbid,
                            request=request,
                            sessions=sessions,
                            preload=preload
                        )
                    if 'release_mbid' in meta['mbid_mapping']:
                        track_url = f"{settings.musicbrainz_url}/release/{meta['mbid_mapping']['release_mbid']}"

                if image_url:
                    image = str(image_url)
                else:
                    if preload:
                        image = None
                    else:
                        image = str(
                            request.url_for('static',
                                            path='/heroicons/24/solid/musical-note.svg')
                        )

                listening['tracks'].append(
                    {
                        'artist': meta['artist_name'],
                        'track': meta['track_name'],
                        'url': track_url,
                        'image': image
                    }
                )

    artists = listenbrainz_artist_stats(sessions, count)
    if 'payload' in artists and 'artists' in artists['payload']:
        for artist in artists['payload']['artists']:
            image_url = None
            artist_meta = {}
            discogs_id = None
            if 'artist_mbid' in artist and artist['artist_mbid']:
                artist_meta = musicbrainz_artist(mbid=artist['artist_mbid'], sessions=sessions)
                if artist_meta and 'relations' in artist_meta:
                    for rel in artist_meta['relations']:
                        if rel['type'] == 'discogs':
                            resource = URL(rel['url']['resource'])
                            discogs_id = os.path.split(resource.path)[1]
                            image_url = discogs_artist_image(
                                discogsid=discogs_id,
                                request=request,
                                sessions=sessions
                            )
                            break

            if image_url:
                image = str(image_url)
            else:
                image = str(request.url_for('static', path='/heroicons/24/solid/musical-note.svg'))

            listening['artists'].append(
                {
                    'name': artist['artist_name'],
                    'count': artist['listen_count'],
                    'image': image,
                    'url': f"{settings.musicbrainz_url}/artist/{artist['artist_mbid']}"
                }
            )

    releases = listenbrainz_release_stats(sessions, count)
    if 'payload' in releases and 'release_groups' in releases['payload']:
        for release in releases['payload']['release_groups']:
            if 'release_group_mbid' in release and release['release_group_mbid']:
                caa_mbid = release['release_group_mbid']
                image_url = coverart_image(
                    mbid=caa_mbid,
                    request=request,
                    sessions=sessions,
                    metadata='release-group',
                    preload=preload
                )

                if image_url:
                    image = str(image_url)
                else:
                    if preload:
                        image = None
                    else:
                        image = str(
                            request.url_for('static',
                                            path='/heroicons/24/solid/musical-note.svg')
                        )

                listening['releases'].append(
                    {
                        'artist': release['artist_name'],
                        'release': release['release_group_name'],
                        'image': image,
                        'url': f"{settings.musicbrainz_url}/release-group/{release['release_group_mbid']}"
                    }
                )

    content = {
        'listening': listening
    }

    return JSONResponse(status_code=HTTPStatus.OK.value, content=content)


def discogs_artist_image(discogsid: str, request: Request, sessions: SessionCaches) -> URL:
    """
    Get artist image URL from Discogs
    """

    settings = get_settings()
    headers = {
        'Accept': 'application/vnd.discogs.v2.discogs+json',
        'Authorization': f'Discogs key={settings.discogs_consumer_key}, secret={settings.discogs_consumer_secret}'
    }
    url = f'{settings.discogs_api_url}/artists/{discogsid}'

    rsp = sessions.images.get(url=url, headers=headers, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        body = rsp.json()
        image_url = None
        if 'images' in body:
            for image in body['images']:
                if image['type'] == 'primary':
                    if 'uri150' in image:
                        image_url = image['uri150']
                        break

                    if 'uri' in image:
                        image_url = image['uri']
                        break

        if image_url:
            image_url = signed_cdn_url(URL(image_url).replace(scheme='https'))
        else:
            image_url = request.url_for('static', path='/heroicons/24/solid/musical-note.svg')

        return image_url

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())


def listenbrainz_artist_stats(sessions: SessionCaches, count: int, period: str = 'week') -> dict:
    """
    Get artist stats from ListenBrainz
    """

    settings = get_settings()
    headers = {
        'Token': settings.listenbrainz_api_token
    }
    params = {
        'count': count,
        'range': period
    }
    url = f'{settings.listenbrainz_api_url}/stats/user/{settings.listenbrainz_api_user}/artists'
    rsp = sessions.stats.get(url=url, headers=headers, params=params, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        return rsp.json()

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())


def listenbrainz_listens(sessions: SessionCaches, count: int) -> dict:
    """
    Get user listens from ListenBrainz
    """

    settings = get_settings()
    headers = {
        'Token': settings.listenbrainz_api_token
    }
    params = {
        'count': count
    }
    url = f'{settings.listenbrainz_api_url}/user/{settings.listenbrainz_api_user}/listens'
    rsp = sessions.listens.get(
        url=url,
        headers=headers,
        params=params,
        timeout=settings.api_timeout
    )
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        return rsp.json()

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())


def listenbrainz_release_stats(sessions: SessionCaches, count: int, period: str = 'week') -> dict:
    """
    Get release group stats from ListenBrainz
    """

    settings = get_settings()
    headers = {
        'Token': settings.listenbrainz_api_token
    }
    params = {
        'count': count,
        'range': period
    }
    url = f'{settings.listenbrainz_api_url}/stats/user/{settings.listenbrainz_api_user}/release-groups'
    rsp = sessions.stats.get(url=url, headers=headers, params=params, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        return rsp.json()

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())


def musicbrainz_artist(
    mbid: str,
    sessions: SessionCaches,
) -> dict:
    """
    Get artist details from MusicBrainz
    """

    settings = get_settings()
    params = {
        'fmt': 'json',
        'inc': 'url-rels'
    }
    url = f'{settings.musicbrainz_api_url}/artist/{mbid}'
    rsp = sessions.artists.get(url=url, params=params, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        return rsp.json()

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())


def coverart_image(
    mbid: str,
    request: Request,
    sessions: SessionCaches,
    preload: bool,
    metadata: str = 'release',
) -> URL:
    """
    Get release covert art image from CoverArtArchive
    """

    settings = get_settings()
    url = f'{settings.coverart_api_url}/{metadata}/{mbid}'
    rsp = sessions.images.get(url=url, timeout=settings.api_timeout)
    logger.debug('%s: %s', url, rsp.status_code)

    if rsp.status_code == HTTPStatus.OK:
        body = rsp.json()
        image_url = None
        if 'images' in body:
            for image in body['images']:
                if image['front'] or (
                    not image['front'] and not image['back'] and image['approved']
                ):
                    if 'thumbnails' in image and 'small' in image['thumbnails']:
                        image_url = image['thumbnails']['small']
                        break

                    if 'image' in image:
                        image_url = image['image']
                        break

        if image_url:
            image_url = signed_cdn_url(URL(image_url).replace(scheme='https'))

        else:
            if preload:
                image_url = None
            else:
                image_url = request.url_for('static', path='/heroicons/24/solid/musical-note.svg')

        return image_url

    raise HTTPException(status_code=rsp.status_code, detail=rsp.json())
