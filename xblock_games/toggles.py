"""
Toggles for games xblock.
"""

from edx_toggles.toggles import WaffleFlag

# .. toggle_name: legacy_studio.enable_games_xblock
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the games xblock
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2025-11-21
# .. toggle_target_removal_date: 2026-02-21
ENABLE_GAMES_XBLOCK = WaffleFlag(
    "legacy_studio.enable_games_xblock",
    module_name=__name__,
    log_prefix="games_xblock",
)


def is_games_xblock_enabled():
    """
    Return Waffle flag for enabling the games xblock on legacy studio.
    """
    try:
        # adding this try/catch cause
        # goCD deployment is getting MySQL connection failure during make pull_translations django command,
        # caused by Django trying to evaluate a waffle flag (legacy_studio.enable_games_xblock) at import time
        # when CMS is not up
        return ENABLE_GAMES_XBLOCK.is_enabled()
    except Exception:
        return False
