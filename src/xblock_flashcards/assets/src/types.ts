export type GameType = 'flashcards' | 'matching';

export interface CardImage {
  url: string;
  alt?: string;
}

export interface CardSide {
  text: string;
  image?: CardImage;
}

export interface CardType {
  card_key: string;
  term: CardSide;
  definition: CardSide;
  editor_open?: boolean;
}

export type ContainerType = 'term' | 'definition';
