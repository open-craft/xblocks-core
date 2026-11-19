import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IntlProvider } from 'react-intl';
import './index.scss';
import App from './App.tsx';
import type { FlashcardsData } from './types.ts';

// The host page sets <html lang>; fall back to English when it is absent.
const locale = document.documentElement.lang || 'en';

interface XBlockRuntime {}

export const renderBlock = (
  element: Element,
  _runtime: XBlockRuntime,
  data: FlashcardsData,
) => {
  createRoot(element).render(
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
