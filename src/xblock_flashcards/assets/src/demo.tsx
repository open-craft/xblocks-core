import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { IntlProvider } from 'react-intl';
import './index.scss';
import App from './App.tsx';
import type { CardType } from './types.ts';

// The host page sets <html lang>; fall back to English when it is absent.
const locale = document.documentElement.lang || 'en';

const cards: CardType[] = [
  {
    key: 'A',
    editor_open: false,
    front: { text: 'Parts of the brain', image: { url: '', alt: '' } },
    back: {
      text: 'cerebrum, brainstem and cerebellum',
      image: { url: '', alt: '' },
    },
  },
  {
    key: 'B',
    editor_open: false,
    front: { text: 'Lobes of the brain', image: { url: '', alt: '' } },
    back: {
      text: 'frontal, parietal, temporal and occipital',
      image: { url: '', alt: '' },
    },
  },
  {
    key: 'C',
    editor_open: false,
    front: { text: 'Layers of heart walls', image: { url: '', alt: '' } },
    back: {
      text: 'Endocardium: Inner layer.\n Myocardium: Muscular middle layer.\n Epicardium: Protective outer layer.',
      image: { url: '', alt: '' },
    },
  },
  {
    key: 'D',
    editor_open: false,
    front: {
      text: 'Placeholder Image',
      image: {
        url: 'https://placehold.co/600x400',
        alt: 'Image of size 600 by 400',
      },
    },
    back: {
      text: 'Just checking for image',
      image: { url: '', alt: '' },
    },
  },
];

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <IntlProvider locale={locale}>
      <App cards={cards} displayName="Demo Flashcards" isShuffled />
    </IntlProvider>
  </StrictMode>,
);
