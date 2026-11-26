"""
PROTOTYPE (throwaway): deployment-token styling for the legacy problem view.

This answers one question: can the existing, server-rendered CAPA markup take its
appearance from a small deployment-supplied token set, scoped to a single block,
without touching the markup, the JS handlers or the grading state?

It is not production code. The production direction is the React + Paragon
renderer, which replaces the markup instead of restyling it.

The interface is one Django setting: an instance allowlist plus the token names
a deployment already emits (see @open-craft/edx-simple-theme paragon/css):

    PROBLEM_LEGACY_THEME = {
        "blocks": ["block-v1:Course+Run+type@problem+block@abc"],
        "tokens": {
            "--pgn-color-primary-500": "#002855",
            "--pgn-typography-headings-font-family": "Sora, sans-serif",
        },
    }

A block not in "blocks" is never touched, so a neighbour problem in the same unit
stays stock. Only TOKEN_NAMES below is consumed. A token the deployment does not
supply drops its own declaration, so the stock stylesheet still applies. No
setting, or an empty/invalid one, emits no stylesheet at all: the view is stock.
"""

from __future__ import annotations

import logging
import re

from django.conf import settings

log = logging.getLogger(__name__)

SETTING_NAME = "PROBLEM_LEGACY_THEME"

# Slot -> token name exactly as the deployment theme build emits it.
TOKEN_NAMES = {
    "primary": "--pgn-color-primary-500",
    "text": "--pgn-color-gray-900",
    "border": "--pgn-color-gray-300",
    "white": "--pgn-color-white",
    "sans": "--pgn-typography-font-family-sans-serif",
    "heading": "--pgn-typography-headings-font-family",
    "button-weight": "--pgn-typography-btn-font-weight",
    "input-radius": "--pgn-size-form-input-radius-border-base",
    "radius": "--pgn-wgu-size-border-radius-base",
    "focus-width": "--pgn-size-btn-focus-width",
    "success": "--pgn-color-success-base",
    "danger": "--pgn-color-danger-base",
}

# (selector suffix, {css property: value template}). SCOPE is replaced by the
# block's own wrapper id. The selectors are legacy CAPA hooks, which is the
# weakness of this approach: they are internal markup.
RULES = [
    ("", {
        "font-family": "{sans}",
        "color": "{text}",
    }),
    (" .problem-header", {
        "font-family": "{heading}",
        "color": "{primary}",
    }),
    (" .problem .choicegroup label", {
        "border-radius": "{input-radius}",
    }),
    (" .problem .choicegroup input:focus + label, SCOPE .problem .choicegroup input:hover + label", {
        "border-color": "{primary}",
    }),
    (" .problem .choicegroup input:focus-visible + label", {
        "outline": "{focus-width} solid {primary}",
    }),
    (" .problem .submit.btn-brand", {
        "background-color": "{primary}",
        "color": "{white}",
        "border-radius": "{radius}",
        "font-weight": "{button-weight}",
    }),
    (" .problem .submit.btn-brand:focus-visible", {
        "outline": "{focus-width} solid {primary}",
    }),
    (" .problem .problem-action-btn", {
        "color": "{primary}",
    }),
    (" .textline input, SCOPE .formulaequationinput input", {
        "border-radius": "{input-radius}",
        "border-color": "{border}",
    }),
    (" .notification.success", {
        "border-color": "{success}",
    }),
    (" .notification.error", {
        "border-color": "{danger}",
    }),
    (" .status.correct", {
        "color": "{success}",
    }),
    (" .status.incorrect", {
        "color": "{danger}",
    }),
]

_SLOT = re.compile(r"\{([a-z][a-z-]*)\}")

def _deployment_config():
    """Return (opt-in block ids, {slot: value}) for what this deployment supplies."""
    try:
        config = getattr(settings, SETTING_NAME, None)
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("Could not read %s; leaving the legacy problem view stock", SETTING_NAME)
        return set(), {}
    if not isinstance(config, dict):
        return set(), {}
    blocks = config.get("blocks")
    if not isinstance(blocks, (list, tuple, set)) or not blocks:
        return set(), {}
    token_config = config.get("tokens")
    if not isinstance(token_config, dict):
        return set(), {}
    tokens = {}
    for slot, token_name in TOKEN_NAMES.items():
        value = token_config.get(token_name)
        if isinstance(value, str) and value.strip():
            tokens[slot] = value.strip()
    return {str(block) for block in blocks}, tokens


def _fill(template, tokens):
    """Substitute slots, or return None if the deployment supplied none of them."""
    if any(slot not in tokens for slot in _SLOT.findall(template)):
        return None
    return _SLOT.sub(lambda match: tokens[match.group(1)], template)


def scoped_css(scope, usage_id):
    """
    Build a stylesheet rooted at ``scope``, or "" when there is nothing to apply.

    ``scope`` must match one block only, such as "#problem_<html_id>"; ``usage_id`` is
    the block's usage key, which is what the deployment allowlists.
    """
    blocks, tokens = _deployment_config()
    if str(usage_id) not in blocks or not tokens:
        return ""
    rules = []
    for suffix, declarations in RULES:
        body = []
        for prop, template in declarations.items():
            value = _fill(template, tokens)
            if value is not None:
                body.append(f"{prop}: {value};")
        if body:
            rules.append(f"{scope}{suffix.replace('SCOPE', scope)} {{ {' '.join(body)} }}")
    return "\n".join(rules)
