import { Flex } from "antd";
import Title from "antd/es/typography/Title";
import { SearchHeaderProps } from "../types";
import { useTranslation } from "react-i18next";
import { TextResourcesKey } from "../../../types/Base";

const SearchHeader = ({ onGoHome }: SearchHeaderProps) => {
    const { t } = useTranslation();
    return (
        <Flex>
            <a onClick={onGoHome}>
                <Title
                    level={2}
                    style={{
                        background:
                            "linear-gradient(270deg, #AE79CC 3%, #1366EC 96%)",
                        backgroundClip: "text",
                        color: "transparent",
                    }}
                >
                    {t(TextResourcesKey.Common.WebsiteName)}
                </Title>
            </a>
        </Flex>
    );
};

export default SearchHeader;
