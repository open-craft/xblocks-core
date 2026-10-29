"""
Types for the matching xblock.
"""

import uuid

from pydantic import BaseModel, Field


class Card(BaseModel):
    """
    Represents a single card.
    """

    text: str


class Pair(BaseModel):
    """
    Represents a pair of cards to match.
    """

    key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    left: Card
    right: Card


class Settings(BaseModel):
    """
    Represents the data associated with a matching xblock that may be modified by authors.
    """

    display_name: str = "Matching"
    is_shuffled: bool = True
    has_timer: bool = True
    pairs: list[Pair] = []
