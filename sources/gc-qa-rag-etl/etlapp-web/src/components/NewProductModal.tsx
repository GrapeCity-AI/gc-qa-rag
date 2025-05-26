import React from "react";
import { Modal, Input, Typography } from "antd";

const { Text } = Typography;

interface NewProductModalProps {
    open: boolean;
    newProductName: string;
    setNewProductName: (v: string) => void;
    onCancel: () => void;
    onOk: () => void;
}

const NewProductModal: React.FC<NewProductModalProps> = ({
    open,
    newProductName,
    setNewProductName,
    onCancel,
    onOk,
}) => (
    <Modal open={open} title="新建产品" onCancel={onCancel} onOk={onOk}>
        <Text type="secondary">产品名称仅支持字母、数字、下划线，建议英文</Text>
        <Input
            placeholder="输入新产品名称"
            value={newProductName}
            onChange={(e) => setNewProductName(e.target.value)}
            style={{ marginTop: 8 }}
        />
    </Modal>
);

export default NewProductModal;
