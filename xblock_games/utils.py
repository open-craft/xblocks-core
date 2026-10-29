"""
Utility methods for xblock
"""

import logging
from functools import cache
from importlib.resources import files

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string

log = logging.getLogger(__name__)


@cache
def read_resource(path):
    """
    Return the text of a file bundled with this package, e.g.
    ``read_resource("static/html/flashcards.html")``.

    Paths are relative to the ``xblock_games`` package. This replaces
    ``pkg_resources.resource_string``, which setuptools no longer ships.
    """
    return files("xblock_games").joinpath(path).read_text(encoding="utf8")


def get_gamesxblock_storage():
    """
    Returns storage for gamesxblock assets.

    If GAMESXBLOCK_STORAGE is not defined for S3, returns default_storage.
    """
    storage_settings = getattr(settings, "GAMESXBLOCK_STORAGE", None)
    if not storage_settings:
        return default_storage

    storage_class = storage_settings.get("storage_class")
    storage_kwargs = storage_settings.get("settings", {}) or {}

    if not storage_class:
        raise ImproperlyConfigured("GAMESXBLOCK_STORAGE.storage_class missing")

    try:
        storage_class = import_string(storage_class)
    except Exception as e:
        raise ImproperlyConfigured(f"Failed importing storage class {storage_class}: {e}") from e

    try:
        return storage_class(**storage_kwargs)
    except Exception as e:
        raise ImproperlyConfigured(f"Failed initializing storage {storage_class} with {storage_kwargs}: {e}") from e


def delete_image(storage, key: str):
    """Delete an image from storage if it exists."""
    if storage.exists(key):
        storage.delete(key)
        return True
    return False
