"""
Types for the flashcards xblock.
"""

import uuid

from pydantic import BaseModel, Field


class Image(BaseModel):
    """
    Represents an image with optional alt text
    """

    url: str
    alt: str


class CardSide(BaseModel):
    """
    Represents a side of a card
    """

    text: str
    image: Image


class Card(BaseModel):
    """
    Represents a single flashcard.
    """

    card_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: CardSide
    definition: CardSide

    # used by the frontend editor in Authoring
    editor_open: bool


class Settings(BaseModel):
    """
    Represents the data associated with a flashcard xblock that may be modified by authors.
    """

    display_name: str = "Flashcards"
    is_shuffled: bool = True
    cards: list[Card] = []
