import React from "react";
import { Modal, Spin, Typography, Input, Alert } from "antd";

const { Text } = Typography;

interface ConfigModalProps {
    open: boolean;
    config: any;
    configLoading: boolean;
    configSaving: boolean;
    setConfig: (cfg: any) => void;
    onCancel: () => void;
    onOk: () => void;
}

const ConfigModal: React.FC<ConfigModalProps> = ({
    open,
    config,
    configLoading,
    configSaving,
    setConfig,
    onCancel,
    onOk,
}) => (
    <Modal
        open={open}
        title="系统配置"
        onCancel={onCancel}
        onOk={onOk}
        confirmLoading={configSaving}
        width={600}
    >
        {configLoading ? (
            <Spin />
        ) : config ? (
            <div>
                <Alert
                    message="配置更改后需要重启服务端才能生效"
                    type="warning"
                    showIcon
                    style={{ marginBottom: "16px" }}
                />
                
                <Text strong>LLM 配置</Text>
                <Input
                    style={{ margin: "8px 0" }}
                    addonBefore="API Key"
                    value={config.llm.api_key}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            llm: {
                                ...config.llm,
                                api_key: e.target.value,
                            },
                        })
                    }
                />
                <Input
                    style={{ margin: "8px 0" }}
                    addonBefore="API Base"
                    value={config.llm.api_base}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            llm: {
                                ...config.llm,
                                api_base: e.target.value,
                            },
                        })
                    }
                />
                <Input
                    style={{ margin: "8px 0" }}
                    addonBefore="模型名"
                    value={config.llm.model_name}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            llm: {
                                ...config.llm,
                                model_name: e.target.value,
                            },
                        })
                    }
                />
                <Text strong>Embedding 配置</Text>
                <Input
                    style={{ margin: "8px 0" }}
                    addonBefore="API Key"
                    value={config.embedding.api_key}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            embedding: {
                                ...config.embedding,
                                api_key: e.target.value,
                            },
                        })
                    }
                />
                <Text strong>Vector DB 配置</Text>
                <Input
                    style={{ margin: "8px 0" }}
                    addonBefore="Host"
                    value={config.vector_db.host}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            vector_db: {
                                ...config.vector_db,
                                host: e.target.value,
                            },
                        })
                    }
                />
                <Text strong>Root Path</Text>
                <Input
                    style={{ margin: "8px 0" }}
                    value={config.root_path}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            root_path: e.target.value,
                        })
                    }
                />
                <Text strong>Log Path</Text>
                <Input
                    style={{ margin: "8px 0" }}
                    value={config.log_path}
                    onChange={(e) =>
                        setConfig({
                            ...config,
                            log_path: e.target.value,
                        })
                    }
                />
            </div>
        ) : null}
    </Modal>
);

export default ConfigModal;
