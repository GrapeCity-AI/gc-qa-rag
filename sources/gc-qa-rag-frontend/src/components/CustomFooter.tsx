import { Flex, Space } from "antd";
import { useTranslation } from "react-i18next";

const CustomFooter = () => {
    const { t } = useTranslation();
    return (
        <Flex align="center" justify="center">
            <Space
                style={{
                    textAlign: "center",
                    fontSize: "12px",
                    color: "#999",
                    padding: "8px",
                }}
                align="baseline"
            >
                <>{t("Common.Copyright", { year: new Date().getFullYear() })}</>
            </Space>
        </Flex>
    );
};

export default CustomFooter;
