import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IntlProvider } from 'react-intl';
import './index.scss';
import App from './App.tsx';

// The host page sets <html lang>; fall back to English when it is absent.
const locale = document.documentElement.lang || 'en';

const cards = [
  {
    card_key: 'A',
    term: { text: 'Parts of the brain' },
    definition: { text: 'cerebrum, brainstem and cerebellum' },
  },
  {
    card_key: 'B',
    term: { text: 'Lobes of the brain' },
    definition: { text: 'frontal, parietal, temporal and occipital' },
  },
  {
    card_key: 'C',
    term: { text: 'Layers of heart walls' },
    definition: {
      text: 'Endocardium: Inner layer.\n Myocardium: Muscular middle layer.\n Epicardium: Protective outer layer.',
    },
  },
  {
    card_key: 'D',
    term: {
      text: 'Placeholder Image',
      image: {
        url: 'https://placehold.co/600x400',
        alt: 'Image of size 600 by 400',
      },
    },
    definition: {
      text: 'Just checking for image',
    },
  },
];

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <IntlProvider locale={locale}>
      <App cards={cards} title="Demo Flashcards" isShuffled />
    </IntlProvider>
  </StrictMode>,
);
