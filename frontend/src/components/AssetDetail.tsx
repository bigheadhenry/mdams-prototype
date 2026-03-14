import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Descriptions, Space, Spin, Tag, Typography } from 'antd';
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
            <Tag color={statusColorMap[detail.status] || 'default'}>{String(detail.status).toUpperCase()}</Tag>
            {detail.process_message && <Text style={{ marginLeft: 8 }}>{detail.process_message}</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{detail.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="文件信息">
        <Descriptions bordered column={1}>
          <Descriptions.Item label="文件名">{detail.file?.filename}</Descriptions.Item>
          <Descriptions.Item label="实际文件名">{detail.file?.actual_filename}</Descriptions.Item>
          <Descriptions.Item label="MIME Type">{detail.file?.mime_type}</Descriptions.Item>
          <Descriptions.Item label="文件大小">{detail.file?.file_size} bytes</Descriptions.Item>
          <Descriptions.Item label="文件路径">
            <Paragraph copyable style={{ marginBottom: 0 }}>{detail.file?.file_path}</Paragraph>
          </Descriptions.Item>
        </Descriptions>
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
        </Descriptions>
      </Card>

      <Card title="访问与输出">
        <Space wrap>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            disabled={!detail.access?.preview_enabled}
            onClick={() => onPreview && onPreview(detail.access?.manifest_url)}
          >
            打开 Mirador 预览
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={() => window.open(detail.access?.manifest_url, '_blank')}
          >
            查看 IIIF Manifest
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = detail.outputs?.download_url;
            }}
          >
            下载当前文件
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              window.location.href = detail.outputs?.download_bag_url;
            }}
          >
            下载 BagIt 包
          </Button>
        </Space>
      </Card>
    </Space>
  );
};

export default AssetDetail;
