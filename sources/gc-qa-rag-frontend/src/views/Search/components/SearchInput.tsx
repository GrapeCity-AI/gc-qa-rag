import { Flex, Input, Segmented, Space, Button, Dropdown } from "antd";
import { isMobile } from "react-device-detect";
import { SearchInputProps } from "../types";
import {
    SearchMode,
    SearchModeNameKey,
    ProductNameKey,
    ProductType,
} from "../../../types/Base";
import { RobotOutlined, RocketOutlined } from "@ant-design/icons";
import GradientButton from "../../../components/GradientButton";
import { useTranslation } from "react-i18next";

const searchModeIcons = {
    [SearchMode.Chat]: <RobotOutlined />,
    [SearchMode.Think]: <RocketOutlined />,
};

const SearchInput = ({
    productType,
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
            <Flex>
                <Segmented
                    value={productType}
                    options={Object.keys(ProductNameKey).map((key: string) => ({
                        label: t(ProductNameKey[key as ProductType]),
                        value: key as ProductType,
                    }))}
                    onChange={onProductChange}
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
