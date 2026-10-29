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

    Paths are relative to the ``xblock_flashcards`` package. This replaces
    ``pkg_resources.resource_string``, which setuptools no longer ships.
    """
    return files("xblock_flashcards").joinpath(path).read_text(encoding="utf8")


# TODO: update storage settings to use course assets instead,
# so any uploaded files are exported/imported with the course.
def get_block_storage():
    """
    Returns storage for flashcard xblock assets.

    If OPENEDX_FLASHCARDS_XBLOCK_STORAGE is not defined for S3, returns default_storage.
    """
    storage_settings = getattr(settings, "OPENEDX_FLASHCARDS_XBLOCK_STORAGE", None)
    if not storage_settings:
        return default_storage

    storage_class = storage_settings.get("storage_class")
    storage_kwargs = storage_settings.get("settings", {}) or {}

    if not storage_class:
        raise ImproperlyConfigured("OPENEDX_FLASHCARDS_XBLOCK_STORAGE.storage_class missing")

    try:
        storage_class = import_string(storage_class)
    except Exception as e:
        raise ImproperlyConfigured(f"Failed importing storage class {storage_class}: {e}") from e

    try:
        return storage_class(**storage_kwargs)
    except Exception as e:
        raise ImproperlyConfigured(f"Failed initializing storage {storage_class} with {storage_kwargs}: {e}") from e
