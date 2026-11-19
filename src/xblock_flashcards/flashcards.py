"""An XBlock for creating Flashcards."""

import json

from django.utils.translation import gettext_noop as _
from web_fragments.fragment import Fragment
from xblock.core import Response, XBlock
from xblock.fields import Boolean, List, Scope, String

from .types import Settings
from .utils import read_resource


@XBlock.needs("i18n")
class FlashcardsXBlock(XBlock):
    """
    An XBlock for creating flashcards.

    The Student view will display the game content and allow the student to interact
    accordingly.
    """

    display_name = String(
        default=_("Flashcards"),
        scope=Scope.settings,
        help=_("Display name for this XBlock"),
    )

    cards = List(
        default=[],
        scope=Scope.content,
        help=_("The list of double sided flashcards."),
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
        frag = Fragment()
        frag.add_javascript(read_resource("static/js/render.js"))
        frag.initialize_js(
            "FlashCardsXBlock",
            {
                "url": self.runtime.local_resource_url(self, "public/flashcards.js"),
                "data": {
                    "display_name": self.display_name,
                    "is_shuffled": self.is_shuffled,
                    "cards": self.cards,
                },
            },
        )
        return frag

    # this cannot be json_handler, because json_handler only supports POST requests
    @XBlock.handler
    def load_data(self, *_args, **_kwargs):
        """
        Respond with a json representation of the block.
        """
        settings = Settings(
            cards=self.cards,
            is_shuffled=self.is_shuffled,
            display_name=self.display_name,
        )
        return Response(json.dumps(settings.model_dump()), content_type="application/json", charset="utf8")

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
