"""
Unit tests for utils.py - Games XBlock utility functions.

Following Open edX testing standards with pytest and ddt.
"""

from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import default_storage

from xblock_games.utils import delete_image, get_gamesxblock_storage


@pytest.mark.django_db
class TestGetGamesxblockStorage:
    """Test cases for get_gamesxblock_storage function."""

    @patch("xblock_games.utils.settings")
    def test_returns_default_storage_when_no_settings(self, mock_settings):
        """Test returns default_storage when GAMESXBLOCK_STORAGE not configured."""
        mock_settings.GAMESXBLOCK_STORAGE = None

        result = get_gamesxblock_storage()

        assert result == default_storage

    @patch("xblock_games.utils.settings")
    @patch("xblock_games.utils.import_string")
    def test_returns_custom_storage_when_configured(self, mock_import_string, mock_settings):
        """Test returns custom storage when properly configured."""
        # Mock storage class and instance
        mock_storage_instance = Mock()
        mock_storage_class = Mock(return_value=mock_storage_instance)
        mock_import_string.return_value = mock_storage_class

        # Configure settings
        mock_settings.GAMESXBLOCK_STORAGE = {
            "storage_class": "myapp.storage.CustomStorage",
            "settings": {
                "bucket_name": "test-bucket",
                "location": "games/",
            },
        }

        result = get_gamesxblock_storage()

        mock_import_string.assert_called_once_with("myapp.storage.CustomStorage")
        mock_storage_class.assert_called_once_with(
            bucket_name="test-bucket",
            location="games/",
        )
        assert result == mock_storage_instance

    @patch("xblock_games.utils.settings")
    def test_raises_error_when_storage_class_missing(self, mock_settings):
        """Test raises ImproperlyConfigured when storage_class is missing."""
        mock_settings.GAMESXBLOCK_STORAGE = {"settings": {"bucket_name": "test-bucket"}}

        with pytest.raises(ImproperlyConfigured) as exc_info:
            get_gamesxblock_storage()

        assert "storage_class missing" in str(exc_info.value)

    @patch("xblock_games.utils.settings")
    @patch("xblock_games.utils.import_string")
    def test_raises_error_when_import_fails(self, mock_import_string, mock_settings):
        """Test raises ImproperlyConfigured when storage class import fails."""
        mock_import_string.side_effect = ImportError("Module not found")

        mock_settings.GAMESXBLOCK_STORAGE = {"storage_class": "nonexistent.storage.Class", "settings": {}}

        with pytest.raises(ImproperlyConfigured) as exc_info:
            get_gamesxblock_storage()

        assert "Failed importing storage class" in str(exc_info.value)

    @patch("xblock_games.utils.settings")
    @patch("xblock_games.utils.import_string")
    def test_raises_error_when_initialization_fails(self, mock_import_string, mock_settings):
        """Test raises ImproperlyConfigured when storage initialization fails."""
        mock_storage_class = Mock(side_effect=TypeError("Invalid arguments"))
        mock_import_string.return_value = mock_storage_class

        mock_settings.GAMESXBLOCK_STORAGE = {
            "storage_class": "myapp.storage.CustomStorage",
            "settings": {"invalid_param": "value"},
        }

        with pytest.raises(ImproperlyConfigured) as exc_info:
            get_gamesxblock_storage()

        assert "Failed initializing storage" in str(exc_info.value)

    @patch("xblock_games.utils.settings")
    @patch("xblock_games.utils.import_string")
    def test_handles_empty_settings_dict(self, mock_import_string, mock_settings):
        """Test handles empty or None settings dict."""
        mock_storage_instance = Mock()
        mock_storage_class = Mock(return_value=mock_storage_instance)
        mock_import_string.return_value = mock_storage_class

        # Test with None settings
        mock_settings.GAMESXBLOCK_STORAGE = {"storage_class": "myapp.storage.CustomStorage", "settings": None}

        result = get_gamesxblock_storage()

        mock_storage_class.assert_called_once_with()
        assert result == mock_storage_instance


@pytest.mark.django_db
class TestDeleteImage:
    """Test cases for delete_image function."""

    def test_deletes_existing_image(self):
        """Test successfully deletes an existing image."""
        mock_storage = Mock()
        mock_storage.exists.return_value = True

        result = delete_image(mock_storage, "path/to/image.jpg")

        mock_storage.exists.assert_called_once_with("path/to/image.jpg")
        mock_storage.delete.assert_called_once_with("path/to/image.jpg")
        assert result is True

    def test_returns_false_for_nonexistent_image(self):
        """Test returns False when image doesn't exist."""
        mock_storage = Mock()
        mock_storage.exists.return_value = False

        result = delete_image(mock_storage, "path/to/nonexistent.jpg")

        mock_storage.exists.assert_called_once_with("path/to/nonexistent.jpg")
        mock_storage.delete.assert_not_called()
        assert result is False

    def test_handles_empty_key(self):
        """Test handles empty key gracefully."""
        mock_storage = Mock()
        mock_storage.exists.return_value = False

        result = delete_image(mock_storage, "")

        mock_storage.exists.assert_called_once_with("")
        assert result is False

    def test_handles_special_characters_in_key(self):
        """Test handles keys with special characters."""
        mock_storage = Mock()
        mock_storage.exists.return_value = True

        special_key = "path/to/image with spaces & special-chars.jpg"
        result = delete_image(mock_storage, special_key)

        mock_storage.exists.assert_called_once_with(special_key)
        mock_storage.delete.assert_called_once_with(special_key)
        assert result is True


class TestReadResource:
    """read_resource loads the block's bundled static files without pkg_resources."""

    def test_reads_a_bundled_template(self):
        from xblock_games.utils import read_resource

        html = read_resource("static/html/flashcards.html")
        assert "<" in html and len(html) > 100

    def test_reads_every_file_the_views_need(self):
        from xblock_games.utils import read_resource

        for path in (
            "static/html/flashcards.html",
            "static/css/flashcards.css",
            "static/js/src/flashcards.js",
            "static/html/matching.html",
            "static/css/matching.css",
            "static/css/confetti.css",
            "static/js/src/matching.js",
            "static/js/src/confetti.js",
        ):
            assert read_resource(path), path

    def test_missing_file_raises(self):
        import pytest

        from xblock_games.utils import read_resource

        with pytest.raises(FileNotFoundError):
            read_resource("static/html/does-not-exist.html")
