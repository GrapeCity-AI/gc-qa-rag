import React, { useState } from 'react';
import { Flex, Segmented, Button, Input } from 'antd';
import { EditOutlined, CloseOutlined } from '@ant-design/icons';
import { AnswerOptions as AnswerOptionsType, AnswerStyle, AnswerComplexity, AnswerStyleNameKey, AnswerComplexityNameKey } from '../types/Base';
import { useTranslation } from 'react-i18next';

interface AnswerOptionsProps {
    options: AnswerOptionsType;
    onStyleChange: (style: AnswerStyle) => void;
    onComplexityChange: (complexity: AnswerComplexity) => void;
    onCustomInstructionChange: (instruction: string) => void;
}

const AnswerOptions: React.FC<AnswerOptionsProps> = ({
    options,
    onStyleChange,
    onComplexityChange,
    onCustomInstructionChange,
}) => {
    const { t } = useTranslation();
    const [showCustomInput, setShowCustomInput] = useState(!!options.customInstruction);

    const styleOptions = [
        { label: t(AnswerStyleNameKey[AnswerStyle.Beginner]), value: AnswerStyle.Beginner },
        { label: t(AnswerStyleNameKey[AnswerStyle.Professional]), value: AnswerStyle.Professional },
    ];

    const complexityOptions = [
        { label: t(AnswerComplexityNameKey[AnswerComplexity.Concise]), value: AnswerComplexity.Concise },
        { label: t(AnswerComplexityNameKey[AnswerComplexity.Verbose]), value: AnswerComplexity.Verbose },
    ];

    const handleCustomButtonClick = () => {
        if (showCustomInput) {
            setShowCustomInput(false);
            onCustomInstructionChange('');
        } else {
            setShowCustomInput(true);
        }
    };

    const handleCustomCancel = () => {
        setShowCustomInput(false);
        onCustomInstructionChange('');
    };

    return (
        <Flex vertical gap={8} style={{ padding: '8px 0' }}>
            <Flex align="center" gap={8} wrap="wrap">
                <Segmented
                    value={options.style}
                    options={styleOptions}
                    onChange={(value) => onStyleChange(value as AnswerStyle)}
                />

                <Segmented
                    value={options.complexity}
                    options={complexityOptions}
                    onChange={(value) => onComplexityChange(value as AnswerComplexity)}
                />

                <Button
                    type="text"
                    icon={<EditOutlined />}
                    onClick={handleCustomButtonClick}
                >
                    {t('AnswerOptions.Custom')}
                </Button>
            </Flex>

            {showCustomInput && (
                <Flex gap={8}>
                    <Input
                        placeholder={t('AnswerOptions.CustomPlaceholder')}
                        value={options.customInstruction}
                        onChange={(e) => onCustomInstructionChange(e.target.value)}
                        style={{ flex: 1 }}
                    />
                    <Button
                        icon={<CloseOutlined />}
                        onClick={handleCustomCancel}
                    />
                </Flex>
            )}
        </Flex>
    );
};

export default AnswerOptions;
