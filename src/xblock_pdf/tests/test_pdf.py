"""Tests for the PDF Block"""

import json
from dataclasses import dataclass
from typing import Any, TypedDict
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from requests import Response
from requests.exceptions import HTTPError
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblock_pdf import PDFBlock
from xblock_pdf.utils import error_response, fetch_external_url

MockOptValues = TypedDict("MockOptValues", {"edx-platform.user_is_staff": bool, "edx-platform.user_id": int})


@dataclass
class MockUser:
    opt_attrs: MockOptValues


class ToyUserService:
    """
    Toy version of the user service that implements just enough for us to work with.
    """

    def __init__(self, *, user_id: int, is_staff=False):
        self._user = MockUser(opt_attrs={"edx-platform.user_is_staff": is_staff, "edx-platform.user_id": user_id})

    def get_current_user(self):
        return self._user


class ToyPermissionsService:
    """
    Toy version of the studio_user_permissions service.
    """

    def __init__(self, can_read=True, can_write=False):
        self._can_read = can_read
        self._can_write = can_write

    def can_read(self, _context_key):
        return self._can_read

    def can_write(self, _context_key):
        return self._can_write


class ToyServiceRuntime(ToyRuntime):
    """
    Modified toy runtime that includes custom services for mocking/testing.
    """

    def __init__(self, *, services: dict[str, Any] | None = None):
        super().__init__()
        if services is not None:
            self._services.update(services)


def make_block(*, services: dict[str, Any] | None = None, **fields: str) -> PDFBlock:
    """Build a block with specific fields set."""
    scope_ids = ScopeIds("1", "2", "3", "4")
    return PDFBlock(ToyServiceRuntime(services=services), scope_ids=scope_ids, field_data=DictFieldData(data=fields))


def get_student_content(block: PDFBlock) -> str:
    """Get the contents of a student render for a block."""
    frag = block.student_view()
    as_dict = frag.to_dict()
    return as_dict["content"]


def mock_handle_request(data: dict[str, Any] | None = None, method: str = "POST"):
    """Return a request object compatible with an xblock_handler."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.body = json.dumps(data).encode("utf-8")
    return mock_request


def test_defaults_render():
    """Test the basic view loads."""
    block = make_block()
    content = get_student_content(block)
    assert '<iframe src="https://tutorial.math.lamar.edu/pdf/Trig_Cheat_Sheet.pdf"' in content


def test_download_button():
    """Test the allow_download toggle."""
    block = make_block(allow_download=True)
    get_student_content(block)
    content = get_student_content(block)
    assert "Download the PDF" in content
    block.allow_download = False
    content = get_student_content(block)
    assert "Download the PDF" not in content


def test_source_url():
    """Test rendering based on whether there's a source URL"""
    block = make_block()
    get_student_content(block)
    content = get_student_content(block)
    assert "Download the Source Document" not in content
    block.source_url = "https://example.com/"
    content = get_student_content(block)
    assert "Download the source document" in content


@patch.object(ToyRuntime, "publish")
def test_download_event_fires(mock_publish):
    """Test that we fire a download event."""
    block = make_block()
    request = mock_handle_request()
    block.on_download(request)
    mock_publish.assert_called_with(
        block,
        "edx.pdf.downloaded",
        {
            "url": "https://tutorial.math.lamar.edu/pdf/Trig_Cheat_Sheet.pdf",
            "source_url": "",
        },
    )


def test_get_settings():
    """Test that fetching the block's settings works."""
    block = make_block()
    request = mock_handle_request({}, method="GET")
    result = json.loads(block.load_pdf(request).body)
    assert result["display_name"] == "PDF"


@override_settings(GOTENBERG_HOST=None)
def test_convert_pdf_fails_no_gotenberg():
    """
    Test that PDF conversion fails if Gotenberg is not available.
    """
    block = make_block(
        services={
            "studio_user_permissions": ToyPermissionsService(can_write=True),
        }
    )
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert result.status_code == 400
    assert b"Gotenberg not enabled. PDF Conversion unavailable." in result.body


@override_settings(GOTENBERG_HOST=None)
def test_convert_pdf_fails_no_permissions_service():
    """
    Test that PDF conversion fails if Gotenberg is not available.
    """
    block = make_block()
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert result.status_code == 400
    assert b"Conversion endpoint may only be called in a studio permissions-aware environment." in result.body


@override_settings(GOTENBERG_HOST=None)
def test_convert_pdf_fails_not_authorized():
    """
    Test that PDF conversion fails if Gotenberg is not available.
    """
    block = make_block(
        services={
            "studio_user_permissions": ToyPermissionsService(can_write=False),
        }
    )
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert result.status_code == 403
    assert b"You do not have permission to manage files for this block." in result.body


@override_settings(GOTENBERG_HOST="https://gotenberg/")
@patch("xblock_pdf.pdf.logger")
@patch("xblock_pdf.pdf.fetch_source_asset")
@pytest.mark.django_db
def test_failed_fetch_logs(mock_fetch, mock_log):
    block = make_block(
        services={
            "studio_user_permissions": ToyPermissionsService(can_write=True),
            "user": ToyUserService(
                is_staff=True, user_id=User.objects.create(username="beep", email="beep@example.com").id
            ),
        }
    )
    mock_fetch.side_effect = HTTPError(response=error_response({"error": "Failed."}, status=400))
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert mock_log.exception.has_been_called()
    assert result.status_code == 502
    assert b"Could not fetch source document." in result.body


@override_settings(GOTENBERG_HOST="https://gotenberg/")
@patch("xblock_pdf.utils.requests")
@patch("xblock_pdf.pdf.fetch_source_asset")
@pytest.mark.django_db
def test_failed_conversion(mock_fetch, mock_requests):
    block = make_block(
        services={
            "studio_user_permissions": ToyPermissionsService(can_write=True),
            "user": ToyUserService(
                is_staff=True, user_id=User.objects.create(username="beep", email="beep@example.com").id
            ),
        }
    )
    mock_fetch.return_value = b"beep"
    mock_requests.return_value = error_response({"error": "Nope."})
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert result.status_code == 500
    assert b"PDF Conversion failed." in result.body


@override_settings(GOTENBERG_HOST="https://gotenberg/")
@patch("xblock_pdf.pdf.add_asset")
@patch("xblock_pdf.utils.requests")
@patch("xblock_pdf.pdf.fetch_source_asset")
@pytest.mark.django_db
def test_successful_conversion_with_perms_service(mock_fetch, mock_requests, mock_add_asset):
    block = make_block(
        services={
            "studio_user_permissions": ToyPermissionsService(can_write=True),
            "user": ToyUserService(
                is_staff=True, user_id=User.objects.create(username="beep", email="beep@example.com").id
            ),
        }
    )
    mock_fetch.return_value = b"beep"
    mock_response = Response()
    mock_response.__setstate__({"status_code": 200, "_content": b"boop"})
    mock_requests.post.return_value = mock_response
    mock_add_asset.return_value = "https://example.com/exported.pdf"
    request = mock_handle_request({"url": "https://example.com/thing.doc"})
    result = block.convert_pdf(request)
    assert result.status_code == 200
    assert b"https://example.com/exported.pdf" in result.body


@override_settings(LMS_ROOT_URL="https://example.com/")
def test_fetch_external_url_raises():
    with pytest.raises(HTTPError):
        fetch_external_url("https://foo.bar")


@override_settings(LMS_ROOT_URL="https://example.com/")
@patch("xblock_pdf.utils.requests")
def test_fetch_external_url(mock_requests):
    mock_response = Response()
    mock_response.__setstate__({"status_code": 200, "_content": b"boop"})
    mock_requests.get.return_value = mock_response
    result = fetch_external_url("https://example.com/beep.pdf")
    assert result == b"boop"
