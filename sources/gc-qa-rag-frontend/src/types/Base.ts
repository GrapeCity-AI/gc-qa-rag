export enum ProductType {
    Forguncy = 'forguncy',
    Wyn = 'wyn',
    SpreadJS = 'spreadjs',
    GcExcel = 'gcexcel',
}

export enum SearchMode {
    Chat = 'chat',
    Think = 'think',
}

export const ProductNameKey = {
    [ProductType.Forguncy]: 'ProductName.Forguncy',
    [ProductType.Wyn]: 'ProductName.Wyn',
    [ProductType.SpreadJS]: 'ProductName.SpreadJS',
    [ProductType.GcExcel]: 'ProductName.GcExcel',
}

export interface ProductInfo {
    id: string;
    name: string;
    display_name: string;
    type: 'fixed' | 'generic';
}

export interface ProductsResponse {
    mode: 'fixed' | 'generic';
    products: ProductInfo[];
}

export const SearchModeNameKey = {
    [SearchMode.Chat]: 'SearchModeName.chat',
    [SearchMode.Think]: 'SearchModeName.think',
}

export const TextResourcesKey = {
    Common: {
        WebsiteName: 'Common.WebsiteName'
    },
    Home: {
        SearchPlaceholder: 'Home.SearchPlaceholder',
        SearchPlaceholder_Mobile: 'Home.SearchPlaceholder_Mobile',
    },
    Search: {
        AIChat: 'Search.AIChat',
        SearchResults: 'Search.SearchResults'
    }
}

// Answer Options Types
export enum AnswerStyle {
    Beginner = 'beginner',
    Professional = 'professional'
}

export enum AnswerComplexity {
    Concise = 'concise',
    Verbose = 'verbose'
}

export interface AnswerOptions {
    style: AnswerStyle;
    complexity: AnswerComplexity;
    customInstruction: string;
}

export const DEFAULT_ANSWER_OPTIONS: AnswerOptions = {
    style: AnswerStyle.Professional,
    complexity: AnswerComplexity.Concise,
    customInstruction: ''
};

export const AnswerStyleNameKey = {
    [AnswerStyle.Beginner]: 'AnswerOptions.Beginner',
    [AnswerStyle.Professional]: 'AnswerOptions.Professional',
};

export const AnswerComplexityNameKey = {
    [AnswerComplexity.Concise]: 'AnswerOptions.Concise',
    [AnswerComplexity.Verbose]: 'AnswerOptions.Verbose',
};