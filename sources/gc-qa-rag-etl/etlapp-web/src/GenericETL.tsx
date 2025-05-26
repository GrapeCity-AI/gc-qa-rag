import React, { useState, useEffect } from "react";
import { Button, Card, Space, Typography, message } from "antd";
import ProductSelector from "./components/ProductSelector";
import FileStatusTable from "./components/FileStatusTable";
import ServerLog from "./components/ServerLog";
import PublishModal from "./components/PublishModal";
import PreviewModal from "./components/PreviewModal";
import NewProductModal from "./components/NewProductModal";
import ConfigModal from "./components/ConfigModal";

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

const fetchConfig = async () => {
    const res = await fetch(`${API_BASE}/get_config`);
    return await res.json();
};

const saveConfig = async (config: any) => {
    const res = await fetch(`${API_BASE}/update_config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("保存失败");
    message.success("配置已保存");
    return true;
};

const GenericETL: React.FC = () => {
    // DAS
    const [product, setProduct] = useState<string>("default");
    const [previewModal, setPreviewModal] = useState(false);
    const [previewContent, setPreviewContent] = useState<any>(null);
    const [previewTitle, setPreviewTitle] = useState("");
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

    // 新增：日志相关 state
    const [serverLog, setServerLog] = useState<string>("");

    // 新增：配置相关 state
    const [configModal, setConfigModal] = useState(false);
    const [config, setConfig] = useState<any>(null);
    const [configLoading, setConfigLoading] = useState(false);
    const [configSaving, setConfigSaving] = useState(false);

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

    // 定时拉取日志
    useEffect(() => {
        const fetchLog = async () => {
            try {
                const res = await fetch(`${API_BASE}/server_log?lines=100`);
                const data = await res.json();
                setServerLog(data.log || "");
            } catch {
                setServerLog("日志获取失败");
            }
        };
        fetchLog();
        const timer = setInterval(fetchLog, 3000); // 每3秒拉取一次
        return () => clearInterval(timer);
    }, []);

    // 创建产品
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
                            const formData = new FormData();
                            formData.append("product", product);
                            formData.append("file", file);
                            await fetch(`${API_BASE}/das_upload`, {
                                method: "POST",
                                body: formData,
                            });
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
                        // 错误提示已在 saveConfig 内部
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
