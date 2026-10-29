"""
Games XBlock handlers package.

This package contains all handler classes for the Games XBlock, organized by functionality:
- common: Universal handlers that work across all game types
- flashcards: Handlers specific to the flashcards game
- matching: Handlers specific to the matching game
"""

from .common import CommonHandlers
from .flashcards import FlashcardsHandlers
from .matching import MatchingHandlers

__all__ = ["CommonHandlers", "FlashcardsHandlers", "MatchingHandlers"]
