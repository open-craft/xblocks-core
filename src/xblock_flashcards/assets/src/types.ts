export interface CardImage {
  url: string;
  alt: string;
}

export interface CardSide {
  text: string;
  image: CardImage;
}

export interface CardType {
  key: string;
  front: CardSide;
  back: CardSide;
  editor_open: boolean;
}

export interface FlashcardsData {
  display_name: string;
  is_shuffled: boolean;
  cards: CardType[];
}
