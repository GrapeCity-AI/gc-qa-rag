import { useState, useEffect } from "react";
import { ProductInfo, ProductsResponse, ProductType } from "../types/Base";
import { getProductsResult } from "../services/ApiService";
import { getUrlSearchArg } from "../common/utils";

export const useProducts = () => {
    const [products, setProducts] = useState<ProductInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [mode, setMode] = useState<'fixed' | 'generic'>('fixed');

    // 获取URL参数或localStorage中的产品模式
    const getInitialMode = (): 'fixed' | 'generic' => {
        const urlMode = getUrlSearchArg("productmode");
        const storedMode = localStorage.getItem("gcai-product-mode");

        if (urlMode === "generic" || storedMode === "generic") {
            return "generic";
        }
        return "fixed";
    };

    // 获取初始选中的产品
    const getInitialProduct = (productList: ProductInfo[]): string => {
        const urlProduct = getUrlSearchArg("product");
        const storedProduct = localStorage.getItem("gcai-product");

        if (urlProduct && productList.some(p => p.id === urlProduct)) {
            return urlProduct;
        }

        if (storedProduct && productList.some(p => p.id === storedProduct)) {
            return storedProduct;
        }

        // 默认返回第一个产品
        return productList.length > 0 ? productList[0].id : urlProduct || storedProduct || ProductType.Forguncy;
    };

    const [selectedProduct, setSelectedProduct] = useState<string>(getInitialProduct([]));

    const loadProducts = async (productMode: 'fixed' | 'generic') => {
        try {
            setLoading(true);
            const response: ProductsResponse = await getProductsResult(productMode);
            setProducts(response.products);
            setMode(response.mode);

            // 设置初始选中的产品
            const initialProduct = getInitialProduct(response.products);
            setSelectedProduct(initialProduct);

        } catch (error) {
            console.error("Failed to load products:", error);
            // 出错时使用固定产品列表
            const fallbackProducts: ProductInfo[] = [
                { id: ProductType.Forguncy, name: "Forguncy", display_name: "ProductName.Forguncy", type: "fixed" },
                { id: ProductType.Wyn, name: "Wyn", display_name: "ProductName.Wyn", type: "fixed" },
                { id: ProductType.SpreadJS, name: "SpreadJS", display_name: "ProductName.SpreadJS", type: "fixed" },
                { id: ProductType.GcExcel, name: "GcExcel", display_name: "ProductName.GcExcel", type: "fixed" }
            ];
            setProducts(fallbackProducts);
            setMode('fixed');
            setSelectedProduct(ProductType.Forguncy);
        } finally {
            setLoading(false);
        }
    };

    const switchMode = async (newMode: 'fixed' | 'generic') => {
        if (newMode !== mode) {
            localStorage.setItem("gcai-product-mode", newMode);
            await loadProducts(newMode);
        }
    };

    const selectProduct = (productId: string) => {
        setSelectedProduct(productId);
        localStorage.setItem("gcai-product", productId);
    };

    useEffect(() => {
        const initialMode = getInitialMode();
        loadProducts(initialMode);
    }, []);

    return {
        products,
        loading,
        mode,
        selectedProduct,
        switchMode,
        selectProduct,
        loadProducts
    };
}; 