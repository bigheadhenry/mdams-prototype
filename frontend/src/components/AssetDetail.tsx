import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Descriptions, Divider, List, Space, Spin, Tag, Typography } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Paragraph, Text } = Typography;

interface AssetDetailProps {
  assetId: number;
  onBack: () => void;
  onPreview?: (manifestUrl: string) => void;
}

const statusColorMap: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const formatBytes = (value?: number) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} bytes`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const AssetDetail: React.FC<AssetDetailProps> = ({ assetId, onBack, onPreview }) => {
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await axios.get(`/api/assets/${assetId}`);
      setDetail(res.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || '加载对象详情失败');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [assetId]);

  useEffect(() => {
    if (!detail || detail.status !== 'processing') return;
    const timer = setInterval(() => fetchDetail(true), 3000);
    return () => clearInterval(timer);
  }, [detail]);

  if (loading) {
    return <Spin tip="正在加载对象详情..." />;
  }

  if (error) {
    return (
      <Card>
        <Alert type="error" message="加载失败" description={error} />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回列表</Button>
        </div>
      </Card>
    );
  }

  const technicalMetadata = detail?.technical_metadata || {};
  const statusInfo = detail?.status_info || {};
  const structure = detail?.structure || {};
  const primaryFile = structure?.primary_file || {};
  const originalFile = structure?.original_file || {};
  const derivatives = structure?.derivatives || [];
  const accessPaths = detail?.access_paths || {};
  const outputActions = detail?.output_actions || {};

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        title="资源对象详情"
        extra={<Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回列表</Button>}
      >
        <Descriptions bordered column={1} title="对象摘要">
          <Descriptions.Item label="标题">{detail.title}</Descriptions.Item>
          <Descriptions.Item label="对象标识">
            <Paragraph copyable style={{ marginBottom: 0 }}>{detail.identifier}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="类型">{detail.resource_type_label}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColorMap[statusInfo.code || detail.status] || 'default'}>
              {statusInfo.label || String(detail.status).toUpperCase()}
            </Tag>
            {(statusInfo.message || detail.process_message) && (
              <Text style={{ marginLeft: 8 }}>{statusInfo.message || detail.process_message}</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{detail.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="对象结构 / 文件关系">
        <Alert type="info" showIcon message={structure.summary || '暂无结构说明'} />

        <Divider orientation="left">当前主文件</Divider>
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="角色">{primaryFile.role_label || '-'}</Descriptions.Item>
          <Descriptions.Item label="文件名">{primaryFile.filename || '-'}</Descriptions.Item>
          <Descriptions.Item label="MIME Type">{primaryFile.mime_type || '-'}</Descriptions.Item>
          <Descriptions.Item label="文件大小">{formatBytes(primaryFile.file_size)}</Descriptions.Item>
          <Descriptions.Item label="文件路径">
            {primaryFile.file_path ? <Paragraph copyable style={{ marginBottom: 0 }}>{primaryFile.file_path}</Paragraph> : '-'}
          </Descriptions.Item>
        </Descriptions>

        <Divider orientation="left">原始文件</Divider>
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="角色">{originalFile.role_label || '-'}</Descriptions.Item>
          <Descriptions.Item label="文件名">{originalFile.filename || '-'}</Descriptions.Item>
          <Descriptions.Item label="与当前主文件关系">
            {originalFile.same_as_primary ? '与当前主文件相同' : '独立原始文件'}
          </Descriptions.Item>
          <Descriptions.Item label="文件大小">{formatBytes(originalFile.file_size)}</Descriptions.Item>
          <Descriptions.Item label="文件路径">
            {originalFile.file_path ? <Paragraph copyable style={{ marginBottom: 0 }}>{originalFile.file_path}</Paragraph> : '-'}
          </Descriptions.Item>
        </Descriptions>

        <Divider orientation="left">衍生文件</Divider>
        {derivatives.length > 0 ? (
          <List
            bordered
            dataSource={derivatives}
            renderItem={(item: any) => (
              <List.Item>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Text strong>{item.role_label || item.role}</Text>
                  <Text>文件名：{item.filename || '-'}</Text>
                  <Text>MIME Type：{item.mime_type || '-'}</Text>
                  <Text>文件大小：{formatBytes(item.file_size)}</Text>
                  <Text>生成方式：{item.derivation_method || '-'}</Text>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Alert type="warning" showIcon message="当前对象暂无独立衍生文件记录" />
        )}

        <Divider orientation="left">打包说明</Divider>
        <Alert
          type="success"
          showIcon
          message={structure?.packaging?.bagit_note || '暂无打包说明'}
        />
      </Card>

      <Card title="技术元数据">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="宽度">{technicalMetadata.width ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="高度">{technicalMetadata.height ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="SHA256">
            {technicalMetadata.fixity_sha256 ? (
              <Paragraph copyable code style={{ marginBottom: 0 }}>{technicalMetadata.fixity_sha256}</Paragraph>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="入库方式">{technicalMetadata.ingest_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="转换方式">{technicalMetadata.conversion_method ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="原始文件路径">{technicalMetadata.original_file_path ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="错误信息">{technicalMetadata.error_message ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="访问路径">
        <Space wrap>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            disabled={!accessPaths?.mirador_preview?.enabled}
            onClick={() => onPreview && onPreview(accessPaths?.mirador_preview?.manifest_url)}
          >
            打开 Mirador 预览
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={() => window.open(accessPaths?.manifest?.url, '_blank')}
          >
            查看 IIIF Manifest
          </Button>
        </Space>
      </Card>

      <Card title="输出动作">
        <Space wrap>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = outputActions?.download_current_file?.url;
            }}
          >
            {outputActions?.download_current_file?.label || '下载当前文件'}
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = outputActions?.download_bag?.url;
            }}
          >
            {outputActions?.download_bag?.label || '下载 BagIt 包'}
          </Button>
        </Space>
      </Card>
    </Space>
  );
};

export default AssetDetail;
