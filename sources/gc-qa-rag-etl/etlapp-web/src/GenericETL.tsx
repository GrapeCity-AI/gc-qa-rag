import React, { useState, useEffect } from 'react';
import { Upload, Button, Select, Progress, message, List, Modal, Input } from 'antd';
import { UploadOutlined, PlayCircleOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

const API_BASE = 'http://127.0.0.1:8000/generic';

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
  form.append('product', product);
  const res = await fetch(`${API_BASE}/create_product`, { method: 'POST', body: form });
  if (!res.ok) throw new Error((await res.json()).detail || '创建失败');
  return await res.json();
};

const GenericETL: React.FC = () => {
  // DAS 相关 state
  const [product, setProduct] = useState<string>('forguncy');
  const [previewModal, setPreviewModal] = useState(false);
  const [previewContent, setPreviewContent] = useState<any>(null);
  const [previewTitle, setPreviewTitle] = useState('');

  // 公共
  const [products, setProducts] = useState<string[]>([]);
  const [newProductModal, setNewProductModal] = useState(false);
  const [newProductName, setNewProductName] = useState('');

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
      message.success('产品创建成功');
      setNewProductModal(false);
      setNewProductName('');
      fetchProducts().then(setProducts);
    } catch (e: any) {
      message.error(e.message || '创建失败');
    }
  };

  // 单文件 DAS 处理
  const handleDasProcess = async (row: any) => {
    setProcessing(p => ({ ...p, [row.filename + ':das']: true }));
    const form = new FormData();
    form.append('product', product);
    const res = await fetch(`${API_BASE}/das_start`, { method: 'POST', body: form });
    setProcessing(p => ({ ...p, [row.filename + ':das']: false }));
    // 简单延迟后刷新
    setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
  };

  // 单文件 ETL 处理
  const handleEtlProcess = async (row: any, etlType: 'embedding' | 'qa' | 'full') => {
    setProcessing(p => ({ ...p, [row.filename + ':' + etlType]: true }));
    const form = new FormData();
    form.append('product', product);
    form.append('etl_type', etlType);
    const res = await fetch(`${API_BASE}/etl_start`, { method: 'POST', body: form });
    setProcessing(p => ({ ...p, [row.filename + ':' + etlType]: false }));
    setTimeout(() => fetchFilesStatus(product).then(setEtlFileRows), 1000);
  };

  // 批量处理
  const handleBatchProcess = async (stage: 'das' | 'embedding' | 'qa' | 'full') => {
    for (const row of etlFileRows.filter(r => selectedRowKeys.includes(r.filename))) {
      if (stage === 'das' && row.das.status === 'not_started') {
        await handleDasProcess(row);
      } else if (['embedding', 'qa', 'full'].includes(stage) && row[stage].status === 'not_started') {
        await handleEtlProcess(row, stage as any);
      }
    }
    fetchFilesStatus(product).then(setEtlFileRows);
  };

  // 单文件内容预览
  const handlePreview = async (row: any, stage: 'das' | 'embedding' | 'qa' | 'full') => {
    let content = null;
    let title = '';
    if (stage === 'das' && row.das.resultFile) {
      const res = await fetch(`${API_BASE}/das_result_content?product=${product}&filename=${row.das.resultFile}`);
      content = await res.json();
      title = `${row.filename} - DAS`;
    } else if ((stage === 'embedding' || stage === 'qa' || stage === 'full') && row[stage].resultFile) {
      const etlType = stage;
      const res = await fetch(`${API_BASE}/etl_result_content?product=${product}&etl_type=${etlType}&filename=${row[stage].resultFile}`);
      content = await res.json();
      title = `${row.filename} - ${stage}`;
    }
    setPreviewContent(content);
    setPreviewTitle(title);
    setPreviewModal(true);
  };

  // 表格列定义
  const columns = [
    { title: '文件名', dataIndex: 'filename', key: 'filename' },
    { title: '上传时间', dataIndex: 'uploadTime', key: 'uploadTime' },
    {
      title: 'DAS处理', key: 'das',
      render: (_: any, row: any) => {
        if (row.das.status === 'done') return <Button size="small" onClick={() => handlePreview(row, 'das')}>预览</Button>;
        if (processing[row.filename + ':das']) return <span>处理中...</span>;
        return <Button size="small" color='primary' onClick={() => handleDasProcess(row)}>处理</Button>;
      }
    },
    {
      title: 'Embedding', key: 'embedding',
      render: (_: any, row: any) => {
        if (row.embedding.status === 'done') return <Button size="small" onClick={() => handlePreview(row, 'embedding')}>预览</Button>;
        if (processing[row.filename + ':embedding']) return <span>处理中...</span>;
        return <Button size="small" color='primary' onClick={() => handleEtlProcess(row, 'embedding')}>处理</Button>;
      }
    },
    {
      title: 'QA', key: 'qa',
      render: (_: any, row: any) => {
        if (row.qa.status === 'done') return <Button size="small" onClick={() => handlePreview(row, 'qa')}>预览</Button>;
        if (processing[row.filename + ':qa']) return <span>处理中...</span>;
        return <Button color='primary' size="small" onClick={() => handleEtlProcess(row, 'qa')}>处理</Button>;
      }
    },
    {
      title: 'FullAnswer', key: 'full',
      render: (_: any, row: any) => {
        if (row.full.status === 'done') return <Button size="small" onClick={() => handlePreview(row, 'full')}>预览</Button>;
        if (processing[row.filename + ':full']) return <span>处理中...</span>;
        return <Button color='primary' size="small" onClick={() => handleEtlProcess(row, 'full')}>处理</Button>;
      }
    },
  ];

  // 表格多选
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => setSelectedRowKeys(newSelectedRowKeys),
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
      <div style={{ margin: '24px 0' }}>
        <b>文件全流程状态：</b>
        <div style={{ margin: '8px 0' }}>
          <Button disabled={selectedRowKeys.length === 0} onClick={() => handleBatchProcess('das')}>批量DAS处理</Button>
          <Button disabled={selectedRowKeys.length === 0} style={{ marginLeft: 8 }} onClick={() => handleBatchProcess('embedding')}>批量Embedding</Button>
          <Button disabled={selectedRowKeys.length === 0} style={{ marginLeft: 8 }} onClick={() => handleBatchProcess('qa')}>批量QA</Button>
          <Button disabled={selectedRowKeys.length === 0} style={{ marginLeft: 8 }} onClick={() => handleBatchProcess('full')}>批量Full</Button>
        </div>
        <div>
          <table className="ant-table">
            <thead>
              <tr>
                <th>选择</th>
                {columns.map(col => <th key={col.key}>{col.title}</th>)}
              </tr>
            </thead>
            <tbody>
              {etlFileRows.map((row, idx) => (
                <tr key={row.filename}>
                  <td>
                    <input type="checkbox" checked={selectedRowKeys.includes(row.filename)} onChange={e => {
                      if (e.target.checked) setSelectedRowKeys([...selectedRowKeys, row.filename]);
                      else setSelectedRowKeys(selectedRowKeys.filter(k => k !== row.filename));
                    }} />
                  </td>
                  {columns.map(col => <td key={col.key}>{col.render ? col.render(null, row) : row[col.dataIndex]}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GenericETL; 