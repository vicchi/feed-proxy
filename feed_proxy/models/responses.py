"""
Feed Proxy API: models package; responses module
"""

from typing import List
from pydantic import BaseModel, HttpUrl


class Track(BaseModel):
    """
    A single music track
    """

    artist: str
    track: str
    image: HttpUrl
    url: HttpUrl


class Artist(BaseModel):
    """
    A single music artist
    """

    name: str
    count: int
    image: HttpUrl
    url: HttpUrl


class Release(BaseModel):
    """
    A single music release
    """

    artist: str
    release: str
    image: HttpUrl
    url: HttpUrl


class CurrentMusic(BaseModel):
    """
    All current music stats response
    """

    tracks: List[Track] = []
    artists: List[Artist] = []
    releases: List[Release] = []


class CurrentWeather(BaseModel):
    """
    Current weather response
    """

    temp: float
    icon: HttpUrl
    descr: str
