"""Utility functions for PDF XBlock."""

import json
from io import BytesIO
from logging import getLogger
from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from opaque_keys.edx.locator import BlockUsageLocator, LibraryUsageLocatorV2
from requests import HTTPError
from webob import Response

logger = getLogger(__name__)


def is_gotenberg_enabled() -> bool:
    """
    Returns if gotenberg is enabled.
    """
    return bool(get_gotenberg_host())


def get_gotenberg_host() -> str | None:
    """
    Returns the hostname of the Gotenberg instance, if configured.
    Returns None if Gotenberg is not configured.
    """
    return getattr(settings, "GOTENBERG_HOST", None)


def get_conversion_url() -> str | None:
    """
    Get the URL for sending a document for conversion by Gotenberg
    """
    return (base_url := get_gotenberg_host()) and f"{base_url}/forms/libreoffice/convert"


def add_asset(
    location: BlockUsageLocator | LibraryUsageLocatorV2,
    # Must have the 'name' attribute set.
    asset: InMemoryUploadedFile,
    user: AbstractBaseUser,
) -> str:  # pragma: no cover
    """
    Adds an asset for this block. If we aren't in the studio environment, will create ImportErrors.
    Easily mocked for tests.
    """
    # pylint: disable=import-error,import-outside-toplevel
    from cms.djangoapps.contentstore.asset_storage_handlers import update_course_run_asset

    # pylint: disable=import-error,import-outside-toplevel
    from openedx.core.djangoapps.content_libraries.api import add_library_block_static_asset_file

    match location:
        case BlockUsageLocator():
            asset = update_course_run_asset(location.course_key, asset)
            return asset.get_static_path_from_location(asset.location)
        case LibraryUsageLocatorV2():
            # Static assets with a /static/ prefix rendered by the backend have their paths
            # translated to the paths for loading library assets.
            path = f"static/{asset.name}"
            # The path must be stored without the leading slash.
            add_library_block_static_asset_file(location, path, asset.read(), user)
            return "/" + path


def fetch_external_url(
    url: str,
) -> bytes:
    """
    Fetches an 'external' URL, which is only actually permitted if it's from the LMS,
    and returns its byte content.
    """
    allowed = urlparse(settings.LMS_ROOT_URL)
    target = urlparse(url)
    if (target.scheme.lower(), target.netloc.lower()) != (allowed.scheme.lower(), allowed.netloc.lower()):
        raise HTTPError("Unpermitted URL.")
    response = requests.get(url, timeout=(10, 120))
    response.raise_for_status()
    return response.content


def fetch_source_asset(
    location: BlockUsageLocator | LibraryUsageLocatorV2, source_url: str
) -> bytes:  # pragma: no cover
    """
    Fetch a source asset and return its bytes. When using a full URL, pull it via requests. When using
    an absolute URL in a library, find the relevant asset and return its bytes.
    """
    # pylint: disable=import-error,import-outside-toplevel
    from openedx.core.djangoapps.content_libraries import api as libraries_api

    # pylint: disable=import-error,import-outside-toplevel
    from openedx_content import api as content_api

    if not source_url.startswith("/"):
        return fetch_external_url(source_url)
    match location:
        case BlockUsageLocator():
            return fetch_external_url(source_url)
        case LibraryUsageLocatorV2():
            version_uuid = libraries_api.get_component_from_usage_key(location).versioning.draft.uuid
            component_version = content_api.get_component_version_by_uuid(version_uuid)
            media = component_version.componentversionmedia_set.get(path=source_url[1:]).media
            with media.read_file() as f:
                return f.read()


def convert_to_pdf(source_filename: str, data: bytes, filename: str) -> InMemoryUploadedFile | None:
    """
    Uses the Gotenberg service to convert the document at `doc_url` to a PDF file.
    """
    if not (conversion_url := get_conversion_url()):  # pragma: no cover
        return None

    pdf_response = requests.post(conversion_url, files={"file": (source_filename, data)}, timeout=(2, 120))
    if pdf_response.status_code != 200:
        logger.error("Gotenberg error: %s", pdf_response.content)
        return None
    return InMemoryUploadedFile(
        file=BytesIO(pdf_response.content),
        field_name="file",
        content_type="application/pdf",
        size=len(pdf_response.content),
        charset=None,
        name=filename,
    )


def is_all_download_disabled():
    """Check if all downloads are disabled or not."""
    return getattr(settings, "PDFXBLOCK_DISABLE_ALL_DOWNLOAD", False)


def error_response(data: dict[Any, Any], status: int = 400):
    """
    Returns a JSON response object with the appropriate status.
    """
    return Response(
        json.dumps(data),
        status=status,
        content_type="application/json",
        charset="utf8",
    )
