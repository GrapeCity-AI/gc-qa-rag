import { useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Flex, MenuProps, message } from "antd";
import { RobotOutlined, RocketOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { MessageItem, SearchItem } from "../../types/Api";
import {
    getChatResult,
    getFeedbackResult,
    getSearchResult,
    getThinkResult,
} from "../../services/ApiService";
import {
    SearchMode,
    SearchModeNameKey,
    TextResourcesKey,
} from "../../types/Base";
import CustomFooter from "../../components/CustomFooter";
import {
    captureDivToClipboard,
    copyToClipboard,
    extractContentAfterDivider,
    raise_gtag_event,
} from "../../common/utils";
import { useSearchState } from "./hooks/useSearchState";
import SearchHeader from "./components/SearchHeader";
import SearchInput from "./components/SearchInput";
import AnswerSection from "./components/AnswerSection";
import SearchResults from "./components/SearchResults";
import { useTranslation } from "react-i18next";
import { useProducts } from "../../hooks/useProducts";

interface RetrivalItem {
    key: number;
    query: string;
    answer: {
        reasoning_content?: string;
        content: string;
        loading: boolean;
        typing: boolean;
        asking: boolean;
        collapsed: boolean;
        liked: boolean;
        disliked: boolean;
    };
    search: {
        results: SearchItem[];
        loading: boolean;
        collapsed: boolean;
    };
}

const convertToMessages = (retrivals: RetrivalItem[]) => {
    const messages = retrivals.reduce((acc, curr) => {
        if (curr.query !== "") {
            acc.push({
                role: "user",
                content: curr.query,
            });
        }

        if (curr.answer.content !== "") {
            acc.push({
                role: "assistant",
                content: curr.answer.content,
            });
        }

        return acc;
    }, [] as MessageItem[]);
    return messages;
};

const searchModeIcons = {
    [SearchMode.Chat]: <RobotOutlined />,
    [SearchMode.Think]: <RocketOutlined />,
};

const SearchPage = () => {
    const { t } = useTranslation();
    const {
        products,
        loading: productsLoading,
        mode,
        selectedProduct,
        switchMode,
        selectProduct,
    } = useProducts();
    const {
        searchMode,
        setSearchMode,
        inputValue,
        setInputValue,
        retrivals,
        setRetrivals,
        controller,
        setController,
        shouldSearchOnModeChange,
        retrivalsUUID,
        appendMessageMap,
    } = useSearchState();

    const [messageApi, contextHolder] = message.useMessage();
    const navigate = useNavigate();

    const refreshUI = () => {
        setRetrivals([...retrivals]);
    };

    const createNewRetrivalItem = (newQuery: string): RetrivalItem => ({
        key: retrivals.length,
        query: newQuery,
        answer: {
            reasoning_content: "",
            content: "",
            loading: false,
            typing: false,
            asking: false,
            collapsed: false,
            liked: false,
            disliked: false,
        },
        search: {
            results: [],
            collapsed: false,
            loading: false,
        },
    });

    const loadSearchResult = async (item: RetrivalItem) => {
        if (item.query === "") {
            item.search.loading = false;
            item.search.results = [];
            refreshUI();
        } else {
            item.search.loading = true;
            const res = await getSearchResult(
                item.query,
                searchMode,
                selectedProduct,
                retrivalsUUID.current,
                retrivals.length - 1
            );
            item.search.loading = false;
            item.search.results = res;
            refreshUI();
        }
    };

    const createNewChatMessage = (newQuery: string) => {
        if (searchMode !== SearchMode.Chat) return;

        const newItem = createNewRetrivalItem(newQuery);
        retrivals.push(newItem);
        refreshUI();

        appendMessageMap.current.set(retrivals.length - 1, "");
        loadSearchResult(newItem);

        let currentIndex = 0;
        const typeWrite = (text: string) => {
            if (currentIndex < text.length) {
                currentIndex += 1;
                const textContent = text.slice(0, currentIndex);
                newItem.answer.content = textContent;
                refreshUI();
                requestAnimationFrame(() => typeWrite(text));
            }
        };

        if (newQuery !== "") {
            let currentAnswer = "";
            newItem.answer.loading = true;
            newItem.answer.typing = true;
            refreshUI();

            const messages = convertToMessages(retrivals);

            getChatResult(
                newQuery,
                messages,
                selectedProduct,
                (e, end) => {
                    newItem.answer.loading = false;
                    refreshUI();

                    currentIndex = currentAnswer.length;
                    if (end) {
                        newItem.answer.typing = false;
                        refreshUI();
                        currentAnswer += e;
                        newItem.answer.content = currentAnswer;
                        refreshUI();
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
    };

    const createNewThinkMessage = (newQuery: string) => {
        if (searchMode !== SearchMode.Think) return;

        const newItem = createNewRetrivalItem(newQuery);
        retrivals.push(newItem);
        refreshUI();

        appendMessageMap.current.set(retrivals.length - 1, "");
        loadSearchResult(newItem);

        let currenReasoningContenttIndex = 0;
        const typeWriteReasoningContent = (text: string) => {
            if (currenReasoningContenttIndex < text.length) {
                currenReasoningContenttIndex += 1;
                const textContent = text.slice(0, currenReasoningContenttIndex);
                newItem.answer.reasoning_content = textContent;
                refreshUI();
                requestAnimationFrame(() => typeWriteReasoningContent(text));
            }
        };

        let currentIndex = 0;
        const typeWrite = (text: string) => {
            if (currentIndex < text.length) {
                currentIndex += 1;
                const textContent = text.slice(0, currentIndex);
                newItem.answer.content = textContent;
                refreshUI();
                requestAnimationFrame(() => typeWrite(text));
            }
        };

        if (newQuery !== "") {
            let currentAnswerReasoningContent = "";
            let currentAnswerContent = "";
            newItem.answer.loading = true;
            newItem.answer.typing = true;
            refreshUI();

            const messages = convertToMessages(retrivals);

            getThinkResult(
                newQuery,
                messages,
                selectedProduct,
                (e, end) => {
                    const newRValue = "";
                    const newCValue = e;

                    newItem.answer.loading = false;
                    refreshUI();

                    currenReasoningContenttIndex =
                        currentAnswerReasoningContent.length;
                    currentIndex = currentAnswerContent.length;

                    if (end) {
                        newItem.answer.typing = false;
                        refreshUI();
                        currentAnswerReasoningContent += newRValue;
                        newItem.answer.reasoning_content =
                            currentAnswerReasoningContent;
                        currentAnswerContent += newCValue;
                        newItem.answer.content = currentAnswerContent;
                        refreshUI();
                    } else {
                        if (newRValue != "") {
                            currentAnswerReasoningContent += newRValue;
                            typeWriteReasoningContent(
                                currentAnswerReasoningContent
                            );
                        }
                        if (newCValue !== "") {
                            currentAnswerContent += newCValue;
                            typeWrite(currentAnswerContent);
                        }
                    }
                },
                (controller) => {
                    setController(controller);
                }
            );
        }
    };

    const initialize = () => {
        if (inputValue) {
            const title =
                inputValue + " - " + t(TextResourcesKey.Common.WebsiteName);
            window.document.title = title;
        }

        if (inputValue) {
            if (searchMode === SearchMode.Chat) {
                createNewChatMessage(inputValue);
            } else if (searchMode === SearchMode.Think) {
                createNewThinkMessage(inputValue);
            } else {
                const newItem = createNewRetrivalItem(inputValue);
                retrivals.push(newItem);
                refreshUI();
                appendMessageMap.current.set(retrivals.length - 1, "");
                loadSearchResult(newItem);
            }
        }
    };

    useEffect(() => {
        initialize();
    }, []);

    useEffect(() => {
        if (shouldSearchOnModeChange.current) {
            handleSearch();
        }
    }, [searchMode]);

    const handlePause = () => {
        controller?.abort();
    };

    const onAppendSearchChanged = (index: number, value: string) => {
        appendMessageMap.current.set(index, value);
    };

    const handleAppendBoxPressEnter = (
        e: React.KeyboardEvent<HTMLTextAreaElement>,
        index: number
    ) => {
        if (e.key === "Enter" && !e.shiftKey) {
            handleAppendSearch(index);
        }
    };

    const handleAppendSearch = (index: number) => {
        const appendQuery = appendMessageMap.current.get(index);
        retrivals[index].answer.asking = false;
        retrivals[index].search.collapsed = true;
        if (index < retrivals.length - 1) {
            retrivals.splice(index + 1, retrivals.length - index - 1);
        }

        raise_gtag_event("search.answer.append");

        if (searchMode === SearchMode.Chat) {
            createNewChatMessage(appendQuery);
        } else if (searchMode === SearchMode.Think) {
            createNewThinkMessage(appendQuery);
        }
    };

    const handleGoHome = () => {
        const productArgStr = `product=${encodeURIComponent(selectedProduct)}`;
        const searchModeArgStr = `searchmode=${encodeURIComponent(
            searchMode ?? SearchMode.Chat
        )}`;
        const productModeArgStr = `productmode=${encodeURIComponent(mode)}`;
        window.document.title = t(TextResourcesKey.Common.WebsiteName);

        raise_gtag_event("search.gohome");

        navigate(
            `/home?${productArgStr}&${searchModeArgStr}&${productModeArgStr}`
        );
    };

    const handleSearch = () => {
        const queryArgStr = `query=${encodeURIComponent(inputValue)}`;
        const productArgStr = `product=${encodeURIComponent(selectedProduct)}`;
        const searchModeArgStr = `searchmode=${encodeURIComponent(
            searchMode ?? SearchMode.Chat
        )}`;
        const productModeArgStr = `productmode=${encodeURIComponent(mode)}`;

        raise_gtag_event("search.enter", {
            query: inputValue,
            product: selectedProduct,
            searchmode: searchMode,
            productmode: mode,
        });

        controller?.abort();
        retrivalsUUID.current = uuidv4();
        retrivals.splice(0, retrivals.length);
        setRetrivals([]);
        appendMessageMap.current.clear();

        navigate(
            `/search?${queryArgStr}&${productArgStr}&${searchModeArgStr}&${productModeArgStr}`
        );
        initialize();
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target?.value);
    };

    const handleProductChange = (value: string) => {
        selectProduct(value);

        controller?.abort();
        retrivalsUUID.current = uuidv4();
        retrivals.splice(0, retrivals.length);
        setRetrivals([]);
        appendMessageMap.current.clear();
    };

    const handleSearchModeChange = (value: SearchMode) => {
        shouldSearchOnModeChange.current = true;
        setSearchMode(value);
        sessionStorage.setItem("gcai-searchmode", value);
    };

    const searchModeItems: MenuProps["items"] = [
        {
            key: "1",
            label: (
                <a onClick={() => handleSearchModeChange(SearchMode.Chat)}>
                    {t(SearchModeNameKey[SearchMode.Chat])}
                </a>
            ),
            icon: searchModeIcons[SearchMode.Chat],
        },
        {
            key: "2",
            label: (
                <a onClick={() => handleSearchModeChange(SearchMode.Think)}>
                    {t(SearchModeNameKey[SearchMode.Think])}
                </a>
            ),
            icon: searchModeIcons[SearchMode.Think],
        },
    ];

    const likeAnswer = async (retrivalItem: RetrivalItem) => {
        retrivalItem.answer.liked = true;
        refreshUI();
        await getFeedbackResult(
            retrivalItem.query,
            retrivalItem.answer.content,
            1,
            "",
            selectedProduct
        );

        raise_gtag_event("search.answer.like");

        messageApi.open({
            type: "success",
            content: t("Search.Commited"),
            duration: 2,
        });
    };

    const dislikeAnswer = async (retrivalItem: RetrivalItem) => {
        retrivalItem.answer.disliked = true;
        refreshUI();
        await getFeedbackResult(
            retrivalItem.query,
            retrivalItem.answer.content,
            0,
            "",
            selectedProduct
        );

        raise_gtag_event("search.answer.dislike");

        messageApi.open({
            type: "success",
            content: t("Search.Commited"),
            duration: 2,
        });
    };

    const handleShowFullAnswer = (searchItem: SearchItem) => {
        raise_gtag_event("search.hit.expand");
        searchItem.show_full_answer = !searchItem.show_full_answer;
        refreshUI();
    };

    return (
        <Flex
            vertical
            style={{
                height: "100vh",
                width: "calc(100vw - 64px)",
                maxWidth: "1200px",
            }}
        >
            {contextHolder}
            <SearchHeader onGoHome={handleGoHome} />
            <Flex flex={1} vertical>
                <Flex
                    style={{ background: "white", margin: "16px 0px" }}
                    vertical
                >
                    <SearchInput
                        products={products}
                        productsLoading={productsLoading}
                        mode={mode}
                        selectedProduct={selectedProduct}
                        switchMode={switchMode}
                        searchMode={searchMode}
                        inputValue={inputValue}
                        onProductChange={handleProductChange}
                        onInputChange={handleInputChange}
                        onSearch={handleSearch}
                        searchModeItems={searchModeItems}
                    />

                    <Flex vertical>
                        {retrivals.map((retrivalItem, index) => (
                            <Flex vertical style={{ width: "100%" }}>
                                {(searchMode === SearchMode.Chat ||
                                    searchMode === SearchMode.Think) && (
                                    <AnswerSection
                                        retrivalItem={retrivalItem}
                                        index={index}
                                        onLike={() => likeAnswer(retrivalItem)}
                                        onDislike={() =>
                                            dislikeAnswer(retrivalItem)
                                        }
                                        onCopy={async () => {
                                            const copyText =
                                                searchMode === SearchMode.Think
                                                    ? extractContentAfterDivider(
                                                          retrivalItem.answer
                                                              .content
                                                      )
                                                    : retrivalItem.answer
                                                          .content;
                                            const success =
                                                await copyToClipboard(copyText);
                                            if (success) {
                                                raise_gtag_event(
                                                    "search.answer.copy"
                                                );
                                                messageApi.open({
                                                    type: "success",
                                                    content: t("Search.Copied"),
                                                    duration: 2,
                                                });
                                            }
                                        }}
                                        onCopyImage={async () => {
                                            const div = document.getElementById(
                                                "ais-answer-" + index
                                            ) as HTMLDivElement;
                                            const success =
                                                await captureDivToClipboard(
                                                    div,
                                                    16,
                                                    10
                                                );
                                            if (success) {
                                                raise_gtag_event(
                                                    "search.answer.copy_image"
                                                );
                                                messageApi.open({
                                                    type: "success",
                                                    content:
                                                        t("Search.CopiedImage"),
                                                    duration: 2,
                                                });
                                            }
                                        }}
                                        onAskMore={() => {
                                            retrivalItem.answer.asking =
                                                !retrivalItem.answer.asking;
                                            refreshUI();
                                        }}
                                        onAppendSearch={() =>
                                            handleAppendSearch(index)
                                        }
                                        onAppendSearchChanged={(value) =>
                                            onAppendSearchChanged(index, value)
                                        }
                                        onAppendBoxPressEnter={(e) =>
                                            handleAppendBoxPressEnter(e, index)
                                        }
                                        onPause={handlePause}
                                        searchMode={searchMode}
                                    />
                                )}
                                <SearchResults
                                    retrivalItem={retrivalItem}
                                    onShowFullAnswer={handleShowFullAnswer}
                                    retrivals={retrivals}
                                    refreshUI={refreshUI}
                                />
                            </Flex>
                        ))}
                    </Flex>
                </Flex>
            </Flex>
            <CustomFooter />
        </Flex>
    );
};

export default SearchPage;
