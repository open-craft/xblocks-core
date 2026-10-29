"""
Types for the flashcards xblock.
"""

import uuid

from pydantic import BaseModel, Field


class Card(BaseModel):
    """
    Represents a single flashcard.
    """

    card_key: str = Field(default_factory=lambda: str(uuid.uuid4()))

    term: str
    term_image: str = ""
    term_image_alt: str = ""
    term_image_path: str = ""

    definition: str
    definition_image: str = ""
    definition_image_alt: str = ""
    definition_image_path: str = ""


class Settings(BaseModel):
    """
    Represents the data associated with a flashcard xblock that may be modified by authors.
    """

    display_name: str = "Flashcards"
    is_shuffled: bool = True
    cards: list[Card] = []
