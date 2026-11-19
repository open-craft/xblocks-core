import { forwardRef, useState, type KeyboardEvent } from 'react';
import { useIntl } from 'react-intl';
import { Card, useMediaQuery, breakpoints } from '@openedx/paragon';

import { type CardSide, type CardType } from '../types';
import messages from '../messages';
import './FlashCard.css';

interface FlashCardProps {
  card: CardType;
  announce: (message: string) => void;
}

const getImageUrl = (side: CardSide) => side.image?.url?.trim() ?? '';

const getImageAlt = (side: CardSide) => side.image?.alt || side.text || '';

const FlashCard = forwardRef<HTMLDivElement, FlashCardProps>(
  ({ card, announce }, ref) => {
    const { formatMessage } = useIntl();
    const isSmall = useMediaQuery({ maxWidth: breakpoints.medium.maxWidth });
    const [isFlipped, setIsFlipped] = useState(false);
    const [shownCardKey, setShownCardKey] = useState(card.card_key);

    // Show the term side again whenever a different card is displayed.
    if (shownCardKey !== card.card_key) {
      setShownCardKey(card.card_key);
      setIsFlipped(false);
    }

    const flip = () => {
      const nextFlipped = !isFlipped;
      setIsFlipped(nextFlipped);
      const side = nextFlipped ? card.definition : card.term;
      announce(
        formatMessage(
          nextFlipped
            ? messages.definitionAnnouncement
            : messages.termAnnouncement,
          { text: side.text || '' },
        ),
      );
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        flip();
      }
    };

    const activeSide = isFlipped ? card.definition : card.term;
    const activeSideLabel = formatMessage(
      isFlipped ? messages.definition : messages.term,
    );
    const cardLabel = formatMessage(messages.cardLabel, {
      side: activeSideLabel,
      text: activeSide.text || '',
    });

    const termImageUrl = getImageUrl(card.term);
    const definitionImageUrl = getImageUrl(card.definition);

    return (
      <div className="flashcard" style={{ width: isSmall ? '100%' : '32rem' }}>
        <div
          ref={ref}
          className={`text-center flashcard-wrapper ${isFlipped ? 'flipped' : ''}`}
          onClick={flip}
          onKeyDown={handleKeyDown}
          role="button"
          tabIndex={0}
          aria-pressed={isFlipped}
          aria-roledescription={formatMessage(messages.flashcardRole)}
          aria-label={cardLabel}
        >
          <Card
            className="flashcard-face flashcard-front"
            aria-hidden={isFlipped}
          >
            <div className="flashcard-content" title={card.term.text || ''}>
              <h3 className="h3">{card.term.text}</h3>
              {termImageUrl && (
                <img src={termImageUrl} alt={getImageAlt(card.term)} />
              )}
            </div>
          </Card>
          <Card
            className="flashcard-face flashcard-back"
            aria-hidden={!isFlipped}
          >
            <div
              className="flashcard-content"
              title={card.definition.text || ''}
            >
              <h3 className="h3">{card.definition.text}</h3>
              {definitionImageUrl && (
                <img
                  src={definitionImageUrl}
                  alt={getImageAlt(card.definition)}
                />
              )}
            </div>
          </Card>
        </div>
      </div>
    );
  },
);

export default FlashCard;
