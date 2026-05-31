"""Fetch WDI indicator zip files from the World Bank API, with disk cache."""

from __future__ import annotations

import logging

import requests

from wdi_to_parquet.cache import CacheStore

logger = logging.getLogger(__name__)

WB_API = "https://api.worldbank.org/v2/en/indicator/{indicator}?downloadformat=csv"


def fetch_indicator_zip(indicator: str, cache: CacheStore) -> bytes:
    """Return zip bytes for `indicator`, using cache when fresh.

    On cache miss, downloads from the World Bank API and writes to cache.
    Raises requests.HTTPError on non-2xx responses.
    """
    cached = cache.get(indicator)
    if cached is not None:
        logger.info("cache HIT: %s", indicator)
        return cached

    url = WB_API.format(indicator=indicator)
    logger.info("cache MISS: fetching %s from %s", indicator, url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.content
    cache.put(indicator, data)
    logger.info("cached %s (%d bytes)", indicator, len(data))
    return data
