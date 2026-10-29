"""Tests for image storage-key persistence (LP-913).

Storage keys were not round-tripped by save_settings, so after a reload the
block no longer knew which file belonged to a card. These tests are independent
of which authoring editor the block uses.
"""

from unittest.mock import Mock

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xblock_games.constants import DEFAULT, UPLOAD
from xblock_games.games import GamesXBlock
from xblock_games.handlers.common import CommonHandlers
from xblock_games.handlers.flashcards import FlashcardsHandlers

BLOCK_ID = "1234567890abcdef1234567890abcdef"


def _make_block():
    usage_id = Mock()
    usage_id.block_id = BLOCK_ID
    scope_ids = ScopeIds("user", "games", "def", usage_id)
    block = GamesXBlock(Mock(), DictFieldData({}), scope_ids)
    block.game_type = "flashcards"
    block.cards = [{"term": "a", "definition": "b"}]
    block.is_shuffled = True
    block.has_timer = False
    block.display_name = "Games"
    return block


def test_save_settings_persists_image_paths():
    """Storage keys must round-trip, or the card loses track of its file."""
    xblock = _make_block()
    result = CommonHandlers.save_settings(
        xblock,
        {
            "game_type": "flashcards",
            "cards": [
                {
                    "term": "t",
                    "definition": "d",
                    "term_image": "http://example.com/i.png",
                    "term_image_path": f"{UPLOAD.PATH_PREFIX}/{BLOCK_ID}/d41d8cd98f00b204e9800998ecf8427e.png",
                    "definition_image_path": f"{UPLOAD.PATH_PREFIX}/{BLOCK_ID}/other.png",
                }
            ],
        },
    )
    assert result["success"] is True
    card = xblock.cards[0]
    assert card["term_image_path"] == f"{UPLOAD.PATH_PREFIX}/{BLOCK_ID}/d41d8cd98f00b204e9800998ecf8427e.png"
    assert card["definition_image_path"] == f"{UPLOAD.PATH_PREFIX}/{BLOCK_ID}/other.png"


def test_save_settings_tolerates_cards_without_image_paths():
    """Content authored before this change has no *_image_path keys."""
    xblock = _make_block()
    CommonHandlers.save_settings(
        xblock,
        {
            "game_type": "flashcards",
            "cards": [{"term": "t", "definition": "d"}],
        },
    )
    assert xblock.cards[0]["term_image_path"] == ""


def test_save_settings_drops_keys_that_are_not_this_blocks():
    """A key for another block, a traversal, or a non-string is never persisted.

    The keys come from the client and are meant to drive a later cleanup, and
    the storage bucket is shared by the whole platform.
    """
    xblock = _make_block()
    CommonHandlers.save_settings(
        xblock,
        {
            "game_type": "flashcards",
            "cards": [
                {
                    "term": "t",
                    "definition": "d",
                    "term_image_path": f"{UPLOAD.PATH_PREFIX}/otherblock/x.png",
                    "definition_image_path": f"{UPLOAD.PATH_PREFIX}/{BLOCK_ID}/../x.png",
                },
                {"term": "t", "definition": "d", "term_image_path": "../../etc/passwd", "definition_image_path": 123},
            ],
        },
    )
    for card in xblock.cards:
        assert card["term_image_path"] == ""
        assert card["definition_image_path"] == ""


def test_save_settings_coerces_null_text_fields():
    """A null alt/image/definition from the editor must not break student_view for learners."""
    xblock = _make_block()
    result = CommonHandlers.save_settings(
        xblock,
        {
            "game_type": "flashcards",
            "cards": [{"term": "t", "definition": None, "term_image_alt": None, "definition_image": 5}],
        },
    )
    assert result["success"] is True
    assert xblock.cards[0]["definition"] == ""
    assert xblock.cards[0]["term_image_alt"] == ""
    assert xblock.cards[0]["definition_image"] == ""
    assert FlashcardsHandlers.student_view(xblock) is not None


def test_save_settings_rejects_invalid_game_type_and_non_bool_flags():
    """Bad input is refused before anything is written to the block."""
    xblock = _make_block()
    assert CommonHandlers.save_settings(xblock, {"game_type": "bogus", "cards": []})["success"] is False
    assert (
        CommonHandlers.save_settings(xblock, {"game_type": "flashcards", "is_shuffled": "no", "cards": []})["success"]
        is False
    )
    assert CommonHandlers.save_settings(xblock, {"game_type": "flashcards", "cards": "abc"})["success"] is False
    assert xblock.game_type == "flashcards"
    assert xblock.cards == [{"term": "a", "definition": "b"}]
    assert xblock.is_shuffled is True


def test_save_settings_null_display_name_falls_back_to_default():
    """The editor types display_name as ``string | null``; None must not be stored."""
    xblock = _make_block()
    result = CommonHandlers.save_settings(xblock, {"game_type": "flashcards", "display_name": None, "cards": []})
    assert result["success"] is True
    assert xblock.display_name == DEFAULT.DISPLAY_NAME
