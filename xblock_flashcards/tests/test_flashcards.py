"""Tests for the Flashcards Block"""

import json
from typing import Any
from unittest.mock import MagicMock

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblock_flashcards import FlashcardsXBlock


def make_block(**fields: str) -> FlashcardsXBlock:
    """Build a block with specific fields set."""
    scope_ids = ScopeIds("1", "2", "3", "4")
    return FlashcardsXBlock(ToyRuntime(), scope_ids=scope_ids, field_data=DictFieldData(data=fields))


def mock_handle_request(method: str, data: dict[str, Any]):
    """Return a request object compatible with an xblock_handler."""
    mock_request = MagicMock()
    mock_request.method = method
    mock_request.body = json.dumps(data).encode("utf-8")
    return mock_request


def get_student_content(block: FlashcardsXBlock) -> str:
    """Get the contents of a student render for a block."""
    frag = block.student_view()
    as_dict = frag.to_dict()
    return as_dict["content"]


def test_defaults_render():
    """Test the basic view loads."""
    block = make_block()
    content = get_student_content(block)
    assert "flashcards-start-screen" in content


def test_save_settings():
    """Test that the xblock settings are saved."""
    block = make_block()
    request = mock_handle_request(
        "POST",
        {
            "display_name": "Flashcards!",
            "is_shuffled": "false",
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
    assert block.display_name == "Flashcards!"
    assert not block.is_shuffled
    assert len(block.cards) == 2
    assert block.cards[0]["term"] == "hello"
    assert block.cards[0]["definition"] == "a greeting"
