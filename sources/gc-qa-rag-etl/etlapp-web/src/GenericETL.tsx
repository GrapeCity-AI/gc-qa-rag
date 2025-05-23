import React, { useState, useEffect } from 'react';
import { Upload, Button, Select, Table, Progress, message, List, Modal } from 'antd';
import { UploadOutlined, PlayCircleOutlined, EyeOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import type { RcFile } from 'rc-upload/lib/interface';

const PRODUCT_OPTIONS = [
  { label: 'forguncy', value: 'forguncy' },
  { label: 'wyn', value: 'wyn' },
  { label: 'spreadjs', value: 'spreadjs' },
  { label: 'gcexcel', value: 'gcexcel' },
];

const API_BASE = '/generic';

const fetchFiles = async (product: string) => {
  const res = await fetch(`${API_BASE}/files?product=${product}`);
  return (await res.json()).files as string[];
};

const fetchResults = async (product: string) => {
  const res = await fetch(`${API_BASE}/results?product=${product}`);
  return (await res.json()).files as string[];
};

const fetchResultContent = async (product: string, filename: string) => {
  const res = await fetch(`${API_BASE}/result_content?product=${product}&filename=${filename}`);
  return await res.json();
};

const startETL = async (product: string) => {
  const form = new FormData();
  form.append('product', product);
  const res = await fetch(`${API_BASE}/start_etl`, { method: 'POST', body: form });
  return await res.json();
};

const fetchProgress = async (taskId: string) => {
  const res = await fetch(`${API_BASE}/progress/${taskId}`);
  return await res.json();
};

const GenericETL: React.FC = () => {
  const [product, setProduct] = useState<string>('forguncy');
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [serverFiles, setServerFiles] = useState<string[]>([]);
  const [etlRunning, setEtlRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [resultFiles, setResultFiles] = useState<string[]>([]);
  const [previewModal, setPreviewModal] = useState(false);
  const [previewContent, setPreviewContent] = useState<any>(null);
  const [previewTitle, setPreviewTitle] = useState('');

  useEffect(() => {
    if (product) {
      fetchFiles(product).then(setServerFiles);
      fetchResults(product).then(setResultFiles);
    }
  }, [product]);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (etlRunning && taskId) {
      timer = setInterval(async () => {
        const res = await fetchProgress(taskId);
        if (res.status === 'done') {
          setProgress(100);
          setProgressMsg('ETL finished');
          setEtlRunning(false);
          fetchResults(product).then(setResultFiles);
          clearInterval(timer);
        } else if (res.status === 'error') {
          setProgressMsg('Error: ' + res.msg);
          setEtlRunning(false);
          clearInterval(timer);
        } else if (res.status === 'running') {
          setProgress(res.progress || 50);
          setProgressMsg(res.msg || 'Running...');
        }
      }, 1000);
    }
    return () => timer && clearInterval(timer);
  }, [etlRunning, taskId, product]);

  const handleUpload = async (options: any) => {
    const { file } = options;
    const form = new FormData();
    form.append('product', product);
    form.append('file', file as RcFile);
    const res = await fetch(`${API_BASE}/upload`, {
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

  const handleStartETL = async () => {
    setEtlRunning(true);
    setProgress(0);
    setProgressMsg('ETL started');
    const res = await startETL(product);
    setTaskId(res.task_id);
  };

  const handlePreview = async (filename: string) => {
    const content = await fetchResultContent(product, filename);
    setPreviewContent(content);
    setPreviewTitle(filename);
    setPreviewModal(true);
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
          options={PRODUCT_OPTIONS}
        />
      </div>
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
        onClick={handleStartETL}
        loading={etlRunning}
        disabled={etlRunning || serverFiles.length === 0}
      >
        启动 ETL 处理
      </Button>
      {etlRunning || progress === 100 ? (
        <div style={{ margin: '16px 0' }}>
          <Progress percent={progress} status={progress === 100 ? 'success' : 'active'} />
          <div>{progressMsg}</div>
        </div>
      ) : null}
      <div style={{ margin: '24px 0 8px 0' }}>
        <b>处理结果文件：</b>
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
    </div>
  );
};

export default GenericETL; 