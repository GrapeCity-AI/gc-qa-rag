import { useState } from "react";
import { Button, Flex, Segmented, Space, Switch, Typography, Spin } from "antd";
import { isMobile } from "react-device-detect";
import { ArrowRightOutlined, SettingOutlined } from "@ant-design/icons";
import Title from "antd/es/typography/Title";
import TextArea from "antd/es/input/TextArea";
import { useNavigate } from "react-router-dom";
import {
    SearchMode,
    TextResourcesKey,
} from "../types/Base";
import CustomFooter from "../components/CustomFooter";
import { getUrlSearchArg, raise_gtag_event } from "../common/utils";
import { useTranslation } from "react-i18next";
import { useProducts } from "../hooks/useProducts";
// Custom hooks - 已移至独立的useProducts hook

const useSearchMode = () => {
    const initialSearchMode =
        getUrlSearchArg("searchmode") ??
        sessionStorage.getItem("gcai-searchmode") ??
        SearchMode.Chat;

    const [searchMode, setSearchMode] = useState<SearchMode>(() => {
        if (
            initialSearchMode !== SearchMode.Chat &&
            initialSearchMode !== SearchMode.Think
        ) {
            return SearchMode.Chat;
        }
        return initialSearchMode as SearchMode;
    });

    const handleSearchModeChange = (value: SearchMode) => {
        setSearchMode(value);
        sessionStorage.setItem("gcai-searchmode", value);
    };

    return { searchMode, handleSearchModeChange };
};

// Components
const SearchInput = ({
    value,
    onChange,
    onSearch,
    searchMode,
    onSearchModeChange,
}: {
    value: string;
    onChange: (value: string) => void;
    onSearch: () => void;
    searchMode: SearchMode;
    onSearchModeChange: (value: SearchMode) => void;
}) => {
    const handlePressEnter = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            onSearch();
        }
    };

    const { t } = useTranslation();

    return (
        <Flex
            vertical
            style={{ border: "2px solid #d9d9d9", borderRadius: "4px" }}
        >
            <TextArea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onPressEnter={handlePressEnter}
                placeholder={
                    isMobile
                        ? t(TextResourcesKey.Home.SearchPlaceholder_Mobile)
                        : t(TextResourcesKey.Home.SearchPlaceholder)
                }
                autoSize={{ minRows: 3, maxRows: 5 }}
                size="large"
                variant="borderless"
                count={{ max: 1000 }}
            />
            <Flex
                style={{
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px",
                }}
            >
                <Flex align="center" gap={8}>
                    <Switch
                        size="small"
                        checked={searchMode === SearchMode.Think}
                        onChange={(checked: boolean) =>
                            onSearchModeChange(
                                checked ? SearchMode.Think : SearchMode.Chat
                            )
                        }
                    />
                    <Typography.Text>{t("Home.DeepThink")}</Typography.Text>
                </Flex>
                <Button
                    shape="circle"
                    color="primary"
                    icon={<ArrowRightOutlined />}
                    onClick={onSearch}
                />
            </Flex>
        </Flex>
    );
};

const HomePage = () => {
    const { products, loading, mode, selectedProduct, switchMode, selectProduct } = useProducts();
    const { searchMode, handleSearchModeChange } = useSearchMode();
    const [inputValue, setInputValue] = useState("");
    const navigate = useNavigate();
    const { t } = useTranslation();

    const handleSearch = () => {
        const queryArg = `query=${encodeURIComponent(inputValue)}`;
        const productArg = `product=${encodeURIComponent(selectedProduct)}`;
        const searchModeArg = `searchmode=${encodeURIComponent(searchMode)}`;
        const productModeArg = `productmode=${encodeURIComponent(mode)}`;

        raise_gtag_event("home.enter", {
            query: queryArg,
            product: productArg,
            searchmode: searchModeArg,
            productmode: productModeArg,
        });

        navigate(`/search?${queryArg}&${productArg}&${searchModeArg}&${productModeArg}`);
    };

    return (
        <Flex
            style={{ height: "100vh", width: "100vw" }}
            vertical
            align="center"
            justify="space-between"
        >
            <Flex
                vertical
                align="center"
                justify="center"
                style={{
                    height: "70vh",
                    width: "calc(100vw - 64px)",
                    maxWidth: "720px",
                }}
            >
                <Title
                    level={1}
                    style={{
                        background:
                            "linear-gradient(270deg, #AE79CC 3%, #1366EC 96%)",
                        backgroundClip: "text",
                        color: "transparent",
                        marginBottom: "40px",
                    }}
                >
                    {t(TextResourcesKey.Common.WebsiteName)}
                </Title>
                <Space direction="vertical" style={{ width: "100%" }}>
                    <Flex align="center" gap={8}>
                        {loading ? (
                            <Spin size="small" />
                        ) : (
                            <Segmented
                                value={selectedProduct}
                                options={products.map((product) => ({
                                    label: t(product.display_name, { defaultValue: product.name }),
                                    value: product.id,
                                }))}
                                onChange={(value) => selectProduct(value as string)}
                            />
                        )}
                        <Button 
                            icon={<SettingOutlined />} 
                            onClick={() => switchMode(mode === 'fixed' ? 'generic' : 'fixed')}
                            title={`Switch to ${mode === 'fixed' ? 'Generic' : 'Fixed'} Mode`}
                            type={mode === 'generic' ? 'primary' : 'default'}
                            size="small"
                        />
                    </Flex>
                    <SearchInput
                        value={inputValue}
                        onChange={setInputValue}
                        onSearch={handleSearch}
                        searchMode={searchMode}
                        onSearchModeChange={handleSearchModeChange}
                    />
                </Space>
            </Flex>
            <CustomFooter />
        </Flex>
    );
};

export default HomePage;
