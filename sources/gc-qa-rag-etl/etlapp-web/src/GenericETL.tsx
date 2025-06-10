import React, { useState, useEffect } from "react";
import { Button, Card, Space, Typography, message } from "antd";
import ProductSelector from "./components/ProductSelector";
import FileStatusTable from "./components/FileStatusTable";
import ServerLog from "./components/ServerLog";
import PublishModal from "./components/PublishModal";
import PreviewModal from "./components/PreviewModal";
import NewProductModal from "./components/NewProductModal";
import ConfigModal from "./components/ConfigModal";
import {
    fetchProducts,
    fetchFilesStatus,
    createProduct,
    fetchConfig,
    saveConfig,
    uploadFile,
    dasStart,
    etlStart,
    fetchDasResultContent,
    fetchEtlResultContent,
    publish,
    fetchServerLog,
} from "./api/ApiService";

const GenericETL: React.FC = () => {
    // DAS
    const [product, setProduct] = useState<string>("default");
    const [previewModal, setPreviewModal] = useState(false);
    const [previewContent, setPreviewContent] = useState<any>(null);
    const [previewTitle, setPreviewTitle] = useState("");
    const [products, setProducts] = useState<string[]>([]);
    const [newProductModal, setNewProductModal] = useState(false);
    const [newProductName, setNewProductName] = useState("");

    // Related to publishing
    const [publishModal, setPublishModal] = useState(false);
    const [publishTag, setPublishTag] = useState("");
    const [publishing, setPublishing] = useState(false);

    // New table data
    const [etlFileRows, setEtlFileRows] = useState<any[]>([]);
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

    // Handle loading
    const [processing, setProcessing] = useState<{ [k: string]: boolean }>({});

    // Added: log related state
    const [serverLog, setServerLog] = useState<string>("");

    // Added: config related state
    const [configModal, setConfigModal] = useState(false);
    const [config, setConfig] = useState<any>(null);
    const [configLoading, setConfigLoading] = useState(false);
    const [configSaving, setConfigSaving] = useState(false);

    // DAS 相关 effect
    // DAS related effect
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

    // Periodically fetch logs
    useEffect(() => {
        const fetchLog = async () => {
            try {
                const data = await fetchServerLog(100);
                setServerLog(data.log || "");
            } catch {
                setServerLog("日志获取失败");
            }
        };
        fetchLog();
        const timer = setInterval(fetchLog, 3000);
        return () => clearInterval(timer);
    }, []);

    // Create product
    const handleCreateProduct = async () => {
        if (!newProductName) return;
        try {
            await createProduct(newProductName);
            message.success("产品创建成功");
            setProduct(newProductName);
            setNewProductModal(false);
            setNewProductName("");
            fetchProducts().then(setProducts);
        } catch (e: any) {
            message.error(e.message || "创建失败");
        }
    };

    // Single file DAS processing
    const handleDasProcess = async (row: any) => {
        setProcessing((p) => ({ ...p, [row.filename + ":das"]: true }));
        await dasStart(product);
        setProcessing((p) => ({ ...p, [row.filename + ":das"]: false }));
        setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
    };

    // Single file ETL processing
    const handleEtlProcess = async (
        row: any,
        etlType: "embedding" | "qa" | "full"
    ) => {
        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: true }));
        await etlStart(product, etlType);
        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: false }));
        setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
    };

    // Batch processing
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

    // Single file content preview
    const handlePreview = async (
        row: any,
        stage: "das" | "embedding" | "qa" | "full"
    ) => {
        let content = null;
        let title = "";
        if (stage === "das" && row.das.resultFile) {
            content = await fetchDasResultContent(product, row.das.resultFile);
            title = `${row.filename} - DAS`;
        } else if (
            (stage === "embedding" || stage === "qa" || stage === "full") &&
            row[stage].resultFile
        ) {
            const etlType = stage;
            content = await fetchEtlResultContent(
                product,
                etlType,
                row[stage].resultFile
            );
            title = `${row.filename} - ${stage}`;
        }
        setPreviewContent(content);
        setPreviewTitle(title);
        setPreviewModal(true);
    };

    // Publish to vector database
    const handlePublish = async () => {
        if (!publishTag) {
            message.error("请输入发布标签");
            return;
        }
        setPublishing(true);
        try {
            await publish(product, publishTag);
            message.success("发布任务已启动");
            setPublishModal(false);
            setPublishTag("");
        } catch (e) {
            message.error("发布失败");
        } finally {
            setPublishing(false);
        }
    };

    const { Title } = Typography;

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
                    GC-QA-RAG Generic ETL 流程演示
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
                    <ProductSelector
                        products={products}
                        product={product}
                        setProduct={setProduct}
                        onNewProduct={() => setNewProductModal(true)}
                        onUpload={async (file) => {
                            await uploadFile(product, file);
                            message.success("上传成功");
                            fetchFilesStatus(product).then(setEtlFileRows);
                        }}
                    />
                    <Space>
                        <Button
                            onClick={() => {
                                setConfigModal(true);
                                setConfigLoading(true);
                                fetchConfig()
                                    .then((cfg) => setConfig(cfg))
                                    .finally(() => setConfigLoading(false));
                            }}
                        >
                            配置
                        </Button>
                        <Button
                            type="primary"
                            onClick={() => setPublishModal(true)}
                        >
                            发布到向量库
                        </Button>
                    </Space>
                </Space>
            </Card>
            <PublishModal
                open={publishModal}
                product={product}
                publishTag={publishTag}
                setPublishTag={setPublishTag}
                onCancel={() => setPublishModal(false)}
                onOk={handlePublish}
                confirmLoading={publishing}
            />
            <PreviewModal
                open={previewModal}
                title={previewTitle}
                content={previewContent}
                onCancel={() => setPreviewModal(false)}
            />
            <NewProductModal
                open={newProductModal}
                newProductName={newProductName}
                setNewProductName={setNewProductName}
                onCancel={() => setNewProductModal(false)}
                onOk={handleCreateProduct}
            />
            <ConfigModal
                open={configModal}
                config={config}
                configLoading={configLoading}
                configSaving={configSaving}
                setConfig={setConfig}
                onCancel={() => setConfigModal(false)}
                onOk={async () => {
                    setConfigSaving(true);
                    try {
                        await saveConfig(config);
                        setConfigModal(false);
                    } catch (e) {
                        message.error("保存失败");
                    } finally {
                        setConfigSaving(false);
                    }
                }}
            />
            <Card
                title={<b>文件全流程状态</b>}
                style={{ marginTop: 24, boxShadow: "0 2px 8px #f0f1f2" }}
                extra={
                    <Space>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("das")}
                        >
                            批量DAS
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
                            批量FullAnswer
                        </Button>
                        <Button
                            disabled={selectedRowKeys.length === 0}
                            onClick={() => handleBatchProcess("embedding")}
                        >
                            批量Embedding
                        </Button>
                    </Space>
                }
            >
                <FileStatusTable
                    etlFileRows={etlFileRows}
                    selectedRowKeys={selectedRowKeys}
                    setSelectedRowKeys={setSelectedRowKeys}
                    handleDasProcess={handleDasProcess}
                    handleEtlProcess={handleEtlProcess}
                    handlePreview={handlePreview}
                    processing={processing}
                />
            </Card>
            <Card
                title={<b>Server 控制台日志</b>}
                style={{ marginTop: 24, boxShadow: "0 2px 8px #f0f1f2" }}
            >
                <ServerLog serverLog={serverLog} />
            </Card>
        </div>
    );
};

export default GenericETL;
