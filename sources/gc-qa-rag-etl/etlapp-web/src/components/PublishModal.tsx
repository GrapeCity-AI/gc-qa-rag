import React from "react";
import { Modal, Space, Typography, Input } from "antd";

const { Text } = Typography;

interface PublishModalProps {
    open: boolean;
    product: string;
    publishTag: string;
    setPublishTag: (v: string) => void;
    onCancel: () => void;
    onOk: () => void;
    confirmLoading: boolean;
}

const PublishModal: React.FC<PublishModalProps> = ({
    open,
    product,
    publishTag,
    setPublishTag,
    onCancel,
    onOk,
    confirmLoading,
}) => (
    <Modal
        open={open}
        title="发布到向量数据库"
        onCancel={onCancel}
        onOk={onOk}
        confirmLoading={confirmLoading}
    >
        <Space direction="vertical" style={{ width: "100%" }}>
            <Text>当前产品: {product}</Text>
            <Text type="secondary">请输入发布标签(tag)，用于版本管理</Text>
            <Input
                placeholder="输入标签，如: 230501"
                value={publishTag}
                onChange={(e) => setPublishTag(e.target.value)}
            />
        </Space>
    </Modal>
);

export default PublishModal;
