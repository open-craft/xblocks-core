"""Tests for the Matching Block"""

import json
from typing import Any
from unittest.mock import MagicMock, Mock

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblock_matching import MatchingXBlock


def make_block(**fields: str) -> MatchingXBlock:
    """Build a block with specific fields set."""
    mock_usage_id = Mock(block_id="my_block_id")
    scope_ids = ScopeIds("my_user_id", "my_block_type", "my_def_id", mock_usage_id)
    return MatchingXBlock(ToyRuntime(), scope_ids=scope_ids, field_data=DictFieldData(data=fields))


def mock_handle_request(method: str, data: dict[str, Any]):
    """Return a request object compatible with an xblock_handler."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.body = json.dumps(data).encode("utf-8")
    return mock_request


def get_student_content(block: MatchingXBlock) -> str:
    """Get the contents of a student render for a block."""
    frag = block.student_view()
    as_dict = frag.to_dict()
    return as_dict["content"]


def test_defaults_render():
    """Test the basic view loads."""
    block = make_block()
    content = get_student_content(block)
    assert "matching-start-screen" in content


def test_render_with_data():
    """Test the basic view loads."""
    block = make_block(
        display_name="Matching!",
        is_shuffled=True,
        has_timer=True,
        cards=[
            {
                "term": "hello",
                "definition": "a greeting",
            },
            {
                "term": "foo",
                "definition": "a common placeholder in code",
            },
        ],
    )
    content = get_student_content(block)
    assert "matching-start-screen" in content
    assert "a common placeholder in code" in content


def test_save_settings():
    """Test that the xblock settings are saved."""
    block = make_block()
    request = mock_handle_request(
        "POST",
        {
            "display_name": "Matching!",
            "is_shuffled": "false",
            "has_timer": "false",
            "cards": [
                {
                    "term": "hello",
                    "definition": "a greeting",
                },
                {
                    "term": "foo",
                    "definition": "a common placeholder in code",
                },
            ],
        },
    )
    block.save_settings(request)
    assert block.display_name == "Matching!"
    assert not block.is_shuffled
    assert not block.has_timer
    assert len(block.cards) == 2
    assert block.cards[0]["term"] == "hello"
    assert block.cards[0]["definition"] == "a greeting"
