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
    fetchDasProgress,
    etlStart,
    fetchEtlProgress,
    fetchDasResultContent,
    fetchEtlResultContent,
    publish,
    fetchServerLog,
    updateAliases,
    fetchPublishProgress,
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
    const [updatingAliases, setUpdatingAliases] = useState(false);

    // New table data
    const [etlFileRows, setEtlFileRows] = useState<any[]>([]);
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

    // Handle loading
    const [processing, setProcessing] = useState<{ [k: string]: boolean }>({});

    // 添加进度状态管理
    const [progressInfo, setProgressInfo] = useState<{ [k: string]: { progress: number; msg: string } }>({});

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
        try {
            const response = await dasStart(product, row.filename);
            const taskId = response.task_id;
            
            // 轮询查询进度
            const pollProgress = async () => {
                try {
                    const progress = await fetchDasProgress(taskId);
                    console.log(`DAS进度 - ${row.filename}: ${progress.status} (${progress.progress}%) - ${progress.msg}`);
                    
                    // 更新进度信息
                    setProgressInfo((prev) => ({
                        ...prev,
                        [row.filename + ":das"]: {
                            progress: progress.progress || 0,
                            msg: progress.msg || ""
                        }
                    }));
                    
                    if (progress.status === "done" || progress.status === "error") {
                        setProcessing((p) => ({ ...p, [row.filename + ":das"]: false }));
                        // 清除进度信息
                        setProgressInfo((prev) => {
                            const newInfo = { ...prev };
                            delete newInfo[row.filename + ":das"];
                            return newInfo;
                        });
                        if (progress.status === "error") {
                            message.error(`DAS处理失败: ${progress.msg}`);
                        } else {
                            message.success(`DAS处理完成: ${row.filename}`);
                        }
                        // 刷新文件状态
                        fetchFilesStatus(product).then(setEtlFileRows);
                        return;
                    }
                    
                    // 继续轮询
                    setTimeout(pollProgress, 2000);
                } catch (error) {
                    console.error("获取进度失败:", error);
                    setProcessing((p) => ({ ...p, [row.filename + ":das"]: false }));
                    // 清除进度信息
                    setProgressInfo((prev) => {
                        const newInfo = { ...prev };
                        delete newInfo[row.filename + ":das"];
                        return newInfo;
                    });
                    message.error("获取进度失败");
                }
            };
            
            // 开始轮询
            setTimeout(pollProgress, 1000);
            
        } catch (error: any) {
            setProcessing((p) => ({ ...p, [row.filename + ":das"]: false }));
            message.error(error.message || "DAS处理启动失败");
        }
    };

    // Single file ETL processing
    const handleEtlProcess = async (
        row: any,
        etlType: "embedding" | "qa" | "full"
    ) => {
        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: true }));
        try {
            const response = await etlStart(product, etlType, row.das.resultFile);
            const taskId = response.task_id;
            
            // 轮询查询进度
            const pollProgress = async () => {
                try {
                    const progress = await fetchEtlProgress(taskId);
                    console.log(`ETL-${etlType}进度 - ${row.filename}: ${progress.status} (${progress.progress}%) - ${progress.msg}`);
                    
                    // 更新进度信息
                    setProgressInfo((prev) => ({
                        ...prev,
                        [row.filename + ":" + etlType]: {
                            progress: progress.progress || 0,
                            msg: progress.msg || ""
                        }
                    }));
                    
                    if (progress.status === "done" || progress.status === "error") {
                        setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: false }));
                        // 清除进度信息
                        setProgressInfo((prev) => {
                            const newInfo = { ...prev };
                            delete newInfo[row.filename + ":" + etlType];
                            return newInfo;
                        });
                        if (progress.status === "error") {
                            message.error(`ETL-${etlType}处理失败: ${progress.msg}`);
                        } else {
                            message.success(`ETL-${etlType}处理完成: ${row.filename}`);
                        }
                        // 刷新文件状态
                        fetchFilesStatus(product).then(setEtlFileRows);
                        return;
                    }
                    
                    // 继续轮询
                    setTimeout(pollProgress, 2000);
                } catch (error) {
                    console.error("获取ETL进度失败:", error);
                    setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: false }));
                    // 清除进度信息
                    setProgressInfo((prev) => {
                        const newInfo = { ...prev };
                        delete newInfo[row.filename + ":" + etlType];
                        return newInfo;
                    });
                    message.error("获取ETL进度失败");
                }
            };
            
            // 开始轮询
            setTimeout(pollProgress, 1000);
            
        } catch (error: any) {
            setProcessing((p) => ({ ...p, [row.filename + ":" + etlType]: false }));
            message.error(error.message || `ETL-${etlType}处理启动失败`);
        }
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
            const response = await publish(product, publishTag);
            const taskId = response.task_id;
            message.success("发布任务已启动");
            
            // 轮询查询进度
            const pollProgress = async () => {
                try {
                    const progress = await fetchPublishProgress(taskId);
                    console.log(`发布进度: ${progress.status} (${progress.progress}%) - ${progress.msg}`);
                    
                    if (progress.status === "done" || progress.status === "error") {
                        setPublishing(false);
                        if (progress.status === "error") {
                            message.error(`发布失败: ${progress.msg}`);
                            setPublishModal(false);
                            setPublishTag("");
                        } else {
                            message.success("发布完成！现在可以选择是否更新生产别名");
                            // 不关闭 modal，让用户选择下一步操作
                        }
                        return;
                    }
                    
                    // 继续轮询
                    setTimeout(pollProgress, 2000);
                } catch (error) {
                    console.error("获取发布进度失败:", error);
                    setPublishing(false);
                    message.error("获取发布进度失败");
                }
            };
            
            // 开始轮询
            setTimeout(pollProgress, 1000);
            
        } catch (e: any) {
            message.error(e.message || "发布失败");
            setPublishing(false);
        }
    };

    // Update aliases
    const handleUpdateAliases = async () => {
        if (!publishTag) {
            message.error("请输入发布标签");
            return;
        }
        setUpdatingAliases(true);
        try {
            const response = await updateAliases(product, publishTag);
            const taskId = response.task_id;
            message.success("更新别名任务已启动");
            
            // 轮询查询进度
            const pollProgress = async () => {
                try {
                    const progress = await fetchPublishProgress(taskId);
                    console.log(`更新别名进度: ${progress.status} (${progress.progress}%) - ${progress.msg}`);
                    
                    if (progress.status === "done" || progress.status === "error") {
                        setUpdatingAliases(false);
                        if (progress.status === "error") {
                            message.error(`更新别名失败: ${progress.msg}`);
                        } else {
                            message.success("生产别名更新完成！新版本已上线");
                        }
                        // 完成后关闭 modal 并重置状态
                        setPublishModal(false);
                        setPublishTag("");
                        return;
                    }
                    
                    // 继续轮询
                    setTimeout(pollProgress, 2000);
                } catch (error) {
                    console.error("获取更新别名进度失败:", error);
                    setUpdatingAliases(false);
                    message.error("获取更新别名进度失败");
                }
            };
            
            // 开始轮询
            setTimeout(pollProgress, 1000);
            
        } catch (e: any) {
            message.error(e.message || "更新别名失败");
            setUpdatingAliases(false);
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
                onCancel={() => {
                    setPublishModal(false);
                    setPublishTag("");
                }}
                onOk={handlePublish}
                onUpdateAliases={handleUpdateAliases}
                confirmLoading={publishing}
                updateAliasesLoading={updatingAliases}
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
                    progressInfo={progressInfo}
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
