import React, { useMemo } from "react";
import { Modal, Alert } from "antd";

interface PreviewModalProps {
    open: boolean;
    title: string;
    content: any;
    onCancel: () => void;
}

const MAX_PREVIEW_LENGTH = 100000; // 限制预览字符数为 100KB

const PreviewModal: React.FC<PreviewModalProps> = ({
    open,
    title,
    content,
    onCancel,
}) => {
    const { displayContent, isTruncated, totalSize, truncatedInfo } = useMemo(() => {
        if (!content) {
            return { displayContent: "", isTruncated: false, totalSize: 0, truncatedInfo: "" };
        }

        // 检查是否有数据层面的截断标记
        const dataLevelTruncated = content._truncated === true;
        const originalCount = content._originalCount || 0;
        let truncatedInfo = "";
        if (dataLevelTruncated) {
            const currentCount = content.Groups?.length || content.chunks?.length || 0;
            truncatedInfo = `数据已截断: 仅显示前 ${currentCount} 条，共 ${originalCount} 条`;
        }

        const fullJson = JSON.stringify(content, null, 2);
        const totalSize = fullJson.length;

        if (totalSize <= MAX_PREVIEW_LENGTH) {
            return { displayContent: fullJson, isTruncated: dataLevelTruncated, totalSize, truncatedInfo };
        }

        // 截断内容，保留前 MAX_PREVIEW_LENGTH 字符
        const truncated = fullJson.slice(0, MAX_PREVIEW_LENGTH);
        return {
            displayContent: truncated + "\n\n... (内容已截断)",
            isTruncated: true,
            totalSize,
            truncatedInfo: truncatedInfo || `内容过大，仅显示前 ${(MAX_PREVIEW_LENGTH / 1024).toFixed(0)} KB`,
        };
    }, [content]);

    return (
        <Modal
            open={open}
            title={title}
            onCancel={onCancel}
            footer={null}
            width={800}
        >
            {isTruncated && (
                <Alert
                    message={truncatedInfo || `内容过大 (${(totalSize / 1024 / 1024).toFixed(2)} MB)，仅显示前 ${(MAX_PREVIEW_LENGTH / 1024).toFixed(0)} KB`}
                    type="warning"
                    showIcon
                    style={{ marginBottom: 12 }}
                />
            )}
            <pre
                style={{
                    maxHeight: 500,
                    overflow: "auto",
                    borderRadius: 6,
                    padding: 12,
                    backgroundColor: "#f5f5f5",
                    fontSize: 12,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-all",
                }}
            >
                {displayContent}
            </pre>
        </Modal>
    );
};

export default PreviewModal;
