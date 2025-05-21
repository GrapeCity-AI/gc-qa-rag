import { Button, Divider, Flex, Space } from "antd";
import { ExpandAltOutlined, FileSearchOutlined } from "@ant-design/icons";
import { SearchResultsProps } from "../types";
import HitList from "../../../components/HitList";
import { useTranslation } from "react-i18next";

const SearchResults = ({
    retrivalItem,
    onShowFullAnswer,
    retrivals,
    refreshUI,
}: SearchResultsProps) => {
    const { t } = useTranslation();
    return (
        <Flex vertical>
            <Flex align="center" justify="space-between">
                <Flex flex={1}>
                    <Divider orientationMargin="0" orientation="left">
                        <Space>
                            <FileSearchOutlined />
                            {t("Search.SearchResults")}
                        </Space>
                    </Divider>
                </Flex>
                {retrivals.length > 1 && (
                    <Button
                        icon={<ExpandAltOutlined />}
                        size="small"
                        type="text"
                        onClick={() => {
                            retrivalItem.search.collapsed =
                                !retrivalItem.search.collapsed;
                            refreshUI();
                        }}
                    >
                        {retrivalItem.search.collapsed
                            ? t("Search.Expand")
                            : t("Search.Collapse")}
                    </Button>
                )}
            </Flex>

            {!retrivalItem.search.collapsed && (
                <HitList
                    loading={retrivalItem.search.loading}
                    list={retrivalItem.search.results}
                    onShowFullAnswer={onShowFullAnswer}
                />
            )}
        </Flex>
    );
};

export default SearchResults;
