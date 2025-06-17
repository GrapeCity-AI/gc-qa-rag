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