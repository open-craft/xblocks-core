"""
Common handler methods for the Games XBlock.
"""

import base64
import hashlib
import json
import random
import string
import uuid

from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from xblock.core import Response

from ..constants import CARD_FIELD, CONFIG, DEFAULT, GAME_TYPE, UPLOAD
from ..utils import delete_image, get_gamesxblock_storage


class CommonHandlers:
    """Handlers that work across all game types."""

    @staticmethod
    def generate_unique_var_names(keys, min_len=3, max_len=6, max_attempts=1000):
        """
        Generate unique random variable names for obfuscation.
        """
        used = set()
        names = {}
        for key in keys:
            for _i in range(max_attempts):
                name = "".join(random.choices(string.ascii_lowercase, k=random.randint(min_len, max_len)))
                if name not in used:
                    used.add(name)
                    names[key] = name
                    break
            else:
                raise RuntimeError(
                    f"Unable to generate a unique variable name after {max_attempts} attempts. "
                    "Consider increasing min_len/max_len."
                )
        return names

    @staticmethod
    def generate_encryption_key(xblock):
        """
        Generate encryption key using block_id and salt.
        Uses a consistent identifier that doesn't change across requests.

        Args:
            xblock: The xblock instance

        Returns:
            Base64-encoded encryption key (bytes)
        """
        # Use block_id (which is stable) and the encryption salt
        block_id = str(xblock.scope_ids.usage_id.block_id)
        seed_string = f"{block_id}:{CONFIG.ENCRYPTION_SALT}"

        # Generate a 32-byte key using SHA-256
        key_bytes = hashlib.sha256(seed_string.encode()).digest()

        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key_bytes)

    @staticmethod
    def encrypt_data(data, encryption_key):
        """
        Encrypt data using Fernet (symmetric encryption).

        Args:
            data: Dictionary or any JSON-serializable data to encrypt
            encryption_key: Base64-encoded encryption key

        Returns:
            Base64-encoded encrypted string
        """
        fernet = Fernet(encryption_key)
        data_json = json.dumps(data)
        encrypted_data = fernet.encrypt(data_json.encode())
        return encrypted_data.decode()

    @staticmethod
    def decrypt_data(encrypted_hash, encryption_key):
        """
        Decrypt encrypted data back to original format.

        Args:
            encrypted_hash: Base64-encoded encrypted string
            encryption_key: Base64-encoded encryption key

        Returns:
            Decrypted data (dictionary or original data structure)
        """
        fernet = Fernet(encryption_key)
        # Fernet.decrypt expects bytes (base64-encoded), so just encode the string
        decrypted_json = fernet.decrypt(encrypted_hash.encode()).decode()
        return json.loads(decrypted_json)

    @staticmethod
    def get_settings(xblock, data, suffix=""):
        """Get game type, cards, and shuffle setting in one call."""
        return {
            "game_type": xblock.game_type,
            "cards": xblock.cards,
            "is_shuffled": xblock.is_shuffled,
            "has_timer": xblock.has_timer,
        }

    @staticmethod
    def upload_image(xblock, request, suffix=""):
        """
        Upload an image file to configured storage (S3 if set) and return URL.
        """
        asset_storage = get_gamesxblock_storage()
        try:
            upload_file = request.params["file"].file
            file_name = request.params["file"].filename
            if "." not in file_name:
                return Response(
                    json_body={
                        "success": False,
                        "error": "File must have an extension",
                    },
                    status=400,
                )
            _stem, ext = file_name.rsplit(".", 1)
            ext = ext.lower()
            if ext not in UPLOAD.ALLOWED_EXTENSIONS:
                return Response(
                    json_body={
                        "success": False,
                        "error": (
                            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(UPLOAD.ALLOWED_EXTENSIONS))}"
                        ),
                    },
                    status=400,
                )
            blob = upload_file.read()
            file_hash = hashlib.md5(blob).hexdigest()
            file_path = f"{UPLOAD.PATH_PREFIX}/{xblock.scope_ids.usage_id.block_id}/{file_hash}.{ext}"
            saved_path = asset_storage.save(file_path, ContentFile(blob))
            file_url = asset_storage.url(saved_path)
            return Response(
                json_body={
                    "success": True,
                    "url": file_url,
                    "filename": file_name,
                    "file_path": saved_path,
                }
            )
        except Exception as e:
            return Response(json_body={"success": False, "error": str(e)}, status=400)

    @staticmethod
    def delete_image_handler(xblock, data, suffix=""):
        """
        Delete an image by storage key.
        Expected: { "key": "games/<block_id>/<hash>.ext" }

        Only keys this block created through ``upload_image`` are accepted; the
        storage bucket is shared platform-wide.
        """
        raw_key = data.get("key")
        if not raw_key:
            return {"success": False, "error": "Missing key"}
        key = CommonHandlers.own_storage_key(xblock, raw_key)
        if not key:
            return {"success": False, "error": _("Key does not belong to this block")}
        try:
            storage = get_gamesxblock_storage()
            is_deleted = delete_image(storage, key)
            return {"success": is_deleted, "key": key}
        except Exception:  # pylint: disable=broad-exception-caught
            return {"success": False, "error": _("Delete failed")}

    @staticmethod
    def own_storage_key(xblock, key):
        """
        Return ``key`` only if it is a storage key this block created through
        ``upload_image`` (``<UPLOAD.PATH_PREFIX>/<block_id>/<file>``); otherwise "".

        The client supplies these keys and they are meant to drive a later
        cleanup/delete, so a key pointing at another block's file (or any
        arbitrary storage path) must not be persisted.
        """
        if not isinstance(key, str) or not key:
            return ""
        prefix = f"{UPLOAD.PATH_PREFIX}/{xblock.scope_ids.usage_id.block_id}/"
        name = key[len(prefix) :]
        if not key.startswith(prefix) or not name or "/" in name or "\\" in name or name in (".", ".."):
            return ""
        if name.rsplit(".", 1)[-1].lower() not in UPLOAD.ALLOWED_EXTENSIONS:
            return ""
        return key

    @staticmethod
    def text_field(value, default=""):
        """
        Return ``value`` if it is a string, else ``default``.

        Card text fields come from the client; a ``null`` or non-string value
        stored here makes ``student_view`` raise for every learner
        (``.strip()`` / ``.encode()`` on ``None``), so coerce at the boundary.
        """
        return value if isinstance(value, str) else default

    @staticmethod
    def save_settings(xblock, data, suffix=""):
        """
        Save game type, shuffle setting, and all cards in one API call.
        Expected data format:
        {
            'display_name': 'Block title',
            'game_type': 'flashcards' or 'matching',
            'is_shuffled': true or false,
            'has_timer': true or false,
            'cards': [
                {
                    'term': 'Term 1',
                    'definition': 'Definition 1',
                    'order': 1,
                    'card_key': 'uuid (assigned here if missing)',
                    'term_image': 'http://...',
                    'term_image_path': 'games/<block_id>/<hash>.ext',
                    'term_image_alt': 'alt text',
                    'definition_image': 'http://...',
                    'definition_image_path': 'games/<block_id>/<hash>.ext',
                    'definition_image_alt': 'alt text'
                },
                ...
            ]
        }
        """
        try:
            new_game_type = data.get("game_type", GAME_TYPE.FLASHCARDS)
            if new_game_type not in GAME_TYPE.VALID:
                return {"success": False, "error": _("Invalid game type")}
            new_is_shuffled = data.get("is_shuffled", DEFAULT.IS_SHUFFLED)
            new_has_timer = data.get("has_timer", DEFAULT.HAS_TIMER)
            if not isinstance(new_is_shuffled, bool) or not isinstance(new_has_timer, bool):
                return {"success": False, "error": _("is_shuffled and has_timer must be booleans")}
            new_cards = data.get("cards", [])
            if not isinstance(new_cards, list):
                return {"success": False, "error": _("cards must be a list")}
            display_name = CommonHandlers.text_field(data.get("display_name"), DEFAULT.DISPLAY_NAME)

            validated_cards = []
            for card in new_cards:
                if not isinstance(card, dict):
                    return {"success": False, "error": _("Each card must be an object")}

                # Validate required fields
                if CARD_FIELD.TERM not in card or CARD_FIELD.DEFINITION not in card:
                    return {
                        "success": False,
                        "error": _("Each card must have term and definition"),
                    }

                validated_cards.append(
                    {
                        CARD_FIELD.TERM: CommonHandlers.text_field(card.get(CARD_FIELD.TERM)),
                        CARD_FIELD.TERM_IMAGE: CommonHandlers.text_field(card.get(CARD_FIELD.TERM_IMAGE)),
                        CARD_FIELD.DEFINITION: CommonHandlers.text_field(card.get(CARD_FIELD.DEFINITION)),
                        CARD_FIELD.DEFINITION_IMAGE: CommonHandlers.text_field(card.get(CARD_FIELD.DEFINITION_IMAGE)),
                        CARD_FIELD.ORDER: card.get(CARD_FIELD.ORDER, ""),
                        CARD_FIELD.CARD_KEY: CommonHandlers.text_field(
                            card.get(CARD_FIELD.CARD_KEY), str(uuid.uuid4())
                        ),
                        CARD_FIELD.TERM_IMAGE_ALT: CommonHandlers.text_field(card.get(CARD_FIELD.TERM_IMAGE_ALT)),
                        CARD_FIELD.DEFINITION_IMAGE_ALT: CommonHandlers.text_field(
                            card.get(CARD_FIELD.DEFINITION_IMAGE_ALT)
                        ),
                        # Storage keys: where each image's file lives, as opposed to
                        # the URL it is shown from. Kept so the block knows which file
                        # belongs to a card (a cleanup of unused files needs that).
                        CARD_FIELD.TERM_IMAGE_PATH: CommonHandlers.own_storage_key(
                            xblock, card.get(CARD_FIELD.TERM_IMAGE_PATH, "")
                        ),
                        CARD_FIELD.DEFINITION_IMAGE_PATH: CommonHandlers.own_storage_key(
                            xblock, card.get(CARD_FIELD.DEFINITION_IMAGE_PATH, "")
                        ),
                    }
                )

            xblock.display_name = display_name
            if new_game_type == GAME_TYPE.FLASHCARDS:
                xblock.title = DEFAULT.FLASHCARDS_TITLE
            else:
                xblock.title = DEFAULT.MATCHING_TITLE
            xblock.cards = validated_cards
            xblock.game_type = new_game_type
            xblock.is_shuffled = new_is_shuffled
            xblock.has_timer = new_has_timer
            xblock.list_length = len(validated_cards)

            xblock.save()

            return {
                "success": True,
                "game_type": xblock.game_type,
                "cards": xblock.cards,
                "count": len(xblock.cards),
                "is_shuffled": xblock.is_shuffled,
                "has_timer": xblock.has_timer,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def format_as_uuid_like(key_hex, index):
        """
        Format key and index as UUID-like string for maximum obfuscation.
        Format: key-index_part1-rand4-index_part2-rand12

        Args:
            key_hex: 8-char hex string (key)
            index: integer index

        Returns:
            UUID-like formatted string (36 chars total: 8-4-4-4-12)
        """
        index_hex = format(index, "08x")
        index_part1 = index_hex[:4]
        index_part2 = index_hex[4:]
        rand_4 = format(random.getrandbits(16), "04x")
        rand_12 = format(random.getrandbits(48), "012x")
        return f"{key_hex}-{index_part1}-{rand_4}-{index_part2}-{rand_12}"
