"""pdfXBlock main Python class."""

import json
from logging import getLogger
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_noop as _
from requests import HTTPError, Timeout
from web_fragments.fragment import Fragment
from webob import Response
from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.utils.resources import ResourceLoader

from .utils import (
    add_asset,
    convert_to_pdf,
    error_response,
    fetch_source_asset,
    is_all_download_disabled,
    is_gotenberg_enabled,
)

resource_loader = ResourceLoader(__name__)

logger = getLogger(__name__)


@XBlock.needs("i18n", "user")
@XBlock.wants("studio_user_permissions")
class PDFBlock(XBlock):
    """PDF XBlock. Allows authors to embed PDFs in their courses."""

    icon_class = "other"

    display_name = String(
        display_name=_("Display Name"),
        default=_("PDF"),
        scope=Scope.settings,
        help=_("This name appears in the horizontal navigation at the top of the page."),
    )

    url = String(
        display_name=_("PDF URL"),
        default=_("https://tutorial.math.lamar.edu/pdf/Trig_Cheat_Sheet.pdf"),
        scope=Scope.content,
        help=_("The URL for your PDF."),
    )

    allow_download = Boolean(
        display_name=_("PDF Download Allowed"),
        default=True,
        scope=Scope.content,
        help=_("Display a download button for this PDF."),
    )

    source_text = String(
        display_name=_("Source document button text"),
        default="",
        scope=Scope.content,
        help=_(
            "Add a download link for the source file of your PDF. "
            "Use it for example to provide the PowerPoint file used to create this PDF."
        ),
    )

    source_url = String(
        display_name=_("Source document URL"),
        default="",
        scope=Scope.content,
        help=_(
            "Add a download link for the source file of your PDF. "
            "Use it for example to provide the PowerPoint file used to create this PDF."
        ),
    )

    @property
    def raw_settings(self):
        """Get the raw settings of the XBlock as a dictionary."""
        return {
            "display_name": self.display_name,
            "url": self.url,
            "allow_download": self.allow_download,
            "disable_all_download": is_all_download_disabled(),
            "conversion_available": is_gotenberg_enabled(),
            "source_text": self.source_text,
            "source_url": self.source_url,
        }

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """Primary view of the XBlock, shown to students when viewing courses."""
        html = resource_loader.render_django_template(
            "templates/html/pdf.html",
            context=self.raw_settings,
            i18n_service=self.runtime.service(self, "i18n"),
        )

        event_type = "edx.pdf.loaded"
        event_data = {
            "url": self.url,
            "source_url": self.source_url,
        }
        self.runtime.publish(self, event_type, event_data)
        frag = Fragment(html)
        frag.add_javascript(resource_loader.load_unicode("static/js/pdf.js"))
        frag.initialize_js("pdfXBlockInitView")
        return frag

    def studio_view(self, context=None):
        """Return a fragment that contains the html for the studio view."""
        # Only the ReactJS editor is supported for this block.
        # See https://github.com/openedx/frontend-app-authoring/tree/master/src/editors/containers/PdfEditor
        raise NotImplementedError  # pragma: no cover

    @XBlock.json_handler
    def on_download(self, data, suffix=""):  # pylint: disable=unused-argument
        """Download file event handler."""
        event_type = "edx.pdf.downloaded"
        event_data = {
            "url": self.url,
            "source_url": self.source_url,
        }
        self.runtime.publish(self, event_type, event_data)

    @XBlock.handler
    def load_pdf(self, *_args, **_kwargs):
        """Get the PDF block's settings in JSON format."""
        return Response(json.dumps(self.raw_settings), content_type="application/json", charset="utf8")

    @XBlock.json_handler
    def convert_pdf(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        PDF Conversion handling. Basically just a frontend to the Gotenberg service which converts the given URL
        and then saves it to course assets, returning the URL.
        """
        permissions_service = self.runtime.service(self, "studio_user_permissions")
        if not permissions_service:
            return error_response(
                {"error": _("Conversion endpoint may only be called in a studio permissions-aware environment.")}
            )
        if not permissions_service.can_write(self.context_key):
            return error_response(
                {"error": _("You do not have permission to manage files for this block.")},
                status=403,
            )
        if not is_gotenberg_enabled():
            return error_response({"error": _("Gotenberg not enabled. PDF Conversion unavailable.")})
        user_service = self.runtime.service(self, "user")
        user_attrs = user_service.get_current_user().opt_attrs
        user = get_user_model().objects.get(id=user_attrs.get("edx-platform.user_id"))
        output_name = f"{self.scope_ids.usage_id}.pdf"
        try:
            file_bytes = fetch_source_asset(self.scope_ids.usage_id, data["url"])
        except (HTTPError, Timeout):
            logger.exception(_("Failed to fetch document at %s."), data["url"])
            return error_response({"error": _("Could not fetch source document.")}, status=502)
        source_url = urlparse(data["url"])
        source_filename = source_url.path.split("/")[-1]
        result = convert_to_pdf(source_filename, file_bytes, output_name)
        if result is None:
            return error_response({"error": _("PDF Conversion failed.")}, status=500)
        return {"url": add_asset(self.scope_ids.usage_id, result, user)}
