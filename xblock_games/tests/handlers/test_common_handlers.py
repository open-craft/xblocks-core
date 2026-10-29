"""
Tests for common handlers.
"""

import json
from unittest.mock import Mock, patch

from django.test import TestCase
from faker import Faker
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xblock_games.constants import GAME_TYPE
from xblock_games.games import GamesXBlock
from xblock_games.handlers.common import CommonHandlers


class TestCommonHandlers(TestCase):
    """Tests for common handler methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake = Faker()
        self.runtime = Mock()
        usage_id = Mock()
        usage_id.block_id = self.fake.uuid4()
        self.scope_ids = ScopeIds(self.fake.uuid4(), "games", self.fake.uuid4(), usage_id)
        self.field_data = DictFieldData(
            {
                "game_type": GAME_TYPE.FLASHCARDS,
                "cards": [],
                "is_shuffled": self.fake.boolean(),
                "has_timer": self.fake.boolean(),
                "display_name": self.fake.catch_phrase(),
            }
        )
        self.xblock = GamesXBlock(self.runtime, self.field_data, self.scope_ids)

    # Tests for generate_unique_var_names
    def test_generate_unique_var_names(self):
        """Test generating unique variable names for obfuscation."""
        keys = [self.fake.word(), self.fake.word(), self.fake.word()]
        names = CommonHandlers.generate_unique_var_names(keys)

        self.assertEqual(len(names), 3)
        for key in keys:
            self.assertIn(key, names)

        # Check all names are unique
        values = list(names.values())
        self.assertEqual(len(values), len(set(values)))

        # Check name lengths
        for name in values:
            self.assertGreaterEqual(len(name), 3)
            self.assertLessEqual(len(name), 6)
            self.assertTrue(name.islower())

    # Tests for generate_encryption_key
    def test_generate_encryption_key(self):
        """Test encryption key generation."""
        key = CommonHandlers.generate_encryption_key(self.xblock)

        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 44)  # Base64-encoded 32-byte key

    # Tests for encrypt_data and decrypt_data
    def test_encrypt_decrypt_data(self):
        """Test encrypting and decrypting data."""
        key = CommonHandlers.generate_encryption_key(self.xblock)
        original_data = {"term": self.fake.word(), "definition": self.fake.sentence(), "index": self.fake.random_int()}

        encrypted = CommonHandlers.encrypt_data(original_data, key)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, json.dumps(original_data))

        decrypted = CommonHandlers.decrypt_data(encrypted, key)
        self.assertEqual(decrypted, original_data)

    # Tests for get_settings
    def test_get_settings(self):
        """Test getting game settings."""
        self.xblock.game_type = GAME_TYPE.MATCHING
        cards = [{"term": self.fake.word(), "definition": self.fake.word()}]
        is_shuffled = self.fake.boolean()
        has_timer = self.fake.boolean()
        self.xblock.cards = cards
        self.xblock.is_shuffled = is_shuffled
        self.xblock.has_timer = has_timer

        result = CommonHandlers.get_settings(self.xblock, {})

        self.assertEqual(result["game_type"], GAME_TYPE.MATCHING)
        self.assertEqual(result["cards"], cards)
        self.assertEqual(result["is_shuffled"], is_shuffled)
        self.assertEqual(result["has_timer"], has_timer)

    # Tests for upload_image
    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    def test_upload_image_success(self, mock_get_storage):
        """Test successful image upload."""
        mock_storage = Mock()
        image_path = self.fake.file_path(extension="jpg")
        image_url = self.fake.image_url()
        mock_storage.save.return_value = image_path
        mock_storage.url.return_value = image_url
        mock_get_storage.return_value = mock_storage

        mock_file = Mock()
        mock_file.read.return_value = self.fake.binary(length=100)

        filename = self.fake.file_name(extension="jpg")
        mock_file_obj = Mock()
        mock_file_obj.file = mock_file
        mock_file_obj.filename = filename

        request = Mock()
        request.params = {"file": mock_file_obj}

        response = CommonHandlers.upload_image(self.xblock, request)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.body.decode())
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["url"], image_url)
        self.assertEqual(response_data["filename"], filename)

    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    def test_upload_image_returns_the_key_storage_used(self, mock_get_storage):
        """Storage may rename on collision; the key handed back must be the real one."""
        mock_storage = Mock()
        mock_storage.save.return_value = f"games/{self.scope_ids.usage_id.block_id}/renamed_by_storage.png"
        mock_storage.url.return_value = "http://example.com/renamed_by_storage.png"
        mock_get_storage.return_value = mock_storage
        mock_file = Mock()
        mock_file.read.return_value = b"bytes"
        upload = Mock()
        upload.file = mock_file
        upload.filename = "image.png"
        request = Mock()
        request.params = {"file": upload}

        response = CommonHandlers.upload_image(self.xblock, request)

        body = json.loads(response.body)
        self.assertTrue(body["success"])
        self.assertEqual(body["file_path"], mock_storage.save.return_value)

    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    def test_upload_image_no_extension(self, mock_get_storage):
        """Test upload fails when file has no extension."""
        mock_file_obj = Mock()
        mock_file_obj.file = Mock()
        mock_file_obj.filename = self.fake.word()

        request = Mock()
        request.params = {"file": mock_file_obj}

        response = CommonHandlers.upload_image(self.xblock, request)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.body.decode())
        self.assertFalse(response_data["success"])
        self.assertIn("extension", response_data["error"])

    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    def test_upload_image_invalid_extension(self, mock_get_storage):
        """Test upload fails with unsupported file type."""
        mock_file_obj = Mock()
        mock_file_obj.file = Mock()
        mock_file_obj.filename = self.fake.file_name(extension="exe")

        request = Mock()
        request.params = {"file": mock_file_obj}

        response = CommonHandlers.upload_image(self.xblock, request)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.body.decode())
        self.assertFalse(response_data["success"])
        self.assertIn("Unsupported file type", response_data["error"])

    # Tests for save_settings
    def test_save_settings_flashcards(self):
        """Test saving settings for flashcards game."""
        display_name = self.fake.catch_phrase()
        data = {
            "game_type": GAME_TYPE.FLASHCARDS,
            "is_shuffled": self.fake.boolean(),
            "has_timer": self.fake.boolean(),
            "display_name": display_name,
            "cards": [
                {"term": self.fake.word(), "definition": self.fake.sentence()},
                {"term": self.fake.word(), "definition": self.fake.sentence()},
            ],
        }

        result = CommonHandlers.save_settings(self.xblock, data)

        self.assertTrue(result["success"])
        self.assertEqual(self.xblock.game_type, GAME_TYPE.FLASHCARDS)
        self.assertEqual(self.xblock.display_name, display_name)
        self.assertEqual(self.xblock.is_shuffled, data["is_shuffled"])
        self.assertEqual(self.xblock.has_timer, data["has_timer"])
        self.assertEqual(len(self.xblock.cards), 2)
        self.assertEqual(self.xblock.list_length, 2)

    def test_save_settings_matching(self):
        """Test saving settings for matching game."""
        data = {
            "game_type": GAME_TYPE.MATCHING,
            "is_shuffled": self.fake.boolean(),
            "has_timer": self.fake.boolean(),
            "display_name": self.fake.catch_phrase(),
            "cards": [
                {"term": self.fake.word(), "definition": self.fake.sentence()},
            ],
        }

        result = CommonHandlers.save_settings(self.xblock, data)

        self.assertTrue(result["success"])
        self.assertEqual(self.xblock.game_type, GAME_TYPE.MATCHING)
        self.assertEqual(result["count"], 1)

    def test_save_settings_missing_required_fields(self):
        """Test save fails when cards missing required fields."""
        data = {
            "game_type": GAME_TYPE.FLASHCARDS,
            "cards": [
                {"term": self.fake.word()},  # Missing definition
            ],
        }

        result = CommonHandlers.save_settings(self.xblock, data)

        self.assertFalse(result["success"])
        self.assertIn("term and definition", result["error"])

    def test_save_settings_invalid_card_format(self):
        """Test save fails when card is not a dictionary."""
        data = {"game_type": GAME_TYPE.FLASHCARDS, "cards": [self.fake.sentence()]}

        result = CommonHandlers.save_settings(self.xblock, data)

        self.assertFalse(result["success"])
        self.assertIn("object", result["error"])

    # Tests for format_as_uuid_like
    def test_format_as_uuid_like(self):
        """Test UUID-like formatting for obfuscation."""
        key_hex = self.fake.hexify(text="^^^^^^^^", upper=False)
        index = self.fake.random_int(min=0, max=1000)

        result = CommonHandlers.format_as_uuid_like(key_hex, index)

        # Check format: 8-4-4-4-12 (36 chars + 4 hyphens = 40 chars with hyphens)
        parts = result.split("-")
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)

        # First part should be the key
        self.assertEqual(parts[0], key_hex)

    # Tests for delete_image_handler
    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    @patch("xblock_games.handlers.common.delete_image")
    def test_delete_image_handler_success(self, mock_delete, mock_get_storage):
        """Test successful image deletion."""
        mock_delete.return_value = True
        mock_storage = Mock()
        mock_get_storage.return_value = mock_storage

        image_key = f"games/{self.scope_ids.usage_id.block_id}/{self.fake.md5()}.jpg"
        data = {"key": image_key}
        result = CommonHandlers.delete_image_handler(self.xblock, data)

        self.assertTrue(result["success"])
        self.assertEqual(result["key"], image_key)
        mock_delete.assert_called_once_with(mock_storage, image_key)

    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    @patch("xblock_games.handlers.common.delete_image")
    def test_delete_image_handler_rejects_key_of_another_block(self, mock_delete, mock_get_storage):
        """The bucket is shared platform-wide; only this block's own keys may be deleted."""
        for bad_key in (
            "games/otherblock/abc.jpg",
            f"games/{self.scope_ids.usage_id.block_id}/../abc.jpg",
            f"games/{self.scope_ids.usage_id.block_id}/notes.txt",
            self.fake.file_path(extension="jpg"),
        ):
            result = CommonHandlers.delete_image_handler(self.xblock, {"key": bad_key})
            self.assertFalse(result["success"], bad_key)
        mock_delete.assert_not_called()

    @patch("xblock_games.handlers.common.get_gamesxblock_storage")
    def test_delete_image_handler_missing_key(self, mock_get_storage):
        """Test delete fails when key is missing."""
        data = {}
        result = CommonHandlers.delete_image_handler(self.xblock, data)

        self.assertFalse(result["success"])
        self.assertIn("Missing key", result["error"])
