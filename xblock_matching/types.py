"""
Types for the matching xblock.
"""

import uuid

from pydantic import BaseModel, Field


class Card(BaseModel):
    """
    Represents a single flashcard.
    """

    card_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    definition: str


class Settings(BaseModel):
    """
    Represents the data associated with a matching xblock that may be modified by authors.
    """

    display_name: str = "Matching"
    is_shuffled: bool = True
    has_timer: bool = True
    cards: list[Card] = []
