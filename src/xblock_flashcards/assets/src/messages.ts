import { defineMessages } from 'react-intl';

const messages = defineMessages({
  title: {
    id: 'flashcards.title',
    defaultMessage: 'Flashcards',
    description: 'Title shown at the top.',
  },
  regionLabel: {
    id: 'flashcards.region.label',
    defaultMessage: 'Flashcard game',
    description: 'Accessible label for the flashcards block landmark.',
  },
  startMsg: {
    id: 'flashcards.startpage.message',
    defaultMessage: 'Click each card to reveal the definition',
    description:
      'Initial message displayed to the user abdisplayed to the user above the Start button.',
  },
  startBtnLabel: {
    id: 'flashcards.startpage.button.label',
    defaultMessage: 'Start',
    description: 'Label of the "Start" button',
  },
  bottomTooltip: {
    id: 'flashcards.bottom.tooltip.message',
    defaultMessage: ' Click each card to reveal the definition.',
    description:
      'Tooltip message shown when user hover over the question mark icon at the bottom right corner.',
  },
  helpLabel: {
    id: 'flashcards.help.label',
    defaultMessage: 'Help',
    description: 'Accessible label for the help icon.',
  },
  previousCard: {
    id: 'flashcards.navigation.previous',
    defaultMessage: 'Previous card',
    description: 'Accessible label for the previous card button.',
  },
  nextCard: {
    id: 'flashcards.navigation.next',
    defaultMessage: 'Next card',
    description: 'Accessible label for the next card button.',
  },
  gameLoaded: {
    id: 'flashcards.announcement.loaded',
    defaultMessage: 'Flashcard game. Press Start to begin.',
    description: 'Announced to screen readers when the block loads.',
  },
  cardAnnouncement: {
    id: 'flashcards.announcement.card',
    defaultMessage: 'Card {current} of {total}. Term: {text}',
    description: 'Announced when the displayed card changes.',
  },
  termAnnouncement: {
    id: 'flashcards.announcement.term',
    defaultMessage: 'Term: {text}',
    description: 'Announced when a card is flipped back to its term.',
  },
  definitionAnnouncement: {
    id: 'flashcards.announcement.definition',
    defaultMessage: 'Definition: {text}',
    description: 'Announced when a card is flipped to its definition.',
  },
  term: {
    id: 'flashcards.side.term',
    defaultMessage: 'Term',
    description: 'Label for the front side of a card.',
  },
  definition: {
    id: 'flashcards.side.definition',
    defaultMessage: 'Definition',
    description: 'Label for the back side of a card.',
  },
  flashcardRole: {
    id: 'flashcards.card.role',
    defaultMessage: 'flashcard',
    description: 'Accessible role description for a card.',
  },
  cardLabel: {
    id: 'flashcards.card.label',
    defaultMessage: '{side}: {text}. Press Enter or Space to flip.',
    description: 'Accessible label describing the card and its active side.',
  },
});

export default messages;
