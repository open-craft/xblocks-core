"""An XBlock for creating Flashcards."""

import hashlib
import json
import random
import string

from django.core.files.base import ContentFile
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError
from web_fragments.fragment import Fragment
from xblock.core import Response, XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, List, Scope, String

from .types import Settings
from .utils import (
    get_block_storage,
    read_resource,
)

UPLOAD_PATH_PREFIX = "openedx_flashcards"
UPLOAD_ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp", "svg")


class FlashcardsXBlock(XBlock):
    """
    An XBlock for creating flashcards.

    The Student view will display the game content and allow the student to interact
    accordingly.
    """

    display_name = String(
        default="Flashcards",
        scope=Scope.settings,
        help="Display name for this XBlock",
    )

    cards = List(
        default=[],
        scope=Scope.content,
        help=_("The list of terms and definitions."),
    )

    is_shuffled = Boolean(
        default=True,
        scope=Scope.settings,
        help=_("Whether the cards should be shuffled"),
    )

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        The student view for flashcards game.
        """
        cards = random.sample(self.cards, k=len(self.cards)) if self.is_shuffled else self.cards

        # to avoid conflicts with other instances of the flashcards block on the same page
        # NOTE: these unique names and the init function shim won't be necessary when the frontend is ported to React
        unique_prefix = "".join(random.choices(string.ascii_lowercase, k=16))
        init_function_name = f"{unique_prefix}_OpenedXFlashcardsInit"
        data_element_id = f"{unique_prefix}_flashcards_data"

        init_function = (
            f"function {init_function_name}(runtime, element){{"
            f"  var cards = JSON.parse($('#{data_element_id}', element).text());"
            "   OpenedXFlashcardsInit(runtime, element, cards);"
            "}"
        )

        template_context = {
            "title": self.display_name,
            "cards": json.dumps(cards),
            "n_cards": len(cards),
            "data_element_id": data_element_id,
        }

        template_str = read_resource("static/html/flashcards.html")
        template = Template(template_str)
        html = template.render(Context(template_context))

        frag = Fragment(html)
        frag.add_css(read_resource("static/css/flashcards.css"))
        frag.add_javascript(read_resource("static/js/src/flashcards.js"))
        frag.add_javascript(init_function)
        frag.initialize_js(init_function_name)
        return frag

    @XBlock.handler
    def upload_image(self, request, suffix=""):  # pylint: disable=unused-argument
        """
        Upload an image file to configured storage (S3 if set) and return URL.
        """
        asset_storage = get_block_storage()
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
            if ext not in UPLOAD_ALLOWED_EXTENSIONS:
                return Response(
                    json_body={
                        "success": False,
                        "error": (
                            f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(UPLOAD_ALLOWED_EXTENSIONS))}"
                        ),
                    },
                    status=400,
                )
            blob = upload_file.read()
            file_hash = hashlib.md5(blob).hexdigest()
            file_path = f"{UPLOAD_PATH_PREFIX}/{self.scope_ids.usage_id.block_id}/{file_hash}.{ext}"
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
        except Exception as e:  # pylint: disable=broad-exception-caught
            return Response(json_body={"success": False, "error": str(e)}, status=400)

    @XBlock.json_handler
    def delete_image_handler(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        Delete an image by storage key.
        Expected: { "key": "games/<block_id>/<hash>.ext" }

        Only keys this block created through ``upload_image`` are accepted; the
        storage bucket is shared platform-wide.
        """
        raw_key = data.get("key")
        if not raw_key:
            return {"success": False, "error": "Missing key"}
        key = self.own_storage_key(raw_key)
        if not key:
            return {"success": False, "error": _("Key does not belong to this block")}
        try:
            storage = get_block_storage()
            if storage.exists(key):
                storage.delete(key)
                is_deleted = True
            else:
                is_deleted = False
            return {"success": is_deleted, "key": key}
        except Exception:  # pylint: disable=broad-exception-caught
            return {"success": False, "error": _("Delete failed")}

    @XBlock.json_handler
    def save_settings(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        Save game type, shuffle setting, and all cards in one API call.

        See the `Settings` pydantic model for expected data format.
        """
        try:
            validated_data = Settings(**data)
        except ValidationError as e:
            raise JsonHandlerError(400, json.dumps(e.errors())) from e

        cards = []
        for card in validated_data.cards:
            # Storage keys: where each image's file lives, as opposed to
            # the URL it is shown from. Kept so the block knows which file
            # belongs to a card (a cleanup of unused files needs that).
            card.term_image_path = self.own_storage_key(card.term_image_path)
            card.definition_image_path = self.own_storage_key(card.definition_image_path)

            cards.append(card.model_dump())

        self.cards = cards
        self.display_name = validated_data.display_name
        self.is_shuffled = validated_data.is_shuffled

        self.save()

        return {
            "success": True,
            "cards": self.cards,
            "count": len(self.cards),
            "is_shuffled": self.is_shuffled,
        }

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "Flashcards",
                """<openedx_flashcards/>
              """,
            ),
        ]

    def own_storage_key(self, key):
        """
        Return ``key`` only if it is a storage key this block created through
        ``upload_image`` (``<UPLOAD_PATH_PREFIX>/<block_id>/<file>``); otherwise "".

        The client supplies these keys and they are meant to drive a later
        cleanup/delete, so a key pointing at another block's file (or any
        arbitrary storage path) must not be persisted.
        """
        if not isinstance(key, str) or not key:
            return ""
        prefix = f"{UPLOAD_PATH_PREFIX}/{self.scope_ids.usage_id.block_id}/"
        name = key[len(prefix) :]
        if not key.startswith(prefix) or not name or "/" in name or "\\" in name or name in (".", ".."):
            return ""
        if name.rsplit(".", 1)[-1].lower() not in UPLOAD_ALLOWED_EXTENSIONS:
            return ""
        return key
