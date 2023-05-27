"""
Feed Proxy API: common package; .env settings module
"""

from functools import lru_cache
from pathlib import Path

import dotenv
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 5
DEFAULT_BACKOFF = 0.1


class Settings(BaseSettings):
    """
    Feed Proxy API .env settings
    """

    site_host: str
    site_url: HttpUrl
    site_contact: EmailStr
    environment: str

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

    openmeteo_api_url: HttpUrl

    discogs_api_url: HttpUrl
    discogs_consumer_key: str
    discogs_consumer_secret: str

    musicbrainz_url: HttpUrl
    musicbrainz_api_url: HttpUrl

    default_lng: float
    default_lat: float

    api_timeout: int = DEFAULT_TIMEOUT
    api_retries: int = DEFAULT_RETRIES
    api_backoff: float = DEFAULT_BACKOFF

    cache_path: Path
    cache_listens_expiry: str
    cache_listens: Path
    cache_stats_expiry: str
    cache_stats: Path
    cache_images_expiry: str
    cache_images: Path
    cache_artists_expiry: str
    cache_artists: Path

    cache_weather_expiry: str
    cache_weather: Path

    static_path: Path
    cdn_base_url: HttpUrl
    cdn_path: Path
    cdn_secret: str
    cdn_hash_type: str
    cdn_hash_size: int
    cdn_image_height: int
    cdn_image_width: int

    feed_api_version: str

    class Config:    # pylint: disable=too-few-public-methods
        """
        Feed Proxy API .env settings config
        """

        env_file = dotenv.find_dotenv()


@lru_cache
def get_settings() -> Settings:
    """
    Find and return the settings in the current .env
    """

    return Settings()
