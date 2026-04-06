import React from 'react';
import { Alert, Button, Card, Descriptions, Space, Tag, Typography } from 'antd';
import { DownloadOutlined, EyeOutlined, LinkOutlined } from '@ant-design/icons';
import '@google/model-viewer';
import type { ThreeDDetailResponse } from '../types/assets';

const { Text } = Typography;

const WEB_PREVIEW_LABELS: Record<string, string> = {
  ready: '已就绪',
  pending: '准备中',
  disabled: '未启用',
};

const getWebPreviewLabel = (value?: string | null) => {
  if (!value) return '-';
  return WEB_PREVIEW_LABELS[value] || value;
};

const getRendererLabel = (value?: string | null) => {
  if (!value || value === 'model-viewer') return '三维预览器';
  return value;
};

type ThreeDViewerProps = {
  viewer: ThreeDDetailResponse['viewer'] | null | undefined;
  title?: string;
  onOpenPreview?: (url: string) => void;
};

const ThreeDViewer: React.FC<ThreeDViewerProps> = ({ viewer, title, onOpenPreview }) => {
  if (!viewer) {
    return null;
  }

  const previewFile = viewer.preview_file;
  const previewUrl = viewer.preview_url || previewFile?.preview_url || previewFile?.download_url || null;
  const canOpen = Boolean(viewer.enabled && previewUrl);

  return (
    <Card
      size="small"
      title="Web 预览"
      extra={
        <Space wrap>
          <Tag color={viewer.enabled ? 'green' : 'default'}>
            {viewer.enabled ? getWebPreviewLabel('ready') : getWebPreviewLabel('disabled')}
          </Tag>
          <Tag color="blue">{getRendererLabel(viewer.renderer)}</Tag>
        </Space>
      }
    >
      {viewer.enabled && previewUrl ? (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div style={{ borderRadius: 12, overflow: 'hidden', background: '#0b0f14', minHeight: 480 }}>
            <model-viewer
              src={previewUrl}
              alt={title || previewFile?.filename || '三维模型'}
              camera-controls
              auto-rotate
              interaction-prompt="auto"
              shadow-intensity="1"
              exposure="1"
              loading="eager"
              style={{ width: '100%', height: 480, background: '#0b0f14' }}
            />
          </div>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="预览文件">{previewFile?.filename || '-'}</Descriptions.Item>
            <Descriptions.Item label="文件角色">{previewFile?.role_label || previewFile?.role || '-'}</Descriptions.Item>
            <Descriptions.Item label="预览地址">
              {previewUrl ? <Text copyable>{previewUrl}</Text> : '-'}
            </Descriptions.Item>
          </Descriptions>
          <Space wrap>
            {previewUrl ? (
              <Button icon={<EyeOutlined />} onClick={() => onOpenPreview ? onOpenPreview(previewUrl) : window.open(previewUrl, '_blank', 'noopener,noreferrer')}>
                打开预览文件
              </Button>
            ) : null}
            {previewFile?.download_url ? (
              <Button
                icon={<DownloadOutlined />}
                onClick={() => {
                  window.location.href = previewFile.download_url || '';
                }}
              >
                下载预览文件
              </Button>
            ) : null}
            {previewUrl ? (
              <Button icon={<LinkOutlined />} onClick={() => window.open(previewUrl, '_blank', 'noopener,noreferrer')}>
                新标签页打开
              </Button>
            ) : null}
          </Space>
        </Space>
      ) : (
        <Alert
          type="info"
          showIcon
          message={viewer.reason || '当前资源没有可用的 Web 预览。'}
          description={
            previewFile ? (
              <Space direction="vertical" size={0}>
                <Text>候选文件：{previewFile.filename}</Text>
                <Text type="secondary">角色：{previewFile.role_label || previewFile.role}</Text>
              </Space>
            ) : (
              '没有可用于预览的模型文件。'
            )
          }
        />
      )}
      {!canOpen && viewer.preview_file ? (
        <Alert
          style={{ marginTop: 16 }}
          type="warning"
          showIcon
          message="仅支持查看，不支持当前版本直接展示"
          description="该对象已保存对应模型文件，但当前版本未标记为 Web 展示。你仍然可以下载文件或切换到可展示版本。"
        />
      ) : null}
    </Card>
  );
};

export default ThreeDViewer;
