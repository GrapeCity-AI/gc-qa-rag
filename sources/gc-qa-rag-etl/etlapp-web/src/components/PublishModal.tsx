import React, { useState, useEffect } from "react";
import { Modal, Space, Typography, Input, Button, Divider } from "antd";
import { fetchConfig } from "../api/ApiService";

const { Text } = Typography;

interface PublishModalProps {
    open: boolean;
    product: string;
    publishTag: string;
    setPublishTag: (v: string) => void;
    onCancel: () => void;
    onOk: () => void;
    onUpdateAliases: () => void;
    confirmLoading: boolean;
    updateAliasesLoading: boolean;
}

const PublishModal: React.FC<PublishModalProps> = ({
    open,
    product,
    publishTag,
    setPublishTag,
    onCancel,
    onOk,
    onUpdateAliases,
    confirmLoading,
    updateAliasesLoading,
}) => {
    const [vectorDbHost, setVectorDbHost] = useState<string>("");
    const [configLoading, setConfigLoading] = useState<boolean>(false);

    useEffect(() => {
        if (open) {
            loadConfig();
        }
    }, [open]);

    const loadConfig = async () => {
        setConfigLoading(true);
        try {
            const config = await fetchConfig();
            setVectorDbHost(config.vector_db?.host || "");
        } catch (error) {
            console.error("获取配置失败:", error);
        } finally {
            setConfigLoading(false);
        }
    };

    return (
        <Modal
            open={open}
            title="发布到向量数据库"
            onCancel={onCancel}
            footer={[
                <Button key="cancel" onClick={onCancel}>
                    取消
                </Button>,
                <Button
                    key="updateAliases"
                    type="dashed"
                    loading={updateAliasesLoading}
                    disabled={!publishTag || confirmLoading}
                    onClick={onUpdateAliases}
                >
                    更新别名
                </Button>,
                <Button
                    key="publish"
                    type="primary"
                    loading={confirmLoading}
                    disabled={!publishTag || updateAliasesLoading}
                    onClick={onOk}
                >
                    发布
                </Button>,
            ]}
        >
            <Space direction="vertical" style={{ width: "100%" }}>
                <Text>当前产品: {product}</Text>
                <Text>
                    发布目标:{" "}
                    {configLoading ? "加载中..." : vectorDbHost || "未配置"}
                </Text>
                <Text type="secondary">请输入发布标签(tag)，用于版本管理</Text>
                <Input
                    placeholder="输入标签，如: 230501"
                    value={publishTag}
                    onChange={(e) => setPublishTag(e.target.value)}
                />
                <Divider />
                <Text type="secondary">
                    • 发布: 将当前产品的数据发布到向量数据库
                </Text>
                <Text type="secondary">
                    • 更新别名: 更新向量数据库中的集合别名，用于切换版本
                </Text>
            </Space>
        </Modal>
    );
};

export default PublishModal;
