export type BuyerDecisionFeedCardTone =
  | "signal"
  | "plan"
  | "proof"
  | "contrast"
  | "confidence";

export interface BuyerDecisionFeedCard {
  id: string;
  kicker: string;
  headline: string;
  body: string;
  proof?: string;
  tags: string[];
  tone: BuyerDecisionFeedCardTone;
}

export interface BuyerDecisionFeed {
  headline: string;
  subhead: string;
  cards: BuyerDecisionFeedCard[];
}
