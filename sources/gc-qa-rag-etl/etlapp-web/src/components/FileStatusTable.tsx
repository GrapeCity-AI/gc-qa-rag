import React from "react";
import { Table, Button, Spin } from "antd";

interface FileStatusTableProps {
    etlFileRows: any[];
    selectedRowKeys: React.Key[];
    setSelectedRowKeys: (keys: React.Key[]) => void;
    handleDasProcess: (row: any) => void;
    handleEtlProcess: (row: any, etlType: "embedding" | "qa" | "full") => void;
    handlePreview: (row: any, stage: "das" | "embedding" | "qa" | "full") => void;
    processing: { [k: string]: boolean };
}

const FileStatusTable: React.FC<FileStatusTableProps> = ({
    etlFileRows,
    selectedRowKeys,
    setSelectedRowKeys,
    handleDasProcess,
    handleEtlProcess,
    handlePreview,
    processing,
}) => (
    <Table
        rowKey="filename"
        columns={[
            {
                title: "文件名",
                dataIndex: "filename",
                key: "filename",
                width: 220,
                ellipsis: true,
            },
            {
                title: "上传时间",
                dataIndex: "uploadTime",
                key: "uploadTime",
                width: 160,
                ellipsis: true,
            },
            {
                title: "DAS处理",
                key: "das",
                width: 120,
                render: (_: any, row: any) => {
                    if (row.das.status === "done")
                        return (
                            <Button size="small" onClick={() => handlePreview(row, "das")}>预览</Button>
                        );
                    if (processing[row.filename + ":das"])
                        return <Spin size="small" />;
                    return (
                        <Button size="small" type="primary" onClick={() => handleDasProcess(row)}>
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "Embedding",
                key: "embedding",
                width: 120,
                render: (_: any, row: any) => {
                    if (row.embedding.status === "done")
                        return (
                            <Button size="small" onClick={() => handlePreview(row, "embedding")}>预览</Button>
                        );
                    if (processing[row.filename + ":embedding"])
                        return <Spin size="small" />;
                    return (
                        <Button size="small" type="primary" onClick={() => handleEtlProcess(row, "embedding")}>
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "QA",
                key: "qa",
                width: 120,
                render: (_: any, row: any) => {
                    if (row.qa.status === "done")
                        return (
                            <Button size="small" onClick={() => handlePreview(row, "qa")}>预览</Button>
                        );
                    if (processing[row.filename + ":qa"])
                        return <Spin size="small" />;
                    return (
                        <Button size="small" type="primary" onClick={() => handleEtlProcess(row, "qa")}>
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "FullAnswer",
                key: "full",
                width: 120,
                render: (_: any, row: any) => {
                    if (row.full.status === "done")
                        return (
                            <Button size="small" onClick={() => handlePreview(row, "full")}>预览</Button>
                        );
                    if (processing[row.filename + ":full"])
                        return <Spin size="small" />;
                    return (
                        <Button size="small" type="primary" onClick={() => handleEtlProcess(row, "full")}>
                            处理
                        </Button>
                    );
                },
            },
        ]}
        dataSource={etlFileRows}
        rowSelection={{
            selectedRowKeys,
            onChange: (selectedKeys) => setSelectedRowKeys(selectedKeys),
        }}
        pagination={{ pageSize: 8 }}
        style={{ marginTop: 0, borderRadius: 8 }}
    />
);

export default FileStatusTable; 