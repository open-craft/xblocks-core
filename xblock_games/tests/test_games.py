"""
Unit tests for games.py - GamesXBlock core functionality.

Following Open edX testing standards with pytest and ddt.
"""

import json
from unittest.mock import Mock, patch

import pytest
from xblock.field_data import DictFieldData
from xblock.fields import Scope
from xblock.test.tools import TestRuntime

from xblock_games.constants import DEFAULT, GAME_TYPE
from xblock_games.games import GamesXBlock


@pytest.mark.django_db
class TestGamesXBlock:
    """Test cases for GamesXBlock."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runtime = TestRuntime()
        self.field_data = DictFieldData(
            {
                "title": "Test Game",
                "game_type": GAME_TYPE.MATCHING,
                "cards": [],
                "is_shuffled": False,
                "has_timer": True,
            }
        )
        self.block = GamesXBlock(
            self.runtime,
            field_data=self.field_data,
            scope_ids=Mock(
                usage_id=Mock(block_id="test-block-id"),
                user_id="test-user-id",
            ),
        )

    def test_init_block(self):
        """Test that the XBlock initializes correctly."""
        assert self.block.title == "Test Game"
        assert self.block.game_type == GAME_TYPE.MATCHING
        assert self.block.cards == []
        assert self.block.is_shuffled is False
        assert self.block.has_timer is True

    def test_default_values(self):
        """Test default field values."""
        default_block = GamesXBlock(
            self.runtime,
            field_data=DictFieldData({}),
            scope_ids=Mock(
                usage_id=Mock(block_id="test-block-id"),
                user_id="test-user-id",
            ),
        )
        assert default_block.title == DEFAULT.FLASHCARDS_TITLE
        assert default_block.display_name == DEFAULT.DISPLAY_NAME
        assert default_block.game_type == DEFAULT.GAME_TYPE
        assert default_block.cards == []
        assert default_block.is_shuffled == DEFAULT.IS_SHUFFLED
        assert default_block.has_timer == DEFAULT.HAS_TIMER
        assert default_block.best_time is None

    @patch("xblock_games.handlers.matching.MatchingHandlers.student_view")
    def test_student_view_matching(self, mock_matching_view):
        """Test student_view routes to MatchingHandlers for matching game."""
        mock_fragment = Mock()
        mock_matching_view.return_value = mock_fragment

        self.block.game_type = GAME_TYPE.MATCHING
        result = self.block.student_view()

        mock_matching_view.assert_called_once()
        assert result == mock_fragment

    @patch("xblock_games.handlers.flashcards.FlashcardsHandlers.student_view")
    def test_student_view_flashcards(self, mock_flashcards_view):
        """Test student_view routes to FlashcardsHandlers for flashcards game."""
        mock_fragment = Mock()
        mock_flashcards_view.return_value = mock_fragment

        self.block.game_type = GAME_TYPE.FLASHCARDS
        result = self.block.student_view()

        mock_flashcards_view.assert_called_once()
        assert result == mock_fragment

    def test_workbench_scenarios(self):
        """Test workbench scenarios are defined."""
        scenarios = GamesXBlock.workbench_scenarios()
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        # Check structure of scenarios
        for scenario in scenarios:
            assert isinstance(scenario, tuple)
            assert len(scenario) == 2
            assert isinstance(scenario[0], str)  # Title
            assert isinstance(scenario[1], str)  # XML


@pytest.mark.django_db
class TestGamesXBlockHandlers:
    """Test XBlock handler methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runtime = TestRuntime()
        self.block = GamesXBlock(
            self.runtime,
            field_data=DictFieldData(
                {
                    "title": "Test Game",
                    "game_type": GAME_TYPE.MATCHING,
                    "cards": [
                        {
                            "term": "Test Term",
                            "definition": "Test Definition",
                            "term_image": "",
                            "definition_image": "",
                            "order": "0",
                            "card_key": "test-key-1",
                        }
                    ],
                }
            ),
            scope_ids=Mock(
                usage_id=Mock(block_id="test-block-id"),
                user_id="test-user-id",
            ),
        )

    @patch("xblock_games.handlers.common.CommonHandlers.get_settings")
    def test_get_settings_handler(self, mock_handler):
        """Test get_settings JSON handler delegates to CommonHandlers."""
        mock_handler.return_value = {
            "success": True,
            "game_type": GAME_TYPE.MATCHING,
            "cards": [],
        }

        # Create mock request with method and body attributes
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.body = json.dumps({}).encode("utf-8")

        result = self.block.get_settings(mock_request, "")

        # Verify the handler was called with correct arguments
        mock_handler.assert_called_once_with(self.block, {}, "")
        # Result is a Response object wrapping the mocked return value
        assert result.status == "200 OK"

    @patch("xblock_games.handlers.common.CommonHandlers.save_settings")
    def test_save_settings_handler(self, mock_handler):
        """Test save_settings JSON handler delegates to CommonHandlers."""
        mock_handler.return_value = {"success": True}

        data = {
            "game_type": GAME_TYPE.FLASHCARDS,
            "title": "New Title",
            "cards": [],
        }

        # Create mock request with method and body attributes
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.body = json.dumps(data).encode("utf-8")

        result = self.block.save_settings(mock_request, "")

        # Verify the handler was called
        mock_handler.assert_called_once()
        # Result is a Response object
        assert result.status == "200 OK"

    @patch("xblock_games.handlers.common.CommonHandlers.upload_image")
    def test_upload_image_handler(self, mock_handler):
        """Test upload_image handler."""
        mock_response = Mock()
        mock_response.status = 200
        mock_handler.return_value = mock_response

        mock_request = Mock()
        result = self.block.upload_image(mock_request, "")

        mock_handler.assert_called_once_with(self.block, mock_request, "")
        assert result == mock_response

    @patch("xblock_games.handlers.matching.MatchingHandlers.complete_matching_game")
    def test_complete_matching_game_handler(self, mock_handler):
        """Test complete_matching_game handler delegates to MatchingHandlers."""
        mock_handler.return_value = {
            "success": True,
            "is_best_time": True,
            "best_time": 30,
        }

        # Create mock request with method and body attributes
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.body = json.dumps({"time": 30}).encode("utf-8")

        result = self.block.complete_matching_game(mock_request, "")

        # Verify the handler was called
        mock_handler.assert_called_once()
        # Result is a Response object
        assert result.status == "200 OK"


@pytest.mark.django_db
class TestGamesXBlockFieldScopes:
    """Test field scopes and persistence."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runtime = TestRuntime()
        self.block = GamesXBlock(
            self.runtime,
            field_data=DictFieldData({}),
            scope_ids=Mock(
                usage_id=Mock(block_id="test-block-id"),
                user_id="test-user-id",
            ),
        )

    def test_title_is_content_scoped(self):
        """Test that title field has content scope."""
        assert self.block.fields["title"].scope == Scope.content

    def test_cards_is_content_scoped(self):
        """Test that cards field has content scope."""
        assert self.block.fields["cards"].scope == Scope.content

    def test_best_time_is_user_state_scoped(self):
        """Test that best_time field has user_state scope."""
        assert self.block.fields["best_time"].scope == Scope.user_state

    def test_game_type_is_settings_scoped(self):
        """Test that game_type field has settings scope."""
        assert self.block.fields["game_type"].scope == Scope.settings

    def test_is_shuffled_is_settings_scoped(self):
        """Test that is_shuffled field has settings scope."""
        assert self.block.fields["is_shuffled"].scope == Scope.settings

    def test_has_timer_is_settings_scoped(self):
        """Test that has_timer field has settings scope."""
        assert self.block.fields["has_timer"].scope == Scope.settings
