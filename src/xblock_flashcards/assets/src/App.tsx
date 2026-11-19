import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react';
import { useIntl } from 'react-intl';
import {
  Button,
  Col,
  IconButton,
  Icon,
  OverlayTrigger,
  Row,
  Tooltip,
} from '@openedx/paragon';
import { ChevronLeft, ChevronRight, Question } from '@openedx/paragon/icons';

import type { CardType } from './types';
import './App.css';
import messages from './messages';
import FlashCard from './components/Flashcard';

interface AppProps {
  cards: CardType[];
  displayName: string;
  isShuffled: boolean;
}

const shuffleCards = (cards: CardType[]) => {
  const shuffled = [...cards];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

function App({ cards, displayName, isShuffled }: AppProps) {
  const { formatMessage } = useIntl();
  // Shuffle and store the cards as state, so it doesnt re-order at every render.
  const [cardList] = useState(() => (isShuffled ? shuffleCards(cards) : cards));
  const [showCards, setShowCards] = useState(false);
  const totalCards = cardList.length;
  const [currentCard, setCurrentCard] = useState(0);
  const cardRef = useRef<HTMLDivElement>(null);

  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const liveRegionRef = useRef<HTMLDivElement>(null);
  const [liveMessage, setLiveMessage] = useState('');

  const isFirstCard = currentCard === 0;
  const isLastCard = currentCard === totalCards - 1;

  const announce = useCallback((message: string) => {
    if (!liveRegionRef.current) return;
    // Clear first so repeated messages are re-announced by screen readers.
    setLiveMessage('');
    // Avoid cascading on quick user actions
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setLiveMessage(message), 300);
  }, []);

  useEffect(() => {
    // Announce the game is ready on mount
    announce(formatMessage(messages.gameLoaded));
    // clear the last timer on unmount
    return () => clearTimeout(timer.current);
  }, [announce, formatMessage]);

  // Announce which card is shown; FlashCard announces its own side on flip.
  useEffect(() => {
    if (!showCards || totalCards === 0) return;
    announce(
      formatMessage(messages.cardAnnouncement, {
        current: currentCard + 1,
        total: totalCards,
        text: cardList[currentCard].front.text,
      }),
    );
  }, [announce, cardList, currentCard, formatMessage, showCards, totalCards]);

  // Focus the card only after it has been rendered.
  useEffect(() => {
    if (!showCards) return;
    const card = cardRef.current;
    try {
      card?.focus({ preventScroll: true });
    } catch {
      card?.focus();
    }
  }, [showCards]);

  const goToCard = (index: number) => {
    if (index === currentCard || index < 0 || index >= totalCards) return;
    setCurrentCard(index);
  };

  const showPreviousCard = () => goToCard(currentCard - 1);
  const showNextCard = () => goToCard(currentCard + 1);

  const startGame = () => {
    if (totalCards === 0) return;
    setShowCards(true);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault();
        showPreviousCard();
        break;
      case 'ArrowRight':
        event.preventDefault();
        showNextCard();
        break;
      default:
        break;
    }
  };

  const titleText = displayName || formatMessage(messages.displayName);

  return (
    <div
      className="flashcards-block shadow-lg rounded-lg"
      role="region"
      aria-label={formatMessage(messages.regionLabel)}
      onKeyDown={handleKeyDown}
    >
      <div
        className="sr-only"
        aria-live="assertive"
        aria-atomic="true"
        role="alert"
        ref={liveRegionRef}
      >
        {liveMessage}
      </div>
      <Row className="flashcards-header">
        <Col>
          <h1>{titleText}</h1>
        </Col>
      </Row>
      <Row className="flashcards-content">
        {showCards && totalCards > 0 ? (
          <Col className="d-flex justify-content-center">
            <FlashCard
              ref={cardRef}
              card={cardList[currentCard]}
              announce={announce}
            />
          </Col>
        ) : (
          <div className="flashcards-startpage">
            <h3>{formatMessage(messages.startMsg)}</h3>
            <Button
              variant="brand"
              onClick={startGame}
              disabled={totalCards === 0}
            >
              {formatMessage(messages.startBtnLabel)}
            </Button>
          </div>
        )}
      </Row>
      <Row className="flashcards-footer mt-4 justify-content-end">
        {showCards && totalCards > 0 && (
          <Col className="text-center">
            <div className="d-inline-flex align-items-center">
              <IconButton
                variant="secondary"
                src={ChevronLeft}
                alt={formatMessage(messages.previousCard)}
                onClick={showPreviousCard}
                disabled={isFirstCard}
              />
              <span className="mx-4" aria-live="polite" aria-atomic="true">
                {currentCard + 1}/{totalCards}
              </span>
              <IconButton
                variant="secondary"
                src={ChevronRight}
                alt={formatMessage(messages.nextCard)}
                onClick={showNextCard}
                disabled={isLastCard}
              />
            </div>
          </Col>
        )}
        <Col className="flex-grow-0 align-self-end">
          <OverlayTrigger
            overlay={
              <Tooltip id="tooltip-flashcard">
                {formatMessage(messages.bottomTooltip)}
              </Tooltip>
            }
          >
            <button
              type="button"
              className="flashcard-help-icon border-0 bg-transparent p-0"
              aria-label={formatMessage(messages.helpLabel)}
            >
              <Icon src={Question} />
            </button>
          </OverlayTrigger>
        </Col>
      </Row>
    </div>
  );
}

export default App;
