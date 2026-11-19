import { type ComponentProps } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { ResponsiveContext } from '@openedx/paragon';
import { describe, it, expect, vi } from 'vitest';
import App from './App';
import type { CardType } from './types';

const cards: CardType[] = [
  { card_key: 'A', term: { text: 'Apple' }, definition: { text: 'A fruit' } },
  { card_key: 'B', term: { text: 'Ball' }, definition: { text: 'A toy' } },
];

type AppProps = Partial<ComponentProps<typeof App>>;

const renderApp = (props: AppProps = {}) =>
  render(
    <ResponsiveContext.Provider value={{ width: 1200 }}>
      <IntlProvider locale="en">
        <App cards={cards} title="Deck" isShuffled={false} {...props} />
      </IntlProvider>
    </ResponsiveContext.Provider>,
  );

const liveRegion = () => screen.getByRole('alert');
const announced = (text: RegExp | string) =>
  waitFor(() => expect(liveRegion()).toHaveTextContent(text), {
    timeout: 2000,
  });

const startGame = async () => {
  await userEvent.click(screen.getByRole('button', { name: 'Start' }));
};

const cardButton = (term: string) =>
  screen.getByRole('button', {
    name: new RegExp(`Term: ${term}\\. Press Enter or Space to flip\\.`),
  });

describe('App', () => {
  it('renders the region, title, start message, and footer help button', () => {
    renderApp();

    expect(
      screen.getByRole('region', { name: 'Flashcard game' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { level: 1, name: 'Deck' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', {
        level: 3,
        name: 'Click each card to reveal the definition',
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Help' })).toBeInTheDocument();
  });

  it('falls back to the default title when the title is empty', () => {
    renderApp({ title: '' });

    expect(
      screen.getByRole('heading', { level: 1, name: 'Flashcards' }),
    ).toBeInTheDocument();
  });

  it('does not render a card or card navigation before the game starts', () => {
    renderApp();

    expect(() => cardButton('Apple')).toThrow();
    expect(
      screen.queryByRole('button', { name: 'Previous card' }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Next card' }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText('1/2')).not.toBeInTheDocument();
  });

  it('starts the game and shows the first card with navigation state', async () => {
    renderApp();

    await startGame();

    expect(cardButton('Apple')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Previous card' }),
    ).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Next card' })).toBeEnabled();
    expect(
      screen.queryByRole('heading', {
        level: 3,
        name: 'Click each card to reveal the definition',
      }),
    ).not.toBeInTheDocument();
  });

  it('moves between cards with the next and previous buttons', async () => {
    renderApp();

    await startGame();
    await userEvent.click(screen.getByRole('button', { name: 'Next card' }));

    expect(cardButton('Ball')).toBeInTheDocument();
    expect(screen.getByText('2/2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Previous card' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Next card' })).toBeDisabled();

    await userEvent.click(
      screen.getByRole('button', { name: 'Previous card' }),
    );

    expect(cardButton('Apple')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
  });

  it('moves focus to the first card after the game starts', async () => {
    renderApp();

    await startGame();

    await waitFor(() => expect(cardButton('Apple')).toHaveFocus());
  });

  it('navigates with the left and right arrow keys', async () => {
    renderApp();
    const region = screen.getByRole('region', { name: 'Flashcard game' });

    await startGame();

    expect(fireEvent.keyDown(region, { key: 'ArrowRight' })).toBe(false);
    expect(cardButton('Ball')).toBeInTheDocument();
    expect(screen.getByText('2/2')).toBeInTheDocument();

    expect(fireEvent.keyDown(region, { key: 'ArrowLeft' })).toBe(false);
    expect(cardButton('Apple')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();
  });

  it('does not navigate past the first or last card', async () => {
    renderApp();
    const region = screen.getByRole('region', { name: 'Flashcard game' });

    await startGame();

    fireEvent.keyDown(region, { key: 'ArrowLeft' });
    expect(cardButton('Apple')).toBeInTheDocument();

    fireEvent.keyDown(region, { key: 'ArrowRight' });
    fireEvent.keyDown(region, { key: 'ArrowRight' });
    expect(cardButton('Ball')).toBeInTheDocument();
  });

  it('ignores other keys', async () => {
    renderApp();
    const region = screen.getByRole('region', { name: 'Flashcard game' });

    await startGame();

    expect(fireEvent.keyDown(region, { key: 'a' })).toBe(true);
    expect(cardButton('Apple')).toBeInTheDocument();
  });

  it('disables the start button and omits navigation for an empty deck', async () => {
    renderApp({ cards: [] });

    const startButton = screen.getByRole('button', { name: 'Start' });
    expect(startButton).toBeDisabled();

    await userEvent.click(startButton);

    expect(
      screen.getByRole('heading', {
        level: 3,
        name: 'Click each card to reveal the definition',
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Next card' }),
    ).not.toBeInTheDocument();
  });

  it('shuffles the cards when requested', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0);
    renderApp({ isShuffled: true });

    await startGame();

    expect(cardButton('Ball')).toBeInTheDocument();
    expect(screen.getByText('1/2')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Next card' }));

    expect(cardButton('Apple')).toBeInTheDocument();
    expect(screen.getByText('2/2')).toBeInTheDocument();
  });
});

describe('App announcements', () => {
  it('announces that the game is ready on mount', async () => {
    renderApp();

    await announced('Flashcard game. Press Start to begin.');
  });

  it('announces the position and term of the card that is shown', async () => {
    renderApp();

    await startGame();

    await announced('Card 1 of 2. Term: Apple');
  });

  it('announces the new position and term when navigating', async () => {
    renderApp();

    await startGame();
    await announced('Card 1 of 2. Term: Apple');

    await userEvent.click(screen.getByRole('button', { name: 'Next card' }));

    await announced('Card 2 of 2. Term: Ball');
  });

  it('announces only the side when the card is flipped', async () => {
    renderApp();

    await startGame();
    await announced('Card 1 of 2. Term: Apple');

    await userEvent.click(cardButton('Apple'));

    await announced(/^Definition: A fruit$/);
  });
});
