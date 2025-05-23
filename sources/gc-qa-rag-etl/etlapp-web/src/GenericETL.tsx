import React, { useState, useEffect } from 'react';
import { Upload, Button, Select, Progress, message, List, Modal, Input } from 'antd';
import { UploadOutlined, PlayCircleOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

const API_BASE = 'http://127.0.0.1:8000/generic';

// DAS 相关 API
const fetchFiles = async (product: string) => {
  const res = await fetch(`${API_BASE}/das_files?product=${product}`);
  return (await res.json()).files as string[];
};

const fetchResults = async (product: string) => {
  const res = await fetch(`${API_BASE}/das_results?product=${product}`);
  return (await res.json()).files as string[];
};

const fetchResultContent = async (product: string, filename: string) => {
  const res = await fetch(`${API_BASE}/das_result_content?product=${product}&filename=${filename}`);
  return await res.json();
};

const startDAS = async (product: string) => {
  const form = new FormData();
  form.append('product', product);
  const res = await fetch(`${API_BASE}/das_start`, { method: 'POST', body: form });
  return await res.json();
};

const fetchProgress = async (taskId: string) => {
  const res = await fetch(`${API_BASE}/das_progress/${taskId}`);
  return await res.json();
};

// ETL 相关 API

type EtlType = 'embedding' | 'qa' | 'full';

const ETL_TYPE_LABELS: Record<EtlType, string> = {
  embedding: '生成向量',
  qa: '生成QA',
  full: '生成FullAnswer',
};

const startETL = async (product: string, etlType: EtlType) => {
  const form = new FormData();
  form.append('product', product);
  form.append('etl_type', etlType);
  const res = await fetch(`${API_BASE}/etl_start`, { method: 'POST', body: form });
  return await res.json();
};

const fetchEtlProgress = async (taskId: string) => {
  const res = await fetch(`${API_BASE}/etl_progress/${taskId}`);
  return await res.json();
};

const fetchEtlResults = async (product: string, etlType: EtlType) => {
  const res = await fetch(`${API_BASE}/etl_results?product=${product}&etl_type=${etlType}`);
  return (await res.json()).files as string[];
};

const fetchEtlResultContent = async (product: string, etlType: EtlType, filename: string) => {
  const res = await fetch(`${API_BASE}/etl_result_content?product=${product}&etl_type=${etlType}&filename=${filename}`);
  return await res.json();
};

// 公共
const fetchProducts = async () => {
  const res = await fetch(`${API_BASE}/products`);
  return (await res.json()).products as string[];
};

const createProduct = async (product: string) => {
  const form = new FormData();
  form.append('product', product);
  const res = await fetch(`${API_BASE}/create_product`, { method: 'POST', body: form });
  if (!res.ok) throw new Error((await res.json()).detail || '创建失败');
  return await res.json();
};

const GenericETL: React.FC = () => {
  // DAS 相关 state
  const [product, setProduct] = useState<string>('forguncy');
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [serverFiles, setServerFiles] = useState<string[]>([]);
  const [dasRunning, setDasRunning] = useState(false);
  const [dasProgress, setDasProgress] = useState(0);
  const [dasProgressMsg, setDasProgressMsg] = useState('');
  const [dasTaskId, setDasTaskId] = useState<string | null>(null);
  const [resultFiles, setResultFiles] = useState<string[]>([]);
  const [previewModal, setPreviewModal] = useState(false);
  const [previewContent, setPreviewContent] = useState<any>(null);
  const [previewTitle, setPreviewTitle] = useState('');

  // ETL 相关 state
  const [etlType, setEtlType] = useState<EtlType>('embedding');
  const [etlRunning, setEtlRunning] = useState(false);
  const [etlProgress, setEtlProgress] = useState(0);
  const [etlProgressMsg, setEtlProgressMsg] = useState('');
  const [etlTaskId, setEtlTaskId] = useState<string | null>(null);
  const [etlResultFiles, setEtlResultFiles] = useState<string[]>([]);
  const [etlPreviewModal, setEtlPreviewModal] = useState(false);
  const [etlPreviewContent, setEtlPreviewContent] = useState<any>(null);
  const [etlPreviewTitle, setEtlPreviewTitle] = useState('');

  // 公共
  const [products, setProducts] = useState<string[]>([]);
  const [newProductModal, setNewProductModal] = useState(false);
  const [newProductName, setNewProductName] = useState('');

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
      fetchFiles(product).then(setServerFiles);
      fetchResults(product).then(setResultFiles);
    }
  }, [product]);

  useEffect(() => {
    let timer: number;
    if (dasRunning && dasTaskId) {
      timer = window.setInterval(async () => {
        const res = await fetchProgress(dasTaskId);
        if (res.status === 'done') {
          setDasProgress(100);
          setDasProgressMsg('ETL finished');
          setDasRunning(false);
          fetchResults(product).then(setResultFiles);
          clearInterval(timer);
        } else if (res.status === 'error') {
          setDasProgressMsg('Error: ' + res.msg);
          setDasRunning(false);
          clearInterval(timer);
        } else if (res.status === 'running') {
          setDasProgress(res.progress || 50);
          setDasProgressMsg(res.msg || 'Running...');
        }
      }, 1000);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [dasRunning, dasTaskId, product]);

  // ETL 相关 effect
  useEffect(() => {
    if (product && etlType) {
      fetchEtlResults(product, etlType).then(setEtlResultFiles);
    }
  }, [product, etlType]);

  useEffect(() => {
    let timer: number;
    if (etlRunning && etlTaskId) {
      timer = window.setInterval(async () => {
        const res = await fetchEtlProgress(etlTaskId);
        if (res.status === 'done') {
          setEtlProgress(100);
          setEtlProgressMsg('ETL finished');
          setEtlRunning(false);
          fetchEtlResults(product, etlType).then(setEtlResultFiles);
          clearInterval(timer);
        } else if (res.status === 'error') {
          setEtlProgressMsg('Error: ' + res.msg);
          setEtlRunning(false);
          clearInterval(timer);
        } else if (res.status === 'running') {
          setEtlProgress(res.progress || 50);
          setEtlProgressMsg(res.msg || 'Running...');
        }
      }, 1000);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [etlRunning, etlTaskId, product, etlType]);

  // DAS 操作
  const handleUpload = async (options: any) => {
    const { file } = options;
    const form = new FormData();
    form.append('product', product);
    form.append('file', file as any);
    const res = await fetch(`${API_BASE}/das_upload`, {
      method: 'POST',
      body: form,
    });
    if (res.ok) {
      message.success(`${file.name} 上传成功`);
      fetchFiles(product).then(setServerFiles);
    } else {
      message.error(`${file.name} 上传失败`);
    }
  };

  const handleStartDAS = async () => {
    setDasRunning(true);
    setDasProgress(0);
    setDasProgressMsg('ETL started');
    const res = await startDAS(product);
    setDasTaskId(res.task_id);
  };

  const handlePreview = async (filename: string) => {
    const content = await fetchResultContent(product, filename);
    setPreviewContent(content);
    setPreviewTitle(filename);
    setPreviewModal(true);
  };

  // ETL 操作
  const handleStartETL = async () => {
    setEtlRunning(true);
    setEtlProgress(0);
    setEtlProgressMsg('ETL started');
    const res = await startETL(product, etlType);
    setEtlTaskId(res.task_id);
  };

  const handleEtlPreview = async (filename: string) => {
    const content = await fetchEtlResultContent(product, etlType, filename);
    setEtlPreviewContent(content);
    setEtlPreviewTitle(filename);
    setEtlPreviewModal(true);
  };

  // 公共
  const handleCreateProduct = async () => {
    if (!newProductName) return;
    try {
      await createProduct(newProductName);
      message.success('产品创建成功');
      setNewProductModal(false);
      setNewProductName('');
      fetchProducts().then(setProducts);
    } catch (e: any) {
      message.error(e.message || '创建失败');
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', background: '#fff', padding: 24, borderRadius: 8 }}>
      <h2>Generic ETL 流程演示</h2>
      <div style={{ marginBottom: 16 }}>
        <span>选择产品：</span>
        <Select
          style={{ width: 180, marginLeft: 8 }}
          value={product}
          onChange={setProduct}
          options={products.map(p => ({ label: p, value: p }))}
        />
        <Button
          icon={<PlusOutlined />}
          style={{ marginLeft: 8 }}
          onClick={() => setNewProductModal(true)}
        >
          新建产品
        </Button>
      </div>
      {/* DAS 区域 */}
      <Upload
        customRequest={handleUpload}
        fileList={fileList}
        showUploadList={false}
        multiple
      >
        <Button icon={<UploadOutlined />}>上传文件</Button>
      </Upload>
      <div style={{ margin: '16px 0' }}>
        <b>已上传文件：</b>
        <List
          size="small"
          bordered
          dataSource={serverFiles}
          renderItem={item => <List.Item>{item}</List.Item>}
          style={{ marginTop: 8, marginBottom: 8 }}
        />
      </div>
      <Button
        type="primary"
        icon={<PlayCircleOutlined />}
        onClick={handleStartDAS}
        loading={dasRunning}
        disabled={dasRunning || serverFiles.length === 0}
      >
        启动 ETL - DAS 处理
      </Button>
      {dasRunning || dasProgress === 100 ? (
        <div style={{ margin: '16px 0' }}>
          <Progress percent={dasProgress} status={dasProgress === 100 ? 'success' : 'active'} />
          <div>{dasProgressMsg}</div>
        </div>
      ) : null}
      <div style={{ margin: '24px 0 8px 0' }}>
        <b>DAS 处理结果文件：</b>
        <List
          size="small"
          bordered
          dataSource={resultFiles}
          renderItem={item => (
            <List.Item
              actions={[
                <Button size="small" icon={<EyeOutlined />} onClick={() => handlePreview(item)}>
                  预览
                </Button>,
              ]}
            >
              {item}
            </List.Item>
          )}
        />
      </div>
      <Modal
        open={previewModal}
        title={previewTitle}
        onCancel={() => setPreviewModal(false)}
        footer={null}
        width={800}
      >
        <pre style={{ maxHeight: 500, overflow: 'auto', background: '#f6f6f6', padding: 12 }}>
          {JSON.stringify(previewContent, null, 2)}
        </pre>
      </Modal>
      {/* ETL 区域 */}
      <div style={{ margin: '32px 0 0 0', padding: '24px 0 0 0', borderTop: '1px solid #eee' }}>
        <h3>ETL 处理</h3>
        <div style={{ marginBottom: 16 }}>
          <span>选择 ETL 类型：</span>
          <Select
            style={{ width: 180, marginLeft: 8 }}
            value={etlType}
            onChange={setEtlType}
            options={Object.entries(ETL_TYPE_LABELS).map(([k, v]) => ({ label: v, value: k }))}
          />
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleStartETL}
            loading={etlRunning}
            disabled={etlRunning}
            style={{ marginLeft: 16 }}
          >
            启动 ETL
          </Button>
        </div>
        {etlRunning || etlProgress === 100 ? (
          <div style={{ margin: '16px 0' }}>
            <Progress percent={etlProgress} status={etlProgress === 100 ? 'success' : 'active'} />
            <div>{etlProgressMsg}</div>
          </div>
        ) : null}
        <div style={{ margin: '24px 0 8px 0' }}>
          <b>ETL 结果文件：</b>
          <List
            size="small"
            bordered
            dataSource={etlResultFiles}
            renderItem={item => (
              <List.Item
                actions={[
                  <Button size="small" icon={<EyeOutlined />} onClick={() => handleEtlPreview(item)}>
                    预览
                  </Button>,
                ]}
              >
                {item}
              </List.Item>
            )}
          />
        </div>
        <Modal
          open={etlPreviewModal}
          title={etlPreviewTitle}
          onCancel={() => setEtlPreviewModal(false)}
          footer={null}
          width={800}
        >
          <pre style={{ maxHeight: 500, overflow: 'auto', background: '#f6f6f6', padding: 12 }}>
            {JSON.stringify(etlPreviewContent, null, 2)}
          </pre>
        </Modal>
      </div>
      <Modal
        open={newProductModal}
        title="新建产品"
        onCancel={() => setNewProductModal(false)}
        onOk={handleCreateProduct}
      >
        <Input
          placeholder="输入新产品名称"
          value={newProductName}
          onChange={e => setNewProductName(e.target.value)}
        />
      </Modal>
    </div>
  );
};

export default GenericETL; 