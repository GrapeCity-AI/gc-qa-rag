import { MenuProps } from "antd";
import { SearchItem } from "../../types/Api";
import { ProductType, SearchMode } from "../../types/Base";

export interface RetrivalItem {
  key: number;
  query: string;
  answer: {
    reasoning_content?: string;
    content: string;
    loading: boolean;
    typing: boolean;
    asking: boolean;
    collapsed: boolean;
    liked: boolean;
    disliked: boolean;
  };
  search: {
    results: SearchItem[];
    loading: boolean;
    collapsed: boolean;
  };
}

export interface SearchHeaderProps {
  onGoHome: () => void;
}

export interface SearchInputProps {
  productType: ProductType;
  searchMode: SearchMode;
  inputValue: string;
  onProductChange: (value: string) => void;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSearch: () => void;
  searchModeItems: MenuProps["items"];
}

export interface AnswerSectionProps {
  retrivalItem: RetrivalItem;
  index: number;
  onLike: () => void;
  onDislike: () => void;
  onCopy: () => void;
  onCopyImage: () => void;
  onAskMore: () => void;
  onAppendSearch: () => void;
  onAppendSearchChanged: (value: string) => void;
  onAppendBoxPressEnter: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onPause: () => void;
  searchMode: SearchMode;
}

export interface AnswerActionsProps {
  retrivalItem: RetrivalItem;
  index: number;
  onLike: () => void;
  onDislike: () => void;
  onCopy: () => void;
  onCopyImage: () => void;
  onAskMore: () => void;
  onAppendSearch: () => void;
  onAppendSearchChanged: (value: string) => void;
  onAppendBoxPressEnter: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
}

export interface SearchResultsProps {
  retrivalItem: RetrivalItem;
  onShowFullAnswer: (searchItem: SearchItem) => void;
  retrivals: RetrivalItem[];
  refreshUI: () => void;
} 