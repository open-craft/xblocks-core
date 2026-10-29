"""Tests for the Flashcards Block"""

from unittest.mock import Mock

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblock_flashcards import FlashcardsXBlock


def make_block(**fields: str) -> FlashcardsXBlock:
    """Build a block with specific fields set."""
    scope_ids = ScopeIds("1", "2", "3", Mock(block_id="abc"))
    return FlashcardsXBlock(ToyRuntime(), scope_ids=scope_ids, field_data=DictFieldData(data=fields))


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


def test_load_data_default():
    """Test loading data as json."""
    block = make_block()
    data = block.load_data().json

    assert data["display_name"] == "Flashcards"
    assert data["is_shuffled"] is True
    assert data["cards"] == []


def test_load_data():
    """Test loading data as json, with custom cards."""
    block = make_block(
        cards=[
            {
                "key": "card-key-1",
                "front": {"text": "front side", "image": {"url": "", "alt": ""}},
                "back": {"text": "back side", "image": {"url": "", "alt": ""}},
                "editor_open": True,
            }
        ]
    )
    data = block.load_data().json

    assert data["display_name"] == "Flashcards"
    assert data["is_shuffled"] is True
    assert data["cards"] == [
        {
            "key": "card-key-1",
            "front": {"text": "front side", "image": {"url": "", "alt": ""}},
            "back": {"text": "back side", "image": {"url": "", "alt": ""}},
            "editor_open": True,
        }
    ]
