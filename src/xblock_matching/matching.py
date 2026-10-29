"""An XBlock providing a card matching game."""

import hashlib
import hmac
import json
import random
import secrets

from django.template import Context, Template
from django.utils.translation import gettext_lazy as _
from pydantic import ValidationError
from web_fragments.fragment import Fragment
from xblock.core import Response, XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Boolean, Integer, List, Scope, String

from .types import Card, Settings
from .utils import read_resource


class MatchingXBlock(XBlock):
    """
    An XBlock for creating a matching game.

    The Student view will display the game content and allow the student to interact
    accordingly.
    """

    display_name = String(
        default="Matching",
        scope=Scope.settings,
        help="Display name for this XBlock",
    )

    cards = List(default=[], scope=Scope.content, help=_("The list of terms and definitions."))

    best_time = Integer(
        default=None,
        scope=Scope.user_state,
        help=_("Best time (in seconds) for completing the matching game."),
    )

    is_shuffled = Boolean(
        default=True,
        scope=Scope.settings,
        help=_("Whether the cards should be shuffled"),
    )

    has_timer = Boolean(
        default=True,
        scope=Scope.settings,
        help=_("Whether the game should have a timer"),
    )

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        The primary view of the MatchingXBlock, shown to students when viewing courses.
        """
        cards = [Card(**card) for card in self.cards]
        list_length = len(cards)
        session_key = secrets.token_hex(32)

        matches_per_page = 5
        pages = []
        for i in range(0, len(cards), matches_per_page):
            page_cards = cards[i : i + matches_per_page]
            left_items = []
            right_items = []
            for card in page_cards:
                def_text = card.definition
                def_hash = hmac.new(session_key.encode(), def_text.encode(), hashlib.sha256).hexdigest()
                left_items.append(
                    {
                        "text": card.term,
                        "match": def_hash,
                    }
                )
                right_items.append({"text": def_text, "hash": def_hash})
            if self.is_shuffled:
                random.shuffle(left_items)
                random.shuffle(right_items)
            pages.append({"left_items": left_items, "right_items": right_items})

        total_pages = len(pages)

        template_context = {
            "title": self.display_name,
            "list_length": list_length,
            "all_pages": pages,
            "has_timer": self.has_timer,
            "total_pages": total_pages,
            "pages_json": pages,
            "block_id": self.scope_ids.usage_id.block_id,
        }

        template_str = read_resource("static/html/matching.html")
        template = Template(template_str)
        html = template.render(Context(template_context))

        frag = Fragment(html)
        frag.add_css(read_resource("static/css/matching.css"))
        frag.add_css(read_resource("static/css/confetti.css"))
        frag.add_javascript(read_resource("static/js/src/matching.js"))
        frag.add_javascript(read_resource("static/js/src/confetti.js"))
        frag.initialize_js("GamesXBlockMatchingInit")
        return frag

    @XBlock.json_handler
    def save_settings(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        Save game type, shuffle setting, and all cards in one API call.
        Expected data format:
        {
            'display_name': 'Block title',
            'is_shuffled': true or false,
            'has_timer': true or false,
            'cards': [
                {
                    'card_key': 'uuid (assigned here if missing)',
                    'term': 'Term 1',
                    'definition': 'Definition 1',
                },
                ...
            ]
        }
        """
        try:
            validated_data = Settings(**data)
        except ValidationError as e:
            raise JsonHandlerError(400, json.dumps(e.errors())) from e

        self.cards = [card.model_dump() for card in validated_data.cards]
        self.display_name = validated_data.display_name
        self.is_shuffled = validated_data.is_shuffled
        self.has_timer = validated_data.has_timer

        return {
            "success": True,
            "cards": self.cards,
            "count": len(self.cards),
            "is_shuffled": self.is_shuffled,
            "has_timer": self.has_timer,
        }

    @XBlock.json_handler
    def complete_matching_game(self, data, suffix=""):  # pylint: disable=unused-argument
        """Complete the matching game and compare the user's time to the best_time field."""
        new_time = data["new_time"]
        prev_best_time = self.best_time

        if prev_best_time is None or new_time < prev_best_time:
            self.best_time = new_time

        return {
            "new_time": new_time,
            "prev_best_time": prev_best_time,
        }

    @XBlock.handler
    def refresh_game(self, request, suffix=""):  # pylint: disable=unused-argument
        """Refresh the game view with new shuffled data."""
        frag = self.student_view(context=None)
        return Response(frag.content, content_type="text/html", charset="UTF-8")

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "Matching",
                """<openedx_matching/>
              """,
            ),
        ]
