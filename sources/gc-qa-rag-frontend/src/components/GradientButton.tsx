import { useContext } from "react";
import { Button, ConfigProvider, Space } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { css } from "@emotion/css";
import { useTranslation } from "react-i18next";

interface IProps {
    onClick: () => void;
}
const GradientButton = (props: IProps) => {
    const { getPrefixCls } = useContext(ConfigProvider.ConfigContext);
    const { t } = useTranslation();
    const rootPrefixCls = getPrefixCls();
    const linearGradientButton = css`
        &.${rootPrefixCls}-btn-primary:not([disabled]):not(
                .${rootPrefixCls}-btn-dangerous
            ) {
            border-width: 0;

            > span {
                position: relative;
            }

            &::before {
                content: "";
                background: linear-gradient(135deg, #6253e1, #04befe);
                position: absolute;
                inset: 0;
                opacity: 1;
                transition: all 0.3s;
                border-radius: inherit;
            }

            &:hover::before {
                opacity: 0;
            }
        }
    `;
    return (
        <ConfigProvider
            button={{
                className: linearGradientButton,
            }}
        >
            <Space>
                <Button
                    type="primary"
                    size="large"
                    icon={<SearchOutlined />}
                    onClick={props.onClick}
                >
                    {t("Button.Search")}
                </Button>
            </Space>
        </ConfigProvider>
    );
};

export default GradientButton;
