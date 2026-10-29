"""An XBlock providing a pair matching game."""

import hashlib
import hmac
import json
import random
import secrets

from django.template import Context, Template
from django.utils.translation import gettext_noop as _
from web_fragments.fragment import Fragment
from xblock.core import Response, XBlock
from xblock.fields import Boolean, Integer, List, Scope, String

from .types import Pair, Settings
from .utils import read_resource


@XBlock.needs("i18n")
class MatchingXBlock(XBlock):
    """
    An XBlock for creating a matching game.

    The Student view will display the game content and allow the student to interact
    accordingly.
    """

    display_name = String(
        default=_("Matching"),
        scope=Scope.settings,
        help=_("Display name for this XBlock"),
    )

    pairs = List(default=[], scope=Scope.content, help=_("The list of card pairs."))

    best_time = Integer(
        default=None,
        scope=Scope.user_state,
        help=_("Best time (in seconds) for completing the matching game."),
    )

    is_shuffled = Boolean(
        default=True,
        scope=Scope.settings,
        help=_("Whether the pairs should be shuffled"),
    )

    has_timer = Boolean(
        default=True,
        scope=Scope.settings,
        help=_("Whether the game should have a timer"),
    )

    # NOTE: the student view will be rewritten soon in react
    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        The primary view of the MatchingXBlock, shown to students when viewing courses.
        """
        pairs = [Pair(**pair) for pair in self.pairs]
        session_key = secrets.token_hex(32)

        matches_per_page = 5
        pages = []
        for i in range(0, len(pairs), matches_per_page):
            page_pairs = pairs[i : i + matches_per_page]
            left_items = []
            right_items = []
            for pair in page_pairs:
                right_text = pair.right.text
                right_hash = hmac.new(session_key.encode(), right_text.encode(), hashlib.sha256).hexdigest()
                left_items.append(
                    {
                        "text": pair.left.text,
                        "match": right_hash,
                    }
                )
                right_items.append({"text": right_text, "hash": right_hash})
            if self.is_shuffled:
                random.shuffle(left_items)
                random.shuffle(right_items)
            pages.append({"left_items": left_items, "right_items": right_items})

        total_pages = len(pages)

        template_context = {
            "title": self.display_name,
            "list_length": len(pairs),
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

    # this cannot be json_handler, because json_handler only supports POST requests
    @XBlock.handler
    def load_data(self, *_args, **_kwargs):
        """
        Respond with a json representation of the block.
        """
        settings = Settings(
            pairs=self.pairs,
            is_shuffled=self.is_shuffled,
            has_timer=self.has_timer,
            display_name=self.display_name,
        )
        return Response(json.dumps(settings.model_dump()), content_type="application/json", charset="utf8")

    @XBlock.json_handler
    def complete_matching_game(self, data, suffix=""):  # pylint: disable=unused-argument
        """Complete the matching game and compare the user's time to the best_time field."""
        new_time = int(data["new_time"])
        prev_best_time = self.best_time

        if prev_best_time is None or new_time < prev_best_time:
            self.best_time = new_time

        return {
            "new_time": new_time,
            "prev_best_time": prev_best_time,
        }

    # NOTE: this will not be required when the frontend is re-implemented in react
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
