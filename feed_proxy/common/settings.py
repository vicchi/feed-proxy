"""
Feed Proxy API: common package; .env settings module
"""

from pathlib import Path

import dotenv
from pydantic import AnyHttpUrl, BaseSettings, HttpUrl


class Settings(BaseSettings):
    """
    Feed Proxy API .env settings
    """

    trakt_base_url: HttpUrl
    trakt_authorize_url: str
    trakt_api_url: HttpUrl
    trakt_token_url: str

    trakt_client_id: str
    trakt_secret: str
    trakt_redirect_url: AnyHttpUrl

    lastfm_base_url: HttpUrl
    lastfm_authorize_url: str
    lastfm_api_url: HttpUrl
    lastfm_session_method: str

    lastfm_api_key: str
    lastfm_secret: str
    lastfm_redirect_url: AnyHttpUrl

    foursq_base_url: HttpUrl
    foursq_authorize_url: str
    foursq_api_url: HttpUrl
    foursq_token_url: str

    foursq_client_id: str
    foursq_secret: str
    foursq_redirect_url: AnyHttpUrl

    lastfm_oauth_token: str
    trakt_oauth_token: str
    trakt_refresh_token: str
    foursq_oauth_token: str

    tmdb_api_key: str

    listenbrainz_api_url: HttpUrl
    listenbrainz_api_user: str
    listenbrainz_api_token: str

    coverart_api_url: HttpUrl

    cache_expiration: int
    cache_path: Path
    static_path: Path

    feed_api_version: str

    class Config:    # pylint: disable=too-few-public-methods
        """
        Feed Proxy API .env settings config
        """

        env_file = dotenv.find_dotenv()


def get_settings():
    """
    Find and return the settings in the current .env
    """

    return Settings()