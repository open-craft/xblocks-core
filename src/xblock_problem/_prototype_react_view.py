"""
PROTOTYPE ONLY (throwaway branch `prototype/problem-paragon-numeric`).

Structured view/action data for a React + Paragon problem renderer that lives inside
the current `xblocks-core` `ProblemBlock`.

Question this prototype answers: can the *existing* ProblemBlock, inside the
*existing* LMS unit iframe, render a real CAPA problem with React + Paragon from
structured data derived from CAPA -- a single-select multiple choice and the
Studio-basic numerical input (`<numericalresponse><formulaequationinput/></...>`) --
including the existing CAPA `preview_formcalc` preview and MathJax typesetting,
submit through the real CAPA grading path, show structured feedback, and reload
with the same answer and attempts?

Rules this file deliberately keeps (do not grow them in a prototype):
- only one supported response with exactly one input: either one
  `<multiplechoiceresponse>` with one `<choicegroup>`, or one
  `<numericalresponse>` with one `<formulaequationinput>`; every other problem
  falls back to the unchanged legacy HTML renderer;
- no correct answers and no per-choice correctness before CAPA has graded;
- containment is fail-closed: the rollout flag AND an exact match with the one
  usage key in `XBLOCKS_CORE_PROBLEM_REACT_BLOCK_ID` (missing/blank allow-list
  means the prototype is off). The structured response is produced only for
  `problem_check`/`problem_reset` requests that opt in with `react_view=1` on
  that same block; every other request keeps the legacy payload unchanged;
- CAPA stays the only grader and the only owner of persisted learner state.

Remaining duplication with the legacy path (deliberate, limited to this file):
- the prompt/description/input strings are re-derived from CAPA's
  `problem_data` + XML tree instead of the Django templates;
- button visibility is recomputed from ProblemBlock helpers that the legacy
  template also calls, so the "which buttons" rule now has two call sites.
The legacy HTML is still produced on every submit (CAPA builds it before we
drop it) and is simply discarded for `react_view` requests.
"""
from __future__ import annotations

import copy
import logging
import os

from lxml import etree

from web_fragments.fragment import Fragment

from xblock_problem.capa import inputtypes, responsetypes

log = logging.getLogger(__name__)

REQUEST_KEY = "react_view"
ENV_VAR = "XBLOCKS_CORE_PROBLEM_REACT_RENDERER"
BLOCK_ID_ENV_VAR = "XBLOCKS_CORE_PROBLEM_REACT_BLOCK_ID"
SUPPORTED_ACTIONS = frozenset({"problem_check", "problem_reset"})
VIEW_SCHEMA = "prototype-react-view/1"

INPUT_TAGS = frozenset(inputtypes.registry.registered_tags())
RESPONSE_TAGS = frozenset(responsetypes.registry.registered_tags())


def _enabled_flag():
    flag = os.environ.get(ENV_VAR, "")
    return str(flag).strip().lower() in {"1", "true", "yes", "on"}


def allowlisted_block_id():
    """
    The single usage key this prototype may render, or None when unset.
    """
    value = os.environ.get(BLOCK_ID_ENV_VAR, "").strip()
    return value or None


def renderer_enabled(block):
    """
    Fail-closed rollout switch: enabled flag AND an exact usage-key match.

    Separate from the class-selection flag, and never global: a missing or blank
    allow-list, or any other block, keeps the legacy renderer and payloads.
    """
    if not _enabled_flag():
        return False
    allowed = allowlisted_block_id()
    if allowed is None:
        return False
    return str(block.usage_key) == allowed


def requested(data):
    """
    True when an action request asks for the structured payload.
    """
    if data is None:
        return False
    return str(data.get(REQUEST_KEY, "")).strip().lower() in {"1", "true", "yes", "on"}


def should_attach(block, action, data):
    """
    Gate for the structured action response.

    Only the actions this renderer actually performs, only opted-in requests,
    and only the allow-listed block; anything else keeps the legacy payload.
    """
    return action in SUPPORTED_ACTIONS and requested(data) and renderer_enabled(block)


def _choice_label_html(choice):
    """
    Choice label markup, without `<choicehint>` children (hints are feedback, not labels).
    """
    clone = copy.deepcopy(choice)
    for hint in clone.findall(".//choicehint"):
        parent = hint.getparent()
        if parent is not None:
            parent.remove(hint)
    return (clone.text or "") + "".join(etree.tostring(child, encoding="unicode") for child in clone)


def _prompt_html(block, lcp, response, input_id):
    """
    Authored prompt for the response: CAPA's extracted label plus any other
    non-response content still in the problem tree.
    """
    parts = []
    response_data = lcp.problem_data.get(input_id) or {}
    if response_data.get("label"):
        parts.append(str(response_data["label"]))

    for child in lcp.tree:
        if child is response or child.tag in RESPONSE_TAGS or child.tag in INPUT_TAGS:
            continue
        if child.tag == "script":
            continue
        parts.append(etree.tostring(child, encoding="unicode"))

    html = "".join(parts)
    try:
        html = block.runtime.service(block, "replace_urls").replace_urls(html)
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("prototype react view: replace_urls failed")
    return html


def _single_input(response):
    """
    The one input child of a response, or None when the shape is not supported.
    """
    inputs = [child for child in response if child.tag in INPUT_TAGS]
    return inputs[0] if len(inputs) == 1 else None


