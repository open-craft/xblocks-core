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


def test_defaults_render():
    """Test the student view initializes the React app with the block data."""
    block = make_block()
    frag = block.student_view().to_dict()

    assert frag["js_init_fn"] == "FlashCardsXBlock"
    init_args = frag["json_init_args"]
    assert "url" in init_args
    assert init_args["data"] == {
        "display_name": "Flashcards",
        "is_shuffled": True,
        "cards": [],
    }


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
