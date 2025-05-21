export interface Payload {
  file_index: string;
  question: string;
  answer: string;
  summary: string;
  url: string;
  title: string;
  category: string;
  collection_category: string;
  date?: number;
  full_answer?: string;
}

export interface SearchItem {
  id: number;
  version: number;
  score: number;
  payload: Payload;
  vector: any;
  shard_key: any;
  loading?: boolean;
  show_full_answer?: boolean;
}

export interface MessageItem {
  role: string;
  content: string;
}
