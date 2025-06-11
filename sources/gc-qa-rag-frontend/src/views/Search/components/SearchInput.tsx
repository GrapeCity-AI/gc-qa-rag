import { Flex, Input, Segmented, Space, Button, Dropdown, Spin } from "antd";
import { isMobile } from "react-device-detect";
import { SearchInputProps } from "../types";
import {
    SearchMode,
    SearchModeNameKey,
} from "../../../types/Base";
import { RobotOutlined, RocketOutlined, SettingOutlined } from "@ant-design/icons";
import GradientButton from "../../../components/GradientButton";
import { useTranslation } from "react-i18next";

const searchModeIcons = {
    [SearchMode.Chat]: <RobotOutlined />,
    [SearchMode.Think]: <RocketOutlined />,
};

const SearchInput = ({
    products,
    productsLoading,
    mode,
    selectedProduct,
    switchMode,
    searchMode,
    inputValue,
    onProductChange,
    onInputChange,
    onSearch,
    searchModeItems,
}: SearchInputProps) => {
    const { t } = useTranslation();
    return (
        <Space direction="vertical" style={{ width: "100%" }}>
            <Flex align="center" gap={8}>
                {productsLoading ? (
                    <Spin size="small" />
                ) : (
                    <Segmented
                        value={selectedProduct}
                        options={products.map((product) => ({
                            label: t(product.display_name, { defaultValue: product.name }),
                            value: product.id,
                        }))}
                        onChange={onProductChange}
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

            <Flex align="center">
                <Input
                    value={inputValue}
                    placeholder={t("Home.SearchPlaceholder_Mobile")}
                    onChange={onInputChange}
                    allowClear
                    size="large"
                    style={{ marginRight: "10px" }}
                    onPressEnter={onSearch}
                    addonBefore={
                        <Dropdown menu={{ items: searchModeItems }}>
                            <Flex>
                                <Button
                                    color="default"
                                    type="text"
                                    icon={searchModeIcons[searchMode]}
                                >
                                    {isMobile
                                        ? ""
                                        : t(SearchModeNameKey[searchMode])}
                                </Button>
                            </Flex>
                        </Dropdown>
                    }
                />
                <GradientButton onClick={onSearch} />
            </Flex>
        </Space>
    );
};

export default SearchInput;
