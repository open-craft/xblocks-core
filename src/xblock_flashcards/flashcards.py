"""An XBlock for creating Flashcards."""

import json
import random
import string

from django.template import Context, Template
from django.utils.translation import gettext_lazy as _
from web_fragments.fragment import Fragment
from xblock.core import Response, XBlock
from xblock.fields import Boolean, List, Scope, String

from .utils import read_resource


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

    # this cannot be json_handler, because json_handler only supports POST requests
    @XBlock.handler
    def load_flashcards(self, *_args, **_kwargs):
        settings = {
            "cards": self.cards,
            "is_shuffled": self.is_shuffled,
            "display_name": self.display_name,
        }
        return Response(json.dumps(settings), content_type="application/json", charset="utf8")

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
