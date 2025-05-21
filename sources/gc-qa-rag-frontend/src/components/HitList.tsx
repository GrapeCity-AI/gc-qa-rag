import {
    Alert,
    Badge,
    ConfigProvider,
    Empty,
    Flex,
    List,
    Skeleton,
    Space,
    Tabs,
} from "antd";
import { SearchItem } from "../types/Api";
import {
    BookOutlined,
    BulbOutlined,
    CommentOutlined,
    LinkOutlined,
    ProfileOutlined,
} from "@ant-design/icons";
import Text from "antd/es/typography/Text";
import Link from "antd/es/typography/Link";
import { Markdown } from "./Markdown";
import { getDateStringByUnixTime, raise_gtag_event } from "../common/utils";
import { useTranslation } from "react-i18next";

// Constants
const CATEGORIES = ["", "doc", "forum_qa", "forum_tutorial"];
const TAB_ICONS = [
    ProfileOutlined,
    BookOutlined,
    CommentOutlined,
    BulbOutlined,
];

interface HitListProps {
    list: SearchItem[];
    loading?: boolean;
    onShowFullAnswer?: (item: SearchItem) => void;
}

interface HitItemProps {
    item: SearchItem;
    onShowFullAnswer: (item: SearchItem) => void;
}

const HitItem = ({ item, onShowFullAnswer }: HitItemProps) => {
    const handleNavigate = () => {
        raise_gtag_event("search.hit.navigate");
    };
    const { t } = useTranslation();
    return (
        <Skeleton title={false} loading={item.loading} active>
            <List.Item.Meta
                title={item.payload.question}
                description={
                    <Flex vertical>
                        {item.payload.full_answer ? (
                            <Link
                                color="default"
                                onClick={() => onShowFullAnswer(item)}
                            >
                                <Text>{item.payload.answer}</Text>
                                {!item.show_full_answer && (
                                    <Text> {t("Search.ExpandMore")}</Text>
                                )}
                            </Link>
                        ) : (
                            <Text>{item.payload.answer}</Text>
                        )}

                        {item.show_full_answer && (
                            <Alert
                                style={{ marginTop: "16px" }}
                                message={
                                    <Markdown
                                        content={item.payload.full_answer ?? ""}
                                    />
                                }
                            />
                        )}
                    </Flex>
                }
            />
            <Flex align="center" justify="space-between">
                <Space>
                    <LinkOutlined
                        style={{
                            fontSize: 12,
                            color: "rgba(0, 0, 0, 0.45)",
                        }}
                    />
                    <Link
                        href={item.payload.url}
                        target="_blank"
                        onClick={handleNavigate}
                    >
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            {`${item.payload.category} ${
                                item.payload.title
                            } ${getDateStringByUnixTime(item.payload.date)}`}
                        </Text>
                    </Link>
                </Space>
            </Flex>
        </Skeleton>
    );
};

const HitList = ({ list, loading, onShowFullAnswer }: HitListProps) => {
    const { t } = useTranslation();
    const handleShowFullAnswer = (item: SearchItem) => {
        onShowFullAnswer?.(item);
    };

    const customizeRenderEmpty = () => (
        <Empty imageStyle={{ height: 48 }} description={false} />
    );

    const getTabItems = () => {
        const TAB_NAMES = [
            t("Tabs.All"),
            t("Tabs.Doc"),
            t("Tabs.ForumQA"),
            t("Tabs.ForumTutorial"),
        ];
        return TAB_ICONS.map((Icon, index) => {
            const id = String(index + 1);
            const dataSource = list.filter(
                (item) =>
                    CATEGORIES[index] === "" ||
                    CATEGORIES[index] === item.payload["collection_category"]
            );

            const offset: [number, number] =
                dataSource.length >= 10 ? [16, 0] : [8, 0];

            return {
                key: id,
                label: (
                    <Badge
                        color="#CCCCCC"
                        count={dataSource.length}
                        size="small"
                        offset={offset}
                    >
                        {TAB_NAMES[index]}
                    </Badge>
                ),
                disabled: dataSource.length === 0,
                children: (
                    <ConfigProvider renderEmpty={customizeRenderEmpty}>
                        <List
                            style={{ overflow: "auto" }}
                            loading={loading}
                            itemLayout="vertical"
                            dataSource={dataSource}
                            renderItem={(item: SearchItem) => (
                                <List.Item>
                                    <HitItem
                                        item={item}
                                        onShowFullAnswer={handleShowFullAnswer}
                                    />
                                </List.Item>
                            )}
                        />
                    </ConfigProvider>
                ),
                icon: <Icon />,
            };
        });
    };

    return (
        <Tabs
            style={{ flex: "1" }}
            defaultActiveKey="1"
            items={getTabItems()}
        />
    );
};

export default HitList;
