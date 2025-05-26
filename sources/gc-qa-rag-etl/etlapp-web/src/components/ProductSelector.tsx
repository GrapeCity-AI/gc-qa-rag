import React from "react";
import { Select, Button, Upload, message } from "antd";
import { PlusOutlined, UploadOutlined } from "@ant-design/icons";

interface ProductSelectorProps {
    products: string[];
    product: string;
    setProduct: (p: string) => void;
    onNewProduct: () => void;
    onUpload: (file: File) => Promise<void>;
}

const ProductSelector: React.FC<ProductSelectorProps> = ({
    products,
    product,
    setProduct,
    onNewProduct,
    onUpload,
}) => (
    <span>
        <span style={{ marginRight: 8, fontWeight: 500 }}>选择产品：</span>
        <Select
            style={{ width: 180 }}
            value={product}
            onChange={setProduct}
            options={products.map((p) => ({ label: p, value: p }))}
        />
        <Button
            icon={<PlusOutlined />}
            type="primary"
            onClick={onNewProduct}
            style={{ marginLeft: 8 }}
        >
            新建产品
        </Button>
        <Upload
            multiple
            showUploadList={false}
            customRequest={async ({ file, onSuccess, onError }) => {
                try {
                    await onUpload(file as File);
                    if (onSuccess) onSuccess({}, file);
                } catch (e) {
                    message.error("上传失败");
                    if (onError) onError(e as any);
                }
            }}
        >
            <Button icon={<UploadOutlined />} style={{ marginLeft: 8 }}>
                上传文件
            </Button>
        </Upload>
    </span>
);

export default ProductSelector; 