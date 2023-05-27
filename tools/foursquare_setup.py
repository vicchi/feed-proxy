"""
Feed Proxy tools: Get your Foursquare OAuth token
"""

import logging

import requests
from starlette.applications import Starlette
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from feed_proxy.common.settings import get_settings

logger = logging.getLogger('gunicorn.error')


async def home_page(_request: Request) -> HTMLResponse:
    """
    Main landing page hander
    """

    url = f'{settings.foursq_base_url}{settings.foursq_authorize_url}?response_type=code&client_id={settings.foursq_client_id}&redirect_uri={settings.foursq_redirect_url}'    # pylint: disable=line-too-long
    body = f"""
    <html>
    <title>Get your Foursquare OAuth token</title>
    {STYLE}
    <h1>Get your Foursquare OAuth token</h1>
    <p>You need a token in order to retrieve your own personal data from the Foursquare APIs.</p>
    <p style="font-size: 1.2em;"><strong><a href="{url}">Log in with Foursquare</a></strong> to get your token</p>
    """

    return HTMLResponse(content=body)


async def authorise(request: Request) -> HTMLResponse:
    """
    Authorisation page handler
    """

    code = request.query_params['code']
    headers = {
        'Accept': 'application/json',
    }
    params = {
        'code': code,
        'client_id': settings.foursq_client_id,
        'client_secret': settings.foursq_secret,
        'redirect_uri': str(settings.foursq_redirect_url),
        'grant_type': 'authorization_code'
    }
    url = URL(f'{settings.foursq_base_url}{settings.foursq_token_url}')
    url = url.include_query_params(**params)

    rsp = requests.get(url=str(url), headers=headers, timeout=10)
    if rsp.status_code != 200:
        body = f"""
        {STYLE}
        <h1>The Foursquare API returned an error: {rsp.status_code}</h1>
        <code>{rsp.json()}</code>
        """

    else:
        data = rsp.json()
        body = f"""
        {STYLE}
        <h1>Your Foursquare API Oauth Token</h1>
        <p>access_token: <code>{data['access_token']}</code></p>
        """

    return HTMLResponse(content=body)


routes = [Route('/', endpoint=home_page), Route('/authorise', endpoint=authorise)]

STYLE = "<style>body { font-family: Helvetica, sans-serif; padding: 1em 2em; }</style>"

settings = get_settings()
app = Starlette(debug=True, routes=routes)
