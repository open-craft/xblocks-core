"""Tests for the Flashcards Block"""

from unittest.mock import Mock, patch

import pytest
from django.utils.translation import override
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
    # The active language, which is LANGUAGE_CODE in the test settings.
    assert init_args["locale"] == "en-us"


@pytest.mark.parametrize(("language", "locale"), [("pt-br", "pt-br"), ("es-419", "es-419"), (None, "en")])
def test_render_passes_request_language(language, locale):
    """Test the student view passes the request's language to the frontend, or English without one."""
    block = make_block()
    with patch("xblock_flashcards.flashcards.get_language", return_value=language):
        frag = block.student_view().to_dict()

    assert frag["json_init_args"]["locale"] == locale


def test_render_passes_active_language():
    """Test the locale follows Django's active language."""
    block = make_block()
    with override("fr"):
        frag = block.student_view().to_dict()

    assert frag["json_init_args"]["locale"] == "fr"


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


def test_i18n_js_namespace():
    """Test the namespace of the JavaScript catalog matches the one the frontend reads."""
    assert FlashcardsXBlock.i18n_js_namespace == "XBlockFlashcardsI18N"
    assert FlashcardsXBlock.get_i18n_js_namespace() == "XBlockFlashcardsI18N"


def test_render_loads_i18n_js_catalog_before_block_js():
    """Test the student view adds the JavaScript catalog, when there is one, before the block's JS."""
    block = make_block()
    with patch("xblock.runtime.NullI18nService.get_javascript_i18n_catalog_url", return_value="/static/catalog.js"):
        frag = block.student_view()

    js = [r for r in frag.resources if r.mimetype == "application/javascript"]
    assert js[0].kind == "url"
    assert js[0].data == "/static/catalog.js"
    assert "function FlashCardsXBlock(" in js[1].data


@pytest.mark.parametrize("i18n_service", [Mock(get_javascript_i18n_catalog_url=Mock(return_value=None)), Mock(spec=[])])
def test_render_without_i18n_js_catalog(i18n_service):
    """Test no catalog is added when there is none, or the i18n service can't provide one."""
    block = make_block()
    block.runtime.service = Mock(return_value=i18n_service)

    frag = block.student_view()

    assert [r.kind for r in frag.resources] == ["text"]
