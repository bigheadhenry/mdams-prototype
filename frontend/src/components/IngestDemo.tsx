import React, { useState, useRef, useEffect } from 'react';
import { Card, Upload, Button, Steps, Descriptions, Alert, Spin, Tag, Typography, Divider, Collapse, message } from 'antd';
import { UploadOutlined, FileTextOutlined, SafetyCertificateOutlined, CloudUploadOutlined, ExperimentOutlined } from '@ant-design/icons';
// @ts-ignore
import HashWorker from '../workers/hashWorker.ts?worker';
import axios from 'axios';

const { Step } = Steps;
const { Paragraph, Text } = Typography;
const { Panel } = Collapse;

const IngestDemo: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState<{ step: string; message: string }>({ step: '', message: '' });
  const [result, setResult] = useState<any>(null);
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    // Initialize worker
    try {
        workerRef.current = new HashWorker();
        if (workerRef.current) {
            workerRef.current.onmessage = (e) => {
            const { type, step, message, result, error } = e.data;
            
            if (type === 'progress') {
                setProgress({ step, message });
            } else if (type === 'complete') {
                // Client-side processing done, now upload SIP
                uploadSIP(result, file);
            } else if (type === 'error') {
                setStatus('error');
                setProgress({ step: 'error', message: error });
            }
            };
        }
    } catch (e) {
        console.error("Worker init failed", e);
    }

    return () => {
      workerRef.current?.terminate();
    };
  }, []);

  const uploadSIP = async (manifestData: any, fileData: File) => {
    setStatus('uploading');
    setProgress({ step: 'uploading', message: '正在上传 SIP 包并进行服务端校验...' });
    
    const formData = new FormData();
    formData.append('file', fileData);
    formData.append('manifest', JSON.stringify(manifestData));

    try {
      const response = await axios.post('/api/ingest/sip', formData);
      
      setResult({
        ...manifestData,
        serverVerification: response.data
      });
      setStatus('success');
      setProgress({ step: 'done', message: '入库成功！服务端 Fixity 校验通过。' });
      message.success('SIP 入库成功！');
      
    } catch (err: any) {
      console.error(err);
      setStatus('error');
      // Fix: Handle Axios error response structure correctly
      let errorMsg = '上传失败';
      if (err.response) {
          // Server responded with a status code outside of 2xx
          errorMsg = err.response.data?.detail || err.response.statusText;
      } else if (err.request) {
          // The request was made but no response was received
          errorMsg = '无法连接到服务器';
      } else {
          // Something happened in setting up the request
          errorMsg = err.message;
      }
      
      setProgress({ step: 'error', message: `服务端校验失败: ${errorMsg}` });
      message.error(`入库失败: ${errorMsg}`);
    }
  };

  const handleFileSelect = (info: any) => {
    // We only take the last selected file
    const selectedFile = info.file.originFileObj || info.file;
    // Basic validation
    if (selectedFile) {
        setFile(selectedFile);
        setStatus('idle');
        setResult(null);
        setProgress({ step: '', message: '' });
    }
    return false; // Prevent auto upload
  };

  const startProcessing = () => {
    if (!file || !workerRef.current) return;
    
    setStatus('processing');
    setResult(null);
    
    // Send file to worker
    workerRef.current.postMessage({ file });
  };

  const getCurrentStep = () => {
    if (status === 'idle') return -1;
    if (status === 'error') return 1; 
    if (status === 'success') return 3;
    
    switch (progress.step) {
      case 'starting': return 0;
      case 'metadata': return 1;
      case 'hashing': return 2;
      default: return 0;
    }
  };

  return (
    <Card 
      title={<><ExperimentOutlined /> 客户端入库处理 (PoC)</>} 
      style={{ marginTop: 24, marginBottom: 24 }}
      extra={<Tag color="purple">Web Worker</Tag>}
    >
      <Alert 
        message="架构说明" 
        description="本演示将 CPU 密集型任务（SHA256 哈希计算、元数据提取）从服务器转移到客户端浏览器，使用 Web Workers 技术实现。这确保了源头数据的完整性（Fixity Check），并降低了服务器负载。"
        type="info" 
        showIcon 
        style={{ marginBottom: 24 }}
      />

      <div style={{ marginBottom: 24 }}>
        <Upload 
          beforeUpload={() => false} // Manual processing
          onChange={handleFileSelect}
          showUploadList={false}
          maxCount={1}
        >
          <Button icon={<UploadOutlined />}>选择大图文件</Button>
        </Upload>
        {file && (
          <span style={{ marginLeft: 12 }}>
            <FileTextOutlined /> {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </span>
        )}
      </div>

      {file && status === 'idle' && (
        <Button type="primary" onClick={startProcessing} icon={<SafetyCertificateOutlined />}>
          开始处理 (哈希计算 & 提取)
        </Button>
      )}

      {(status === 'processing' || status === 'success' || status === 'error') && (
        <div style={{ marginTop: 24 }}>
          <Steps current={getCurrentStep()} status={status === 'error' ? 'error' : 'process'}>
            <Step title="读取文件" description="加载到内存" />
            <Step title="提取元数据" description="Exif/XMP/IPTC" />
            <Step title="计算完整性" description="SHA256 哈希" />
          </Steps>
          
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            {status === 'processing' && <Spin tip={progress.message} />}
            {status === 'error' && <Alert message="错误" description={progress.message} type="error" />}
          </div>
        </div>
      )}

      {status === 'success' && result && (
        <div style={{ marginTop: 24 }}>
          <Alert message="处理完成" type="success" showIcon style={{ marginBottom: 16 }} />
          
          <Descriptions title="生成的 SIP 元数据" bordered column={1}>
            <Descriptions.Item label="入库状态">
              <Tag color="green">SUCCESS</Tag> Fixity Check Passed
            </Descriptions.Item>
            <Descriptions.Item label="服务端资产 ID">{result.serverVerification?.asset_id}</Descriptions.Item>
            <Descriptions.Item label="文件名">{result.fileName}</Descriptions.Item>
            <Descriptions.Item label="SHA256 校验和">
              <Paragraph copyable code>{result.hash}</Paragraph>
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">{result.fileSize} 字节</Descriptions.Item>
            <Descriptions.Item label="处理时间">{result.timestamp}</Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">提取的元数据 (JSON)</Divider>
          <Collapse>
            <Panel header="查看原始元数据 (Exif/XMP)" key="1">
              <pre style={{ maxHeight: 300, overflow: 'auto', fontSize: 12 }}>
                {JSON.stringify(result.metadata, null, 2)}
              </pre>
            </Panel>
          </Collapse>
        </div>
      )}
    </Card>
  );
};

export default IngestDemo;
