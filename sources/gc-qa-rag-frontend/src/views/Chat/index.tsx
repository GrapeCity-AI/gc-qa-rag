import {
    Alert,
    Avatar,
    Button,
    Divider,
    Flex,
    Input,
    Segmented,
    Space,
    Tooltip,
} from "antd";
import GradientButton from "../../components/GradientButton";
import {
    ExpandAltOutlined,
    FileSearchOutlined,
    HighlightOutlined,
    PlusOutlined,
    RobotOutlined,
} from "@ant-design/icons";
import Title from "antd/es/typography/Title";
import HitList from "../../components/HitList";
import { useRef, useState } from "react";
import { getChatResult, getSearchResult } from "../../services/ApiService";
import { Markdown } from "../../components/Markdown";
import { MessageItem } from "../../types/Api";
import "./index.css";
import {
    ProductType,
    ProductNameKey,
    TextResourcesKey,
} from "../../types/Base";
import CustomFooter from "../../components/CustomFooter";
import { useTranslation } from "react-i18next";

const ChatPage = () => {
    const { t } = useTranslation();
    const isChatCollapsedStored =
        localStorage.getItem("gcai-chat-collapsed") === "false" ? false : true;
    const keywordRef = useRef("");
    const productRef = useRef("Forguncy");
    const [inputValue, setInputValue] = useState("");
    const [_, setKeyword] = useState("");
    const [answer, setAnswer] = useState("");
    const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState([] as MessageItem[]);
    const [isChatCollapsed, setIsChatCollapsed] = useState(
        isChatCollapsedStored
    );
    const [__, setController] = useState<AbortController>();

    const [searchLoading, setSearchLoading] = useState(false);
    const [searchList, setSearchList] = useState([]);

    const createSearchResult = (query: string) => {
        if (query === "") {
            setSearchLoading(false);
            setSearchList([]);
        } else {
            setSearchLoading(true);
            getSearchResult(query, "chat", productRef.current, "", 0).then(
                (res) => {
                    setSearchLoading(false);
                    setSearchList(res);
                }
            );
        }
    };

    const handleNewChat = () => {
        setInputValue("");
        setKeyword("");
        setAnswer("");
        setMessages([]);
    };

    const handleSearch = () => {
        setInputValue(keywordRef.current);
        setKeyword(keywordRef.current);

        createSearchResult(keywordRef.current);

        if (isChatCollapsed) {
            return;
        }

        messages.push({
            role: "user",
            content: keywordRef.current,
        });

        let currentIndex = 0;
        const typeWrite = (text: string) => {
            if (currentIndex < text.length) {
                currentIndex += 1;
                const textContent = text.slice(0, currentIndex);
                setAnswer(textContent);
                setTimeout(() => typeWrite(text), 20);
            }
        };

        setTimeout(() => {
            if (keywordRef.current !== "") {
                let currentAnswer = "";
                setLoading(true);
                getChatResult(
                    keywordRef.current,
                    messages,
                    productRef.current,
                    (e, end) => {
                        setLoading(false);
                        currentIndex = currentAnswer.length;
                        if (end) {
                            setAnswer("");
                            setMessages([
                                ...messages,
                                {
                                    role: "assistant",
                                    content: currentAnswer,
                                },
                            ]);
                        } else {
                            currentAnswer += e;
                            typeWrite(currentAnswer);
                        }
                    },
                    (controller) => {
                        setController(controller);
                    }
                );
            }
        }, 10);
    };

    const handleKeywordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target?.value);
        keywordRef.current = e.target?.value;
    };

    const handleProductChange = (value: string) => {
        productRef.current = value;
        setInputValue("");
    };

    return (
        <Flex vertical style={{ height: "100vh", width: "90vw" }}>
            <Flex>
                <Title
                    level={2}
                    style={{
                        background:
                            "linear-gradient(270deg, #AE79CC 3%, #1366EC 96%)",
                        backgroundClip: "text",
                        color: "transparent",
                    }}
                >
                    {t("Common.WebsiteName")}
                </Title>
            </Flex>
            <Flex
                flex={"1 1 0"}
                style={{
                    maxHeight: "calc(100vh - 216px)",
                    marginBottom: "16px",
                }}
            >
                {!isChatCollapsed && (
                    <Flex
                        vertical
                        flex={"2 1 0"}
                        style={{ marginRight: "16px" }}
                    >
                        <Flex
                            vertical
                            className="answer-box"
                            style={{ width: "100%", height: "100%" }}
                        >
                            <Flex align="center">
                                <Flex flex={"1 1 0"}>
                                    <Divider
                                        orientationMargin="0"
                                        orientation="left"
                                    >
                                        <HighlightOutlined
                                            style={{ marginRight: "4px" }}
                                        />
                                        {t("Search.AIChat")}
                                    </Divider>
                                </Flex>
                                {!isChatCollapsed && (
                                    <Button
                                        icon={<ExpandAltOutlined />}
                                        size="small"
                                        type="text"
                                        onClick={() => {
                                            const newValue = !isChatCollapsed;
                                            setIsChatCollapsed(newValue);
                                            localStorage.setItem(
                                                "gcai-chat-collapsed",
                                                newValue ? "true" : "false"
                                            );
                                        }}
                                    >
                                        {t("Search.Collapse")}
                                    </Button>
                                )}
                            </Flex>

                            <div
                                style={{
                                    width: "100%",
                                    height: "100%",
                                    overflow: "auto",
                                }}
                            >
                                <Space
                                    direction="vertical"
                                    style={{ width: "100%" }}
                                >
                                    {messages.map((v, i) => {
                                        return (
                                            <Flex
                                                justify={
                                                    v.role === "user"
                                                        ? "right"
                                                        : "left"
                                                }
                                            >
                                                {v.role === "assistant" ? (
                                                    <Avatar
                                                        icon={<RobotOutlined />}
                                                        style={{
                                                            marginRight: "8px",
                                                            flexShrink: 0,
                                                        }}
                                                    />
                                                ) : (
                                                    <></>
                                                )}
                                                <Alert
                                                    key={i}
                                                    message={
                                                        <Markdown
                                                            content={v.content}
                                                        ></Markdown>
                                                    }
                                                    type={
                                                        v.role === "user"
                                                            ? "success"
                                                            : "info"
                                                    }
                                                />
                                            </Flex>
                                        );
                                    })}
                                    {loading ||
                                    (answer && answer.length > 0) ? (
                                        <Flex justify={"left"}>
                                            <Avatar
                                                icon={<RobotOutlined />}
                                                style={{
                                                    marginRight: "8px",
                                                    flexShrink: 0,
                                                }}
                                            />
                                            <Alert
                                                message={
                                                    <Markdown
                                                        content={answer}
                                                        loading={loading}
                                                    ></Markdown>
                                                }
                                            ></Alert>
                                        </Flex>
                                    ) : null}
                                </Space>
                            </div>
                        </Flex>
                    </Flex>
                )}
                <Flex vertical flex={"1 1 0"}>
                    <Flex align="center">
                        <Flex flex={"1 1 0"}>
                            <Divider orientationMargin="0" orientation="left">
                                <FileSearchOutlined
                                    style={{ marginRight: "4px" }}
                                />
                                {t("Search.SearchResults")}
                            </Divider>
                        </Flex>
                        {isChatCollapsed && (
                            <Button
                                icon={<ExpandAltOutlined />}
                                size="small"
                                type="text"
                                onClick={() => {
                                    const newValue = !isChatCollapsed;
                                    setIsChatCollapsed(newValue);
                                    localStorage.setItem(
                                        "gcai-chat-collapsed",
                                        newValue ? "true" : "false"
                                    );
                                }}
                            >
                                {t("Search.Expand")}
                            </Button>
                        )}
                    </Flex>

                    <HitList
                        list={searchList}
                        loading={searchLoading}
                        onShowFullAnswer={(searchItem) => {
                            searchItem.show_full_answer =
                                !searchItem.show_full_answer;
                            setSearchList([...searchList]);
                        }}
                    />
                </Flex>
            </Flex>
            <Flex vertical>
                <Space direction="vertical">
                    <Segmented
                        options={Object.keys(ProductNameKey).map(
                            (key: string) => ({
                                label: t(ProductNameKey[key as ProductType]),
                                value: key as ProductType,
                            })
                        )}
                        onChange={(value) => {
                            handleProductChange(value);
                        }}
                    />
                    <Flex>
                        <Input
                            value={inputValue}
                            placeholder={t(
                                TextResourcesKey.Home.SearchPlaceholder
                            )}
                            onChange={handleKeywordChange}
                            allowClear
                            size="large"
                            style={{ marginRight: "10px" }}
                            onPressEnter={handleSearch}
                        />
                        <Space>
                            <GradientButton onClick={handleSearch} />
                            {!isChatCollapsed && (
                                <Tooltip title={t("Button.NewChat")}>
                                    <Button
                                        style={{ color: "gray" }}
                                        type="dashed"
                                        icon={<PlusOutlined />}
                                        onClick={handleNewChat}
                                    ></Button>
                                </Tooltip>
                            )}
                        </Space>
                    </Flex>
                    <CustomFooter></CustomFooter>
                </Space>
            </Flex>
        </Flex>
    );
};

export default ChatPage;