def _find_supported_response(lcp):
    """
    (mode, response, input_node, input_id) for a supported problem shape, else None.

    Supported shapes are deliberately only the two the prototype UI implements:
    a single multiple-choice choicegroup, and a single Studio-basic numerical
    input (formulaequationinput).
    """
    responses = lcp.tree.findall(".//multiplechoiceresponse")
    if len(responses) == 1:
        response = responses[0]
        choicegroups = response.findall("./choicegroup")
        if len(choicegroups) == 1:
            choicegroup = choicegroups[0]
            input_id = choicegroup.get("id")
            if input_id and len(choicegroup.findall("./choice")) >= 2:
                return "choice", response, choicegroup, input_id

    responses = lcp.tree.findall(".//numericalresponse")
    if len(responses) == 1:
        response = responses[0]
        input_node = _single_input(response)
        if input_node is not None and input_node.tag == "formulaequationinput":
            input_id = input_node.get("id")
            if input_id:
                return "numeric", response, input_node, input_id

    return None


def _selected_value(lcp, input_id):
    selected = (lcp.student_answers or {}).get(input_id, "")
    if isinstance(selected, list):
        selected = selected[0] if selected else ""
    return str(selected)


def build_view(block):
    """
    Build the structured view state for a supported problem, else None.
    """
    try:
        lcp = block.lcp
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    if lcp is None:
        return None

    supported = _find_supported_response(lcp)
    if supported is None:
        return None
    mode, response, input_node, input_id = supported

    selected = _selected_value(lcp, input_id)

    correctness_visible = block.correctness_available()
    status = "unsubmitted"
    message = ""
    hint = ""
    correct_map = lcp.correct_map
    if correct_map is not None and input_id in correct_map:
        if not correctness_visible:
            status = "submitted"
        elif not lcp.has_saved_answers:
            status = correct_map.get_correctness(input_id) or "unsubmitted"
            message = str(correct_map.get_msg(input_id) or "")
        hint = str(correct_map.get_hint(input_id) or "")

    notification_type, notification_message = block._get_answer_notification(  # pylint: disable=protected-access
        render_notifications=True
    )
    score, total = block.get_display_progress()

    response_data = lcp.problem_data.get(input_id) or {}
    descriptions = [
        {"id": description_id, "html": str(description_html)}
        for description_id, description_html in (response_data.get("descriptions") or {}).items()
    ]

    if mode == "choice":
        input_state = {
            "id": input_id,
            "name": f"input_{input_id}",
            "kind": "radio",
            "value": selected,
            "size": "",
            "trailing_text": "",
            "preview": False,
        }
        choices = [
            {
                "id": choice.get("name"),
                "label_html": _choice_label_html(choice),
                "selected": choice.get("name") == selected,
            }
            for choice in input_node.findall("./choice")
        ]
    else:
        input_state = {
            "id": input_id,
            "name": f"input_{input_id}",
            "kind": "text",
            "value": selected,
            "size": input_node.get("size") or "20",
            "trailing_text": input_node.get("trailing_text") or "",
            # Existing CAPA preview_formcalc handler, reached through input_ajax.
            "preview": True,
            "preview_url": f"{block.ajax_url}/input_ajax",
        }
        choices = []

    return {
        "schema": VIEW_SCHEMA,
        "mode": mode,
        "block_id": str(block.usage_key),
        "problem_html_id": block.usage_key.html_id(),
        "ajax_url": block.ajax_url,
        "title": block.display_name_with_default,
        "prompt_html": _prompt_html(block, lcp, response, input_id),
        "descriptions": descriptions,
        "input": input_state,
        "choices": choices,
        "status": status,
        "message": message,
        "hint": hint,
        "notification": {
            "type": notification_type or "",
            "message": str(notification_message or ""),
        },
        "attempts": {"used": block.attempts, "allowed": block.max_attempts},
        "grading_method": block.grading_method_display_name(),
        "score": {"earned": score, "possible": total},
        "graded": block.graded,
        "has_saved_answers": bool(lcp.has_saved_answers),
        "closed": block.closed(),
        "buttons": {
            "submit": block.should_enable_submit_button(),
            "submit_label": block.submit_button_name(),
            "reset": bool(block.attempts) and block.should_show_reset_button(),
            "save": block.should_show_save_button(),
            "show_answer": block.answer_available(),
        },
    }


def build_fragment(block):
    """
    Fragment for the React renderer, or None to use the legacy renderer.
    Never raises: an unsupported or broken problem falls back before the learner acts.
    """
    if not renderer_enabled(block):
        return None
    try:
        view = build_view(block)
        if view is None:
            return None
        fragment = Fragment('<div class="xblock-problem-react"></div>')
        fragment.add_javascript_url(
            block.runtime.local_resource_url(block, "public/js/ProblemReactDisplay.js")
        )
        fragment.initialize_js("ProblemReactRenderer", view)
        return fragment
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("prototype react renderer failed; falling back to legacy HTML")
        return None


def attach_to_response(block, result):
    """
    Swap the legacy HTML keys for the structured view, for opted-in requests only.
    Returns True when the structured payload was attached.
    """
    if not renderer_enabled(block):
        return False
    view = build_view(block)
    if view is None:
        return False
    result.pop("contents", None)
    result.pop("html", None)
    result[REQUEST_KEY] = view
    return True
