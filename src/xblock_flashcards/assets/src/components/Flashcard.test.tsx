import { createRef, type ComponentProps } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { ResponsiveContext } from '@openedx/paragon';
import { describe, it, expect, vi } from 'vitest';
import FlashCard from './Flashcard';
import type { CardType } from '../types';

const card: CardType = {
  key: 'A',
  front: { text: 'Apple', image: { url: '/front.png', alt: 'A red apple' } },
  back: { text: 'A fruit', image: { url: '/back.png', alt: '' } },
  editor_open: false,
};

type FlashCardProps = Partial<ComponentProps<typeof FlashCard>>;

const renderCard = (overrides: FlashCardProps = {}, width = 1200) => {
  const announce = vi.fn<(message: string) => void>(overrides.announce);
  const view = render(
    <ResponsiveContext.Provider value={{ width }}>
      <IntlProvider locale="en">
        <FlashCard card={card} {...overrides} announce={announce} />
      </IntlProvider>
    </ResponsiveContext.Provider>,
  );
  return { ...view, announce };
};

describe('FlashCard', () => {
  it('renders the front side when not flipped', () => {
    const { container } = renderCard();

    expect(screen.getByText('Apple')).toBeInTheDocument();
    expect(screen.getByText('A fruit')).toBeInTheDocument();
    expect(container.querySelector('.flashcard-front')).toHaveAttribute(
      'aria-hidden',
      'false',
    );
    expect(container.querySelector('.flashcard-back')).toHaveAttribute(
      'aria-hidden',
      'true',
    );
    expect(container.querySelector('.flashcard-wrapper')).not.toHaveClass(
      'flipped',
    );
  });

  it('does not announce on render, leaving position to the caller', () => {
    const { announce } = renderCard();

    expect(announce).not.toHaveBeenCalled();
  });

  it('flips to the back side when clicked', async () => {
    const { container, announce } = renderCard();

    await userEvent.click(screen.getByRole('button'));

    expect(container.querySelector('.flashcard-wrapper')).toHaveClass(
      'flipped',
    );
    expect(container.querySelector('.flashcard-front')).toHaveAttribute(
      'aria-hidden',
      'true',
    );
    expect(container.querySelector('.flashcard-back')).toHaveAttribute(
      'aria-hidden',
      'false',
    );
    expect(announce).toHaveBeenLastCalledWith('Back: A fruit');
  });

  it('describes the active side in its accessible name', () => {
    renderCard();

    expect(screen.getByRole('button')).toHaveAccessibleName(
      'Front: Apple. Press Enter or Space to flip.',
    );
  });

  it('uses the back in the accessible name when flipped', async () => {
    renderCard();

    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByRole('button')).toHaveAccessibleName(
      'Back: A fruit. Press Enter or Space to flip.',
    );
  });

  it('announces the back and then the front as it flips', async () => {
    const { announce } = renderCard();
    const button = screen.getByRole('button');

    await userEvent.click(button);
    expect(announce).toHaveBeenLastCalledWith('Back: A fruit');

    await userEvent.click(button);
    expect(announce).toHaveBeenLastCalledWith('Front: Apple');
  });

  it('returns to the front side when a different card is shown', async () => {
    const { container, announce, rerender } = renderCard();
    const button = screen.getByRole('button');

    await userEvent.click(button);
    expect(container.querySelector('.flashcard-wrapper')).toHaveClass(
      'flipped',
    );

    rerender(
      <ResponsiveContext.Provider value={{ width: 1200 }}>
        <IntlProvider locale="en">
          <FlashCard card={{ ...card, key: 'B' }} announce={announce} />
        </IntlProvider>
      </ResponsiveContext.Provider>,
    );

    expect(container.querySelector('.flashcard-wrapper')).not.toHaveClass(
      'flipped',
    );
  });

  it.each([
    ['Enter', '{Enter}'],
    ['Space', ' '],
  ])('flips and announces for the %s key', async (_name, keys) => {
    const { announce } = renderCard();
    const button = screen.getByRole('button');
    button.focus();

    await userEvent.keyboard(keys);

    expect(announce).toHaveBeenLastCalledWith('Back: A fruit');
  });

  it('prevents the default action for Enter and Space', () => {
    renderCard();
    const button = screen.getByRole('button');

    expect(fireEvent.keyDown(button, { key: 'Enter' })).toBe(false);
    expect(fireEvent.keyDown(button, { key: ' ' })).toBe(false);
  });

  it('ignores other keys', async () => {
    const { announce } = renderCard();
    const button = screen.getByRole('button');
    button.focus();
    announce.mockClear();

    await userEvent.keyboard('{ArrowRight}a');

    expect(announce).not.toHaveBeenCalled();
  });

  it('forwards its ref to the interactive wrapper', () => {
    const ref = createRef<HTMLDivElement>();
    const { container } = renderCard({ ref });

    expect(ref.current).toBe(container.querySelector('.flashcard-wrapper'));
  });

  it('renders images with alt text and falls back to the side text', () => {
    renderCard();

    expect(screen.getByAltText('A red apple')).toHaveAttribute(
      'src',
      '/front.png',
    );
    expect(screen.getByAltText('A fruit')).toHaveAttribute('src', '/back.png');
  });

  it('omits images that have no url', async () => {
    renderCard({
      card: {
        key: 'B',
        front: { text: 'Ball', image: { url: '   ', alt: '' } },
        back: { text: 'A toy', image: { url: '', alt: '' } },
        editor_open: false,
      },
    });

    expect(screen.getByText('Ball')).toBeInTheDocument();
    expect(screen.queryAllByRole('img')).toHaveLength(0);

    await userEvent.click(screen.getByRole('button'));

    expect(screen.queryAllByRole('img')).toHaveLength(0);
  });

  it('uses the side text as the image title fallback', () => {
    const { container } = renderCard();

    expect(
      container.querySelector('.flashcard-front .flashcard-content'),
    ).toHaveAttribute('title', 'Apple');
    expect(
      container.querySelector('.flashcard-back .flashcard-content'),
    ).toHaveAttribute('title', 'A fruit');
  });

  it('sizes the card dynamically based on screen size', () => {
    const { container: small } = renderCard({}, 500);

    expect(small.querySelector('.flashcard')).toHaveStyle({
      width: '100%',
    });

    const { container: large } = renderCard({}, 1200);

    expect(large.querySelector('.flashcard')).toHaveStyle({
      width: '32rem',
    });
  });
});
