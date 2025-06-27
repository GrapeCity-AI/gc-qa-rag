import React, { useState, useEffect } from "react";
import { Modal, Space, Typography, Input, Button, Divider, Alert, Steps } from "antd";
import { CheckCircleOutlined, LoadingOutlined } from "@ant-design/icons";
import { fetchConfig } from "../api/ApiService";

const { Text } = Typography;
const { Step } = Steps;

interface PublishModalProps {
    open: boolean;
    product: string;
    publishTag: string;
    setPublishTag: (v: string) => void;
    onCancel: () => void;
    onOk: () => void;
    onUpdateAliases: () => void;
    confirmLoading: boolean;
    updateAliasesLoading: boolean;
}

const PublishModal: React.FC<PublishModalProps> = ({
    open,
    product,
    publishTag,
    setPublishTag,
    onCancel,
    onOk,
    onUpdateAliases,
    confirmLoading,
    updateAliasesLoading,
}) => {
    const [vectorDbHost, setVectorDbHost] = useState<string>("");
    const [configLoading, setConfigLoading] = useState<boolean>(false);
    const [publishCompleted, setPublishCompleted] = useState<boolean>(false);
    const [currentStep, setCurrentStep] = useState<number>(0);

    useEffect(() => {
        if (open) {
            loadConfig();
            // 重置状态
            setPublishCompleted(false);
            setCurrentStep(0);
        }
    }, [open]);

    // 监听发布状态变化
    useEffect(() => {
        if (!confirmLoading && publishCompleted && currentStep === 0) {
            setCurrentStep(1);
        }
    }, [confirmLoading, publishCompleted, currentStep]);

    const loadConfig = async () => {
        setConfigLoading(true);
        try {
            const config = await fetchConfig();
            setVectorDbHost(config.vector_db?.host || "");
        } catch (error) {
            console.error("获取配置失败:", error);
        } finally {
            setConfigLoading(false);
        }
    };

    const handlePublishClick = async () => {
        await onOk();
        setPublishCompleted(true);
    };

    const handleSkipAliasUpdate = () => {
        onCancel();
        setPublishCompleted(false);
        setCurrentStep(0);
    };

    const handleUpdateAliasesClick = async () => {
        await onUpdateAliases();
        onCancel();
        setPublishCompleted(false);
        setCurrentStep(0);
    };

    const getSteps = () => [
        {
            title: "发布到向量库",
            description: "将数据推送到向量数据库",
            status: (confirmLoading ? "process" : (publishCompleted ? "finish" : "wait")) as "wait" | "process" | "finish" | "error",
            icon: confirmLoading ? <LoadingOutlined /> : (publishCompleted ? <CheckCircleOutlined /> : undefined),
        },
        {
            title: "更新生产别名",
            description: "切换生产环境版本",
            status: (currentStep === 1 ? (updateAliasesLoading ? "process" : "wait") : "wait") as "wait" | "process" | "finish" | "error",
            icon: updateAliasesLoading ? <LoadingOutlined /> : undefined,
        },
    ];

    return (
        <Modal
            open={open}
            title="发布到向量数据库"
            onCancel={onCancel}
            width={600}
            footer={
                currentStep === 0 ? [
                    <Button key="cancel" onClick={onCancel}>
                        取消
                    </Button>,
                    <Button
                        key="publish"
                        type="primary"
                        loading={confirmLoading}
                        disabled={!publishTag}
                        onClick={handlePublishClick}
                    >
                        {confirmLoading ? "发布中..." : "开始发布"}
                    </Button>,
                ] : [
                    <Button key="skip" onClick={handleSkipAliasUpdate}>
                        跳过更新别名
                    </Button>,
                    <Button
                        key="updateAliases"
                        type="primary"
                        loading={updateAliasesLoading}
                        onClick={handleUpdateAliasesClick}
                    >
                        {updateAliasesLoading ? "更新中..." : "更新生产别名"}
                    </Button>,
                ]
            }
        >
            <Space direction="vertical" style={{ width: "100%" }}>
                <Text>当前产品: <strong>{product}</strong></Text>
                <Text>
                    发布目标:{" "}
                    <strong>
                        {configLoading ? "加载中..." : vectorDbHost || "未配置"}
                    </strong>
                </Text>
                
                <Divider />
                
                <Steps current={currentStep} direction="vertical" size="small">
                    {getSteps().map((step, index) => (
                        <Step
                            key={index}
                            title={step.title}
                            description={step.description}
                            status={step.status}
                            icon={step.icon}
                        />
                    ))}
                </Steps>

                <Divider />

                {currentStep === 0 && (
                    <>
                        <Text type="secondary">请输入发布标签(tag)，用于版本管理</Text>
                        <Input
                            placeholder="输入标签，如: 230501"
                            value={publishTag}
                            onChange={(e) => setPublishTag(e.target.value)}
                            disabled={confirmLoading}
                        />
                    </>
                )}

                {currentStep === 1 && (
                    <Alert
                        message="发布完成！"
                        description={
                            <div>
                                <p>数据已成功发布到向量数据库 (标签: <strong>{publishTag}</strong>)</p>
                                <p>您现在可以选择是否将此版本设置为生产环境：</p>
                                <ul>
                                    <li><strong>更新生产别名</strong>：将刚发布的版本设置为生产环境</li>
                                    <li><strong>跳过更新别名</strong>：保持当前生产环境不变</li>
                                </ul>
                            </div>
                        }
                        type="success"
                        showIcon
                    />
                )}
            </Space>
        </Modal>
    );
};

export default PublishModal;
