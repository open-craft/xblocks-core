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

const getImageUrl = (side: CardSide) => side.image.url.trim();

const getImageAlt = (side: CardSide) => side.image.alt || side.text;

const FlashCard = forwardRef<HTMLDivElement, FlashCardProps>(
  ({ card, announce }, ref) => {
    const { formatMessage } = useIntl();
    const isSmall = useMediaQuery({ maxWidth: breakpoints.medium.maxWidth });
    const [isFlipped, setIsFlipped] = useState(false);
    const [shownCardKey, setShownCardKey] = useState(card.key);

    // Show the front side again whenever a different card is displayed.
    if (shownCardKey !== card.key) {
      setShownCardKey(card.key);
      setIsFlipped(false);
    }

    const flip = () => {
      const nextFlipped = !isFlipped;
      setIsFlipped(nextFlipped);
      const side = nextFlipped ? card.back : card.front;
      announce(
        formatMessage(
          nextFlipped ? messages.backAnnouncement : messages.frontAnnouncement,
          { text: side.text },
        ),
      );
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        flip();
      }
    };

    const activeSide = isFlipped ? card.back : card.front;
    const activeSideLabel = formatMessage(
      isFlipped ? messages.back : messages.front,
    );
    const cardLabel = formatMessage(messages.cardLabel, {
      side: activeSideLabel,
      text: activeSide.text,
    });

    const frontImageUrl = getImageUrl(card.front);
    const backImageUrl = getImageUrl(card.back);

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
            <div className="flashcard-content" title={card.front.text}>
              <h3>{card.front.text}</h3>
              {frontImageUrl && (
                <img src={frontImageUrl} alt={getImageAlt(card.front)} />
              )}
            </div>
          </Card>
          <Card
            className="flashcard-face flashcard-back"
            aria-hidden={!isFlipped}
          >
            <div className="flashcard-content" title={card.back.text}>
              <h3>{card.back.text}</h3>
              {backImageUrl && (
                <img src={backImageUrl} alt={getImageAlt(card.back)} />
              )}
            </div>
          </Card>
        </div>
      </div>
    );
  },
);

export default FlashCard;
