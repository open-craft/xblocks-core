"""
Tests for internationalization (i18n) support.
"""

from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _
from faker import Faker


class TestTranslations(TestCase):
    """Tests for translation support."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake = Faker()

    def test_english_translations(self):
        """Test that English translations are loaded correctly."""
        with translation.override("en"):
            translated = _("Each card must be an object")
            self.assertEqual(translated, "Each card must be an object")

    def test_spanish_translations(self):
        """Test that Spanish translations are loaded correctly."""
        with translation.override("es_419"):
            translated = _("Each card must be an object")
            self.assertEqual(translated, "Cada tarjeta debe ser un objeto")

    def test_spanish_start_button(self):
        """Test Spanish translation for Start button."""
        with translation.override("es_419"):
            translated = _("Start")
            self.assertEqual(translated, "Comenzar")

    def test_spanish_help_text(self):
        """Test Spanish translation for Help."""
        with translation.override("es_419"):
            translated = _("Help")
            self.assertEqual(translated, "Ayuda")

    def test_spanish_congratulations(self):
        """Test Spanish translation for Congratulations."""
        with translation.override("es_419"):
            translated = _("Congratulations!")
            self.assertEqual(translated, "¡Felicitaciones!")

    def test_spanish_play_again(self):
        """Test Spanish translation for Play again."""
        with translation.override("es_419"):
            translated = _("Play again")
            self.assertEqual(translated, "Jugar de nuevo")

    def test_spanish_card_instructions(self):
        """Test Spanish translation for card instructions."""
        with translation.override("es_419"):
            translated = _("Click each card to reveal the definition")
            self.assertEqual(translated, "Haz clic en cada tarjeta para revelar la definición")

    def test_spanish_matching_instructions(self):
        """Test Spanish translation for matching instructions."""
        with translation.override("es_419"):
            translated = _("Match each term with the correct definition")
            self.assertEqual(translated, "Empareja cada término con la definición correcta")

    def test_translation_fallback_to_english(self):
        """Test that untranslated strings fall back to English."""
        with translation.override("es_419"):
            # This string is not in our translations
            untranslated = _("This string does not exist")
            self.assertEqual(untranslated, "This string does not exist")
