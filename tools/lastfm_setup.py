"""
Feed Proxy tools: Get your Last.fm OAuth token
"""

import hashlib
import logging

import requests
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from feed_proxy.common.settings import get_settings

logger = logging.getLogger('gunicorn.error')


def sign_params(params: dict, secret: str) -> str:
    """
    Generate a Last.fm API method signature
    """

    tokens = []
    for key, value in sorted(params.items()):
        if key not in ['format']:
            tokens.append(f'{key}{value}')

    tokens.append(secret)
    signature = ''.join(tokens)

    return hashlib.md5(signature.encode('utf-8')).hexdigest()


async def home_page(_request: Request) -> HTMLResponse:
    """
    Main landing page hander
    """

    url = f'{settings.lastfm_base_url}{settings.lastfm_authorize_url}?api_key={settings.lastfm_api_key}&cb={settings.trakt_redirect_url}'
    body = f"""
    <html>
    <title>Get your Last.fm OAuth token</title>
    {STYLE}
    <h1>Get your Last.fm OAuth token</h1>
    <p>You need a token in order to retrieve your own personal data from the Last.fm APIs.</p>
    <p style="font-size: 1.2em;"><strong><a href="{url}">Log in with Last.fm</a></strong> to get your token</p>
    """

    return HTMLResponse(content=body)


async def authorise(request: Request) -> HTMLResponse:
    """
    Authorisation page handler
    """

    token = request.query_params['token']
    headers = {
        'Accept': 'application/json',
    }

    data = {
        'method': settings.lastfm_session_method,
        'token': token,
        'api_key': settings.lastfm_api_key,
        'format': 'json',
    }
    signature = sign_params(data, settings.lastfm_secret)

    data['api_sig'] = signature

    rsp = requests.get(url=settings.lastfm_api_url, headers=headers, params=data, timeout=10)
    if rsp.status_code != 200:
        body = f"""
        {STYLE}
        <h1>The Last.fm API returned an error: {rsp.status_code}</h1>
        <code>{rsp.json()}</code>
        """

    else:
        data = rsp.json()
        session = data['session']
        body = f"""
        {STYLE}
        <h1>Your Last.fm API Oauth Token</h1>
        <p>name: <code>{session['name']}</code></p>
        <p>key: <code>{session['key']}</code></p>
        <p>subscriber: <code>{session['subscriber']}</code></p>
        """

    return HTMLResponse(content=body)


routes = [Route('/', endpoint=home_page), Route('/authorise', endpoint=authorise)]

STYLE = "<style>body { font-family: Helvetica, sans-serif; padding: 1em 2em; }</style>"

settings = get_settings()
app = Starlette(debug=True, routes=routes)
