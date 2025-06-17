import React from "react";
import { Table, Button, Spin, Progress } from "antd";

interface FileStatusTableProps {
    etlFileRows: any[];
    selectedRowKeys: React.Key[];
    setSelectedRowKeys: (keys: React.Key[]) => void;
    handleDasProcess: (row: any) => void;
    handleEtlProcess: (row: any, etlType: "embedding" | "qa" | "full") => void;
    handlePreview: (
        row: any,
        stage: "das" | "embedding" | "qa" | "full"
    ) => void;
    processing: { [k: string]: boolean };
    progressInfo: { [k: string]: { progress: number; msg: string } };
}

const FileStatusTable: React.FC<FileStatusTableProps> = ({
    etlFileRows,
    selectedRowKeys,
    setSelectedRowKeys,
    handleDasProcess,
    handleEtlProcess,
    handlePreview,
    processing,
    progressInfo,
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
                width: 150,
                render: (_: any, row: any) => {
                    if (row.das.status === "done")
                        return (
                            <Button
                                size="small"
                                onClick={() => handlePreview(row, "das")}
                            >
                                预览
                            </Button>
                        );
                    if (processing[row.filename + ":das"]) {
                        const progressKey = row.filename + ":das";
                        const progress = progressInfo[progressKey];
                        return (
                            <div style={{ width: 100 }}>
                                <Progress 
                                    percent={progress?.progress || 0} 
                                    size="small" 
                                    status="active"
                                />
                                {progress?.msg && (
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                        {progress.msg.length > 20 ? progress.msg.substring(0, 20) + '...' : progress.msg}
                                    </div>
                                )}
                            </div>
                        );
                    }
                    return (
                        <Button
                            size="small"
                            type="primary"
                            onClick={() => handleDasProcess(row)}
                        >
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "QA",
                key: "qa",
                width: 150,
                render: (_: any, row: any) => {
                    if (row.qa.status === "done")
                        return (
                            <Button
                                size="small"
                                onClick={() => handlePreview(row, "qa")}
                            >
                                预览
                            </Button>
                        );
                    if (processing[row.filename + ":qa"]) {
                        const progressKey = row.filename + ":qa";
                        const progress = progressInfo[progressKey];
                        return (
                            <div style={{ width: 100 }}>
                                <Progress 
                                    percent={progress?.progress || 0} 
                                    size="small" 
                                    status="active"
                                />
                                {progress?.msg && (
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                        {progress.msg.length > 20 ? progress.msg.substring(0, 20) + '...' : progress.msg}
                                    </div>
                                )}
                            </div>
                        );
                    }
                    return (
                        <Button
                            size="small"
                            type="primary"
                            onClick={() => handleEtlProcess(row, "qa")}
                            disabled={row.das.status !== "done"}
                        >
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "FullAnswer(可选)",
                key: "full",
                width: 150,
                render: (_: any, row: any) => {
                    if (row.full.status === "done")
                        return (
                            <Button
                                size="small"
                                onClick={() => handlePreview(row, "full")}
                            >
                                预览
                            </Button>
                        );
                    if (processing[row.filename + ":full"]) {
                        const progressKey = row.filename + ":full";
                        const progress = progressInfo[progressKey];
                        return (
                            <div style={{ width: 100 }}>
                                <Progress 
                                    percent={progress?.progress || 0} 
                                    size="small" 
                                    status="active"
                                />
                                {progress?.msg && (
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                        {progress.msg.length > 20 ? progress.msg.substring(0, 20) + '...' : progress.msg}
                                    </div>
                                )}
                            </div>
                        );
                    }
                    return (
                        <Button
                            size="small"
                            type="primary"
                            onClick={() => handleEtlProcess(row, "full")}
                            disabled={
                                row.das.status !== "done" ||
                                row.qa.status !== "done"
                            }
                        >
                            处理
                        </Button>
                    );
                },
            },
            {
                title: "Embedding",
                key: "embedding",
                width: 150,
                render: (_: any, row: any) => {
                    if (row.embedding.status === "done")
                        return (
                            <Button
                                size="small"
                                onClick={() => handlePreview(row, "embedding")}
                            >
                                预览
                            </Button>
                        );
                    if (processing[row.filename + ":embedding"]) {
                        const progressKey = row.filename + ":embedding";
                        const progress = progressInfo[progressKey];
                        return (
                            <div style={{ width: 100 }}>
                                <Progress 
                                    percent={progress?.progress || 0} 
                                    size="small" 
                                    status="active"
                                />
                                {progress?.msg && (
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                        {progress.msg.length > 20 ? progress.msg.substring(0, 20) + '...' : progress.msg}
                                    </div>
                                )}
                            </div>
                        );
                    }
                    return (
                        <Button
                            size="small"
                            type="primary"
                            onClick={() => handleEtlProcess(row, "embedding")}
                            disabled={
                                row.das.status !== "done" ||
                                row.qa.status !== "done"
                            }
                        >
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
