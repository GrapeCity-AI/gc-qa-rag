import { Alert, Divider, Flex, Space, Button } from "antd";
import { HighlightOutlined, PauseCircleOutlined } from "@ant-design/icons";
import { AnswerSectionProps } from "../types";
import { SearchMode } from "../../../types/Base";
import { Markdown } from "../../../components/Markdown";
import AnswerActions from "./AnswerActions";
import AnswerOptionsComponent from "../../../components/AnswerOptions";
import Title from "antd/es/typography/Title";
import { useTranslation } from "react-i18next";

const AnswerSection = ({
    retrivalItem,
    index,
    onLike,
    onDislike,
    onCopy,
    onCopyImage,
    onAskMore,
    onAppendSearch,
    onAppendSearchChanged,
    onAppendBoxPressEnter,
    onPause,
    searchMode,
}: AnswerSectionProps) => {
    const { t } = useTranslation();
    return (
        <Flex vertical id={"ais-answer-" + index}>
            {index > 0 && <Title level={2}>{retrivalItem.query}</Title>}
            <Flex align="center" justify="space-between">
                <Flex flex={1}>
                    <Divider orientationMargin="0" orientation="left">
                        <Space>
                            <HighlightOutlined />
                            {searchMode === SearchMode.Think
                                ? t("Answer.DeepThink")
                                : t("Answer.SmartAnswer")}
                        </Space>
                    </Divider>
                </Flex>
                {retrivalItem.answer.typing && (
                    <Flex style={{ marginLeft: "8px" }}>
                        <Button
                            icon={<PauseCircleOutlined />}
                            onClick={onPause}
                        >
                            {t("Answer.StopGenerating")}
                        </Button>
                    </Flex>
                )}
            </Flex>
            {retrivalItem.answer.reasoning_content && (
                <Alert
                    message={retrivalItem.answer.reasoning_content}
                    type="warning"
                />
            )}
            <Alert
                message={
                    <Markdown
                        content={retrivalItem.answer.content}
                        loading={retrivalItem.answer.loading}
                    />
                }
            />
            {!retrivalItem.answer.typing && (
                <AnswerActions
                    retrivalItem={retrivalItem}
                    index={index}
                    onLike={onLike}
                    onDislike={onDislike}
                    onCopy={onCopy}
                    onCopyImage={onCopyImage}
                    onAskMore={onAskMore}
                    onAppendSearch={onAppendSearch}
                    onAppendSearchChanged={onAppendSearchChanged}
                    onAppendBoxPressEnter={onAppendBoxPressEnter}
                />
            )}
        </Flex>
    );
};

export default AnswerSection;
