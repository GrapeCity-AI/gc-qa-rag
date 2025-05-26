import React, { useState, useEffect } from "react";
import {
    Button,
    Select,
    message,
    Modal,
    Input,
    Upload,
    Table,
    Card,
    Space,
    Typography,
    Spin,
} from "antd";
import { PlusOutlined, UploadOutlined } from "@ant-design/icons";

const API_BASE = "http://127.0.0.1:8000/generic";

// 公共
const fetchProducts = async () => {
    const res = await fetch(`${API_BASE}/products`);
    return (await res.json()).products as string[];
};

// 获取所有文件及其全流程状态
const fetchFilesStatus = async (product: string) => {
    const res = await fetch(`${API_BASE}/files_status?product=${product}`);
    return (await res.json()).files as any[];
};

const createProduct = async (product: string) => {
    const form = new FormData();
    form.append("product", product);
    const res = await fetch(`${API_BASE}/create_product`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error((await res.json()).detail || "创建失败");
    return await res.json();
};

const GenericETL: React.FC = () => {
    // DAS 相关 state
    const [product, setProduct] = useState<string>("default");
    const [previewModal, setPreviewModal] = useState(false);
    const [previewContent, setPreviewContent] = useState<any>(null);
    const [previewTitle, setPreviewTitle] = useState("");

    // 公共
    const [products, setProducts] = useState<string[]>([]);
    const [newProductModal, setNewProductModal] = useState(false);
    const [newProductName, setNewProductName] = useState("");

    // 发布相关
    const [publishModal, setPublishModal] = useState(false);
    const [publishTag, setPublishTag] = useState("");
    const [publishing, setPublishing] = useState(false);

    // 新表格数据
    const [etlFileRows, setEtlFileRows] = useState<any[]>([]);
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

    // 处理loading
    const [processing, setProcessing] = useState<{ [k: string]: boolean }>({});

    // DAS 相关 effect
    useEffect(() => {
        fetchProducts().then(setProducts);
    }, []);

    useEffect(() => {
        if (products.length && !products.includes(product)) {
            setProduct(products[0]);
        }
    }, [products]);

    useEffect(() => {
        if (product) {
            fetchFilesStatus(product).then(setEtlFileRows);
        }
    }, [product]);

    // 公共
    const handleCreateProduct = async () => {
        if (!newProductName) return;
        try {
            await createProduct(newProductName);
            message.success("产品创建成功");
            setNewProductModal(false);
            setNewProductName("");
            fetchProducts().then(setProducts);
        } catch (e: any) {
            message.error(e.message || "创建失败");
        }
    };

    // 单文件 DAS 处理
    const handleDasProcess = async (row: any) => {
        setProcessing((p) => ({ ...p, [row.filename + ":das"]: true }));
        const form = new FormData();
        form.append("product", product);
        await fetch(`${API_BASE}/das_start`, { method: "POST", body: form });
        setProcessing((p) => ({ ...p, [row.filename + ":das"]: false }));
        // 简单延迟后刷新
        setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
    };

    // 单文件 ETL 处理
    const handleEtlProcess = async (
        row: any,
        etlType: "embedding" | "qa" | "full"
    ) => {
        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: true }));
        const form = new FormData();
        form.append("product", product);
        form.append("etl_type", etlType);
        await fetch(`${API_BASE}/etl_start`, { method: "POST", body: form });
        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: false }));
        setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
    };

    // 批量处理
    const handleBatchProcess = async (
        stage: "das" | "embedding" | "qa" | "full"
    ) => {
        for (const row of etlFileRows.filter((r) =>
            selectedRowKeys.includes(r.filename)
        )) {
            if (stage === "das" && row.das.status === "not_started") {
                await handleDasProcess(row);
            } else if (
                ["embedding", "qa", "full"].includes(stage) &&
                row[stage].status === "not_started"
            ) {
                await handleEtlProcess(row, stage as any);
            }
        }
        fetchFilesStatus(product).then(setEtlFileRows);
    };

    // 单文件内容预览
    const handlePreview = async (
        row: any,
        stage: "das" | "embedding" | "qa" | "full"
    ) => {
        let content = null;
        let title = "";
        if (stage === "das" && row.das.resultFile) {
            const res = await fetch(
                `${API_BASE}/das_result_content?product=${product}&filename=${row.das.resultFile}`
            );
            content = await res.json();
            title = `${row.filename} - DAS`;
        } else if (
            (stage === "embedding" || stage === "qa" || stage === "full") &&
            row[stage].resultFile
        ) {
            const etlType = stage;
            const res = await fetch(
                `${API_BASE}/etl_result_content?product=${product}&etl_type=${etlType}&filename=${row[stage].resultFile}`
            );
            content = await res.json();
            title = `${row.filename} - ${stage}`;
        }
        setPreviewContent(content);
        setPreviewTitle(title);
        setPreviewModal(true);
    };

    // 发布到向量数据库
    const handlePublish = async () => {
        if (!publishTag) {
            message.error("请输入发布标签");
            return;
        }
        setPublishing(true);
        try {
            const form = new FormData();
            form.append("product", product);
            form.append("tag", publishTag);
            const res = await fetch(`${API_BASE}/publish`, {
                method: "POST",
                body: form,
            });
            await res.json();
            message.success("发布任务已启动");
            setPublishModal(false);
            setPublishTag("");
        } catch (e) {
            message.error("发布失败");
        } finally {
            setPublishing(false);
        }
    };

    const { Title, Text } = Typography;

    return (
        <div
            style={{
                maxWidth: 1100,
                margin: "40px auto",
                background: "#f5f7fa",
                padding: 32,
                borderRadius: 12,
            }}
        >
            <Card style={{ marginBottom: 24, boxShadow: "0 2px 8px #f0f1f2" }}>
                <Title level={3} style={{ marginBottom: 16 }}>
                    Generic ETL 流程演示
                </Title>
                <Space
                    size="large"
                    align="center"
                    style={{
                        width: "100%",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                    }}
                >
                    <Space>
                        <Text strong>选择产品：</Text>
                        <Select
                            style={{ width: 180 }}
                            value={product}
                            onChange={setProduct}
                            options={products.map((p) => ({
                                label: p,
                                value: p,
                            }))}
                        />
                        <Button
                            icon={<PlusOutlined />}
                            type="primary"
                            onClick={() => setNewProductModal(true)}
                        >
                            新建产品
                        </Button>
                        <Upload
                            multiple
                            showUploadList={false}
                            customRequest={async ({
                                file,
                                onSuccess,
                                onError,
                            }) => {
                                const formData = new FormData();
                                formData.append("product", product);
                                formData.append("file", file);
                                try {
                                    await fetch(`${API_BASE}/das_upload`, {
                                        method: "POST",
                                        body: formData,
                                    });
                                    message.success("上传成功");
                                    fetchFilesStatus(product).then(
                                        setEtlFileRows
                                    );
                                    if (onSuccess) onSuccess({}, file);
                                } catch (e) {
                                    message.error("上传失败");
                                    if (onError) onError(e as any);
                                }
                            }}
                        >
                            <Button icon={<UploadOutlined />}>上传文件</Button>
                        </Upload>
                    </Space>
                    <Button
                        type="primary"
                        onClick={() => setPublishModal(true)}
                    >
                        发布到向量库
                    </Button>
                </Space>
            </Card>

            {/* 发布Modal */}
            <Modal
                open={publishModal}
                title="发布到向量数据库"
                onCancel={() => setPublishModal(false)}
                onOk={handlePublish}
                confirmLoading={publishing}
            >
                <Space direction="vertical" style={{ width: "100%" }}>
                    <Text>当前产品: {product}</Text>
                    <Text type="secondary">
                        请输入发布标签(tag)，用于版本管理
                    </Text>
                    <Input
                        placeholder="输入标签，如: 230501"
                        value={publishTag}
                        onChange={(e) => setPublishTag(e.target.value)}
                    />
                </Space>
            </Modal>

            <Modal
                open={previewModal}
                title={previewTitle}
                onCancel={() => setPreviewModal(false)}
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
                    {previewContent
                        ? JSON.stringify(previewContent, null, 2)
                        : ""}
                </div>
            </Modal>
            <Modal
                open={newProductModal}
                title="新建产品"
                onCancel={() => setNewProductModal(false)}
                onOk={handleCreateProduct}
            >
                <Text type="secondary">
                    产品名称仅支持字母、数字、下划线，建议英文
                </Text>
                <Input
                    placeholder="输入新产品名称"
                    value={newProductName}
                    onChange={(e) => setNewProductName(e.target.value)}
                    style={{ marginTop: 8 }}
                />
            </Modal>
            <Card
                title={<b>文件全流程状态</b>}
                style={{ marginTop: 24, boxShadow: "0 2px 8px #f0f1f2" }}
                extra={
                    <Space>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("das")}
                        >
                            批量DAS处理
                        </Button>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("embedding")}
                        >
                            批量Embedding
                        </Button>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("qa")}
                        >
                            批量QA
                        </Button>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("full")}
                        >
                            批量Full
                        </Button>
                    </Space>
                }
                bodyStyle={{ padding: 0 }}
            >
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
                                        <Button
                                            size="small"
                                            onClick={() =>
                                                handlePreview(row, "das")
                                            }
                                        >
                                            预览
                                        </Button>
                                    );
                                if (processing[row.filename + ":das"])
                                    return <Spin size="small" />;
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
                            title: "Embedding",
                            key: "embedding",
                            width: 120,
                            render: (_: any, row: any) => {
                                if (row.embedding.status === "done")
                                    return (
                                        <Button
                                            size="small"
                                            onClick={() =>
                                                handlePreview(row, "embedding")
                                            }
                                        >
                                            预览
                                        </Button>
                                    );
                                if (processing[row.filename + ":embedding"])
                                    return <Spin size="small" />;
                                return (
                                    <Button
                                        size="small"
                                        type="primary"
                                        onClick={() =>
                                            handleEtlProcess(row, "embedding")
                                        }
                                    >
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
                                        <Button
                                            size="small"
                                            onClick={() =>
                                                handlePreview(row, "qa")
                                            }
                                        >
                                            预览
                                        </Button>
                                    );
                                if (processing[row.filename + ":qa"])
                                    return <Spin size="small" />;
                                return (
                                    <Button
                                        size="small"
                                        type="primary"
                                        onClick={() =>
                                            handleEtlProcess(row, "qa")
                                        }
                                    >
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
                                        <Button
                                            size="small"
                                            onClick={() =>
                                                handlePreview(row, "full")
                                            }
                                        >
                                            预览
                                        </Button>
                                    );
                                if (processing[row.filename + ":full"])
                                    return <Spin size="small" />;
                                return (
                                    <Button
                                        size="small"
                                        type="primary"
                                        onClick={() =>
                                            handleEtlProcess(row, "full")
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
                        onChange: (selectedKeys) =>
                            setSelectedRowKeys(selectedKeys),
                    }}
                    pagination={{ pageSize: 8 }}
                    style={{ marginTop: 0, borderRadius: 8 }}
                />
            </Card>
        </div>
    );
};

export default GenericETL;
