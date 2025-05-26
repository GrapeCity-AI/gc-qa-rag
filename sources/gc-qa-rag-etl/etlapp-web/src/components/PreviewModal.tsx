import React from "react";
import { Modal } from "antd";

interface PreviewModalProps {
    open: boolean;
    title: string;
    content: any;
    onCancel: () => void;
}

const PreviewModal: React.FC<PreviewModalProps> = ({
    open,
    title,
    content,
    onCancel,
}) => (
    <Modal
        open={open}
        title={title}
        onCancel={onCancel}
        footer={null}
        width={800}
    >
        <div
            style={{
                maxHeight: 500,
                overflow: "auto",
                borderRadius: 6,
                padding: 12,
            }}
        >
            {content ? JSON.stringify(content, null, 2) : ""}
        </div>
    </Modal>
);

export default PreviewModal; 