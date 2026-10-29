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
    scope_ids = ScopeIds("1", "2", "3", Mock(block_id="abc"))
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


def test_renders_with_pairs():
    """Test the basic view loads with existing pairs."""
    block = make_block(
        pairs=[
            {"left": {"text": "left text"}, "right": {"text": "right text"}, "key": "key-foo-1"},
            {"left": {"text": "more left text"}, "right": {"text": "more right text"}, "key": "key-foo-2"},
        ]
    )
    content = get_student_content(block)
    assert "matching-start-screen" in content


def test_load_data():
    """Test loading data as json."""
    block = make_block()
    data = block.load_data().json

    assert data["display_name"] == "Matching"
    assert data["is_shuffled"] is True
    assert data["has_timer"] is True
    assert data["pairs"] == []


def test_complete_game():
    """Test completing a game and checking the timing"""
    block = make_block()

    # first attempt, 12 seconds
    data = block.complete_matching_game(mock_handle_request("POST", {"new_time": 12})).json
    assert data["new_time"] == 12
    assert data["prev_best_time"] is None
    assert block.best_time == 12

    # second attempt, slower than the first
    data = block.complete_matching_game(mock_handle_request("POST", {"new_time": 17})).json
    assert data["new_time"] == 17
    assert data["prev_best_time"] == 12
    assert block.best_time == 12

    # third attempt, quicker than the first, new best time
    data = block.complete_matching_game(mock_handle_request("POST", {"new_time": 8})).json
    assert data["new_time"] == 8
    assert data["prev_best_time"] == 12
    assert block.best_time == 8
