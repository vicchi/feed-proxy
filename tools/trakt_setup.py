"""
Feed Proxy tools: Get your Trakt OAuth token
"""

import logging

import requests
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from feed_proxy.common.settings import get_settings

logger = logging.getLogger('gunicorn.error')


async def home_page(_request: Request) -> HTMLResponse:
    """
    Main landing page hander
    """

    url = f'{settings.trakt_base_url}{settings.trakt_authorize_url}?response_type=code&client_id={settings.trakt_client_id}&redirect_uri={settings.trakt_redirect_url}'    # pylint: disable=line-too-long
    body = f"""
    <html>
    <title>Get your Trakt OAuth token</title>
    {STYLE}
    <h1>Get your Trakt OAuth token</h1>
    <p>You need a token in order to retrieve your own personal data from the Trakt APIs.</p>
    <p style="font-size: 1.2em;"><strong><a href="{url}">Log in with Trakt</a></strong> to get your token</p>
    """

    return HTMLResponse(content=body)


async def authorise(request: Request) -> HTMLResponse:
    """
    Authorisation page handler
    """

    code = request.query_params['code']
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'code': code,
        'client_id': settings.trakt_client_id,
        'client_secret': settings.trakt_secret,
        'redirect_uri': str(settings.trakt_redirect_url),
        'grant_type': 'authorization_code'
    }
    url = f'{settings.trakt_api_url}{settings.trakt_token_url}'

    rsp = requests.post(url=url, headers=headers, json=data, timeout=10)
    if rsp.status_code != 200:
        body = f"""
        {STYLE}
        <h1>The Trakt API returned an error: {rsp.status_code}</h1>
        <code>{rsp.json()}</code>
        """

    else:
        data = rsp.json()
        body = f"""
        {STYLE}
        <h1>Your Trakt API Oauth Token</h1>
        <p>access_token: <code>{data['access_token']}</code></p>
        <p>token_type: <code>{data['token_type']}</code></p>
        <p>expires_in: <code>{data['expires_in']}</code></p>
        <p>refresh_token: <code>{data['refresh_token']}</code></p>
        <p>scope: <code>{data['scope']}</code></p>
        <p>created_at: <code>{data['created_at']}</code></p>
        """

    return HTMLResponse(content=body)


routes = [Route('/', endpoint=home_page), Route('/authorise', endpoint=authorise)]

STYLE = "<style>body { font-family: Helvetica, sans-serif; padding: 1em 2em; }</style>"

settings = get_settings()
app = Starlette(debug=True, routes=routes)
