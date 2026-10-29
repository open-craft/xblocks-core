/* Javascript for FlashcardsXBlock. */

function GamesXBlockFlashcardsInit(runtime, element, cards) {
    'use strict';

    // State
    var currentIndex = 0;
    var totalCards = cards.length;
    var flipClassName = 'flashcard-flipped';

    // DOM references
    var $element = $(element);
    var $startScreen = $element.find('.flashcards-start-screen');
    var $startButton = $element.find('.flashcards-start-button');
    var $cardWrapper = $element.find('.flashcards-card-wrapper');
    var $footer = $element.find('.flashcard-footer');
    var $card = $element.find('#flashcard-card');
    var $term = $element.find('#flashcard-term');
    var $definition = $element.find('#flashcard-definition');
    var $termImage = $element.find('#flashcard-term-image');
    var $definitionImage = $element.find('#flashcard-definition-image');
    var $progress = $element.find('#flashcard-progress');
    var $prevBtn = $element.find('#flashcard-prev');
    var $nextBtn = $element.find('#flashcard-next');
    var $inner = $element.find('.flashcard-inner');
    var $liveRegion = $element.find('#flashcard-sr-announcements');

    function announce(message) {
        var el = $liveRegion[0];
        el.textContent = '';
        // Force reflow so the screen reader registers the cleared state
        void el.offsetHeight;
        el.textContent = message;
    }

    function getCardAriaLabel() {
        var card = cards[currentIndex];
        var isFlipped = $card.hasClass(flipClassName);
        if (isFlipped) {
            return 'Flashcard ' + (currentIndex + 1) + ' of ' + totalCards + '. Definition: ' + (card.definition || '') + '. Press Enter or Space to flip.';
        }
        return 'Flashcard ' + (currentIndex + 1) + ' of ' + totalCards + '. Term: ' + (card.term || '') + '. Press Enter or Space to flip.';
    }

    // Render current card
    function renderCard() {
        if (totalCards === 0) return;

        var card = cards[currentIndex];

        // Update content
        $term.text(card.term || '')
        $('.flashcard-front-content').attr('title', card.term || '');
        $definition.text(card.definition || '');
        $('.flashcard-back-content').attr('title', card.definition || '');


        // Handle term image
        if (card.term_image && card.term_image.trim() !== '') {
            var termAlt = card.term_image_alt || card.term || '';
            $termImage.attr('src', card.term_image).attr('alt', termAlt).show();
        } else {
            $termImage.hide();
        }

        // Handle definition image
        if (card.definition_image && card.definition_image.trim() !== '') {
            var defAlt = card.definition_image_alt || card.definition || '';
            $definitionImage.attr('src', card.definition_image).attr('alt', defAlt).show();
        } else {
            $definitionImage.hide();
        }

        // Update progress (1-indexed for display)
        $progress.text((currentIndex + 1));

        // Update button states
        $prevBtn.prop('disabled', currentIndex === 0);
        $nextBtn.prop('disabled', currentIndex === totalCards - 1);

        // Reset flip state instantly (no animation)
        if ($card.hasClass(flipClassName) && $inner.length) {
            $inner.addClass('no-transition');
            $card.removeClass(flipClassName);
            void $inner[0].offsetHeight;
            $inner.removeClass('no-transition');
        }
        $element.find('.flashcard-front').attr('aria-hidden', 'false');
        $element.find('.flashcard-back').attr('aria-hidden', 'true');
        $card.attr('aria-label', getCardAriaLabel());
        announce('Card ' + (currentIndex + 1) + ' of ' + totalCards + '. Term: ' + (card.term || ''));
    }

    // Flip card
    function flipCard() {
        var isFlipped = $card.hasClass(flipClassName);
        if (isFlipped) {
            $card.removeClass(flipClassName);
            $element.find('.flashcard-front').attr('aria-hidden', 'false');
            $element.find('.flashcard-back').attr('aria-hidden', 'true');
        } else {
            $card.addClass(flipClassName);
            $element.find('.flashcard-front').attr('aria-hidden', 'true');
            $element.find('.flashcard-back').attr('aria-hidden', 'false');
        }
        var card = cards[currentIndex];
        if ($card.hasClass(flipClassName)) {
            announce('Definition: ' + (card.definition || ''));
        } else {
            announce('Term: ' + (card.term || ''));
        }
        // Update aria-label after announce so it doesn't compete
        setTimeout(function() {
            $card.attr('aria-label', getCardAriaLabel());
        }, 1000);
    }

    // Navigation
    function goToPrev() {
        if (currentIndex > 0) {
            currentIndex--;
            renderCard();
        }
    }

    function goToNext() {
        if (currentIndex < totalCards - 1) {
            currentIndex++;
            renderCard();
        }
    }

    // Start game
    function startGame() {
        $startScreen.addClass('hidden');
        $cardWrapper.addClass('active');
        $footer.addClass('active');
        renderCard();
        // preventScroll keeps keyboard focus on the card without scrolling
        // the unit page (LP-859). Fall back to jQuery focus if unsupported.
        if ($card[0] && $card[0].focus) {
            $card[0].focus({ preventScroll: true });
        } else {
            $card.focus();
        }
    }

    // Event handlers
    $startButton.on('click', function(e) {
        e.preventDefault();
        startGame();
    });

    $card.on('click', function(e) {
        e.preventDefault();
        flipCard();
    });

    $prevBtn.on('click', function(e) {
        e.preventDefault();
        goToPrev();
    });

    $nextBtn.on('click', function(e) {
        e.preventDefault();
        goToNext();
    });

    // Keyboard navigation
    $(element).on('keydown.flashcards', function(e) {
        // Only handle if flashcards is visible
        if (!$element.is(':visible')) return;

        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                goToPrev();
                break;
            case 'ArrowRight':
                e.preventDefault();
                goToNext();
                break;
            case ' ':
            case 'Enter':
                // Only flip when the card itself is focused, not buttons
                if ($(e.target).is($card) || $card.find(e.target).length) {
                    e.preventDefault();
                    flipCard();
                }
                break;
        }
    });

    // Announce the game on load. Do NOT focus the start button here:
    // calling .focus() on an off-screen element scrolls the unit page down
    // to the flashcards (LP-859). Keyboard users reach Start by tabbing.
    setTimeout(function() {
        announce('Flashcard game. Press Start to begin.');
    }, 300);

    // Cleanup on unload
    $(element).on('remove', function() {
        $(element).off('keydown.flashcards');
    });
}
