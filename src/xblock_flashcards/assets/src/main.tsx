import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IntlProvider } from 'react-intl';
import App from './App.tsx';
import { createShadowContainer } from './shadow.ts';
import type { FlashcardsData } from './types.ts';

// The host page sets <html lang>; fall back to English when it is absent.
const locale = document.documentElement.lang || 'en';

interface XBlockRuntime {}

/**
 * Entry point called by `static/js/render.js`.
 *
 * The block is rendered inside a shadow root (see `shadow.ts`) so that
 * Paragon's styles apply to the block only, and do not leak into the LMS or
 * Studio page around it.
 */
export const renderBlock = (
  _runtime: XBlockRuntime,
  element: Element | ArrayLike<Element>,
  { data }: { data: FlashcardsData },
) => {
  // Some runtimes pass the block element wrapped in jQuery.
  const host = element instanceof Element ? element : element[0];
  const container = createShadowContainer(host);
  createRoot(container).render(
    <StrictMode>
      <IntlProvider locale={locale}>
        <App
          cards={data.cards}
          displayName={data.display_name}
          isShuffled={data.is_shuffled}
        />
      </IntlProvider>
    </StrictMode>,
  );
};
