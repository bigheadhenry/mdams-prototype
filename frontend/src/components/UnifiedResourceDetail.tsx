import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Empty,
  List,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  EyeOutlined,
  LinkOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import type {
  AssetTechnicalMetadata,
  UnifiedResourceDetail as UnifiedResourceDetailType,
  UnifiedResourceSummary,
} from '../types/assets';
import type { LifecycleEntry } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

interface UnifiedResourceDetailProps {
  resourceId: string;
  onBack: () => void;
  onPreview?: (manifestUrl: string) => void;
  onOpenSourceDetail?: (assetId: number) => void;
  onOpenUnifiedResourceDetail?: (resourceId: string) => void;
}

const statusColorMap: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const formatBytes = (value?: number | null) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} bytes`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const SectionTitle: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <Space direction="vertical" size={0} style={{ marginBottom: 12 }}>
    <Title level={5} style={{ margin: 0 }}>
      {title}
    </Title>
    {subtitle && <Text type="secondary">{subtitle}</Text>}
  </Space>
);

const UnifiedResourceDetail: React.FC<UnifiedResourceDetailProps> = ({
  resourceId,
  onBack,
  onPreview,
  onOpenSourceDetail,
  onOpenUnifiedResourceDetail,
}) => {
  const [detail, setDetail] = useState<UnifiedResourceDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [relatedResources, setRelatedResources] = useState<UnifiedResourceSummary[]>([]);
  const [relatedLoading, setRelatedLoading] = useState(false);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get<UnifiedResourceDetailType>(`/api/platform/resources/${resourceId}`);
      setDetail(res.data);
      setError(null);
    } catch (err: unknown) {
      console.error(err);
      if (axios.isAxiosError(err)) {
        const detailMessage = err.response?.data && typeof err.response.data === 'object'
          ? (err.response.data as { detail?: string }).detail
          : undefined;
        setError(detailMessage || '加载统一资源详情失败');
      } else {
        setError('加载统一资源详情失败');
      }
    } finally {
      setLoading(false);
    }
  }, [resourceId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  useEffect(() => {
    const loadRelatedResources = async () => {
      if (!detail) {
        setRelatedResources([]);
        return;
      }

      setRelatedLoading(true);
      try {
        const res = await axios.get<UnifiedResourceSummary[]>('/api/platform/resources', {
          params: {
            source_system: detail.source_system,
            resource_type: detail.resource_type,
          },
        });
        setRelatedResources(
          res.data
            .filter((item) => item.id !== detail.id)
            .slice(0, 3),
        );
      } catch (err) {
        console.error(err);
        setRelatedResources([]);
      } finally {
        setRelatedLoading(false);
      }
    };

    void loadRelatedResources();
  }, [detail]);

  const sourceRecord = detail?.source_record ?? null;
  const technicalMetadata: AssetTechnicalMetadata | undefined = sourceRecord?.technical_metadata;
  const manifestUrl = detail?.manifest_url;
  const previewEnabled = detail?.preview_enabled ?? false;
  const previewImageUrl = sourceRecord?.outputs.download_url || manifestUrl || '';
  const canShowImagePreview = Boolean(
    sourceRecord?.file.mime_type?.startsWith('image/') && previewImageUrl,
  );

  const lifecycleItems = useMemo(() => sourceRecord?.lifecycle || [], [sourceRecord]);
  const derivativeRecords = sourceRecord?.structure.derivatives || [];

  if (loading) return <Spin tip="正在加载统一资源详情..." />;

  if (error) {
    return (
      <Card>
        <Alert type="error" message="加载失败" description={error} />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回目录</Button>
        </div>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card>
        <Alert type="warning" message="暂无统一资源数据" />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回目录</Button>
        </div>
      </Card>
    );
  }

  return (
    <div style={{ maxWidth: 1240, margin: '0 auto', paddingBottom: 32 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
          返回目录
        </Button>
      </Space>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(420px, 1.15fr) minmax(320px, 0.85fr)',
          gap: 24,
          alignItems: 'start',
          marginBottom: 24,
        }}
      >
        <Card
          bordered={false}
          style={{ background: '#f5f4fb' }}
          bodyStyle={{ padding: 20 }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 480,
              borderRadius: 16,
              background: 'linear-gradient(180deg, #1a1a1a 0%, #f2f2f2 100%)',
              overflow: 'hidden',
            }}
          >
            {canShowImagePreview ? (
              <img
                src={previewImageUrl}
                alt={detail.title}
                style={{
                  width: '100%',
                  maxHeight: 480,
                  objectFit: 'contain',
                  display: 'block',
                }}
              />
            ) : (
              <Empty
                image={<PictureOutlined style={{ fontSize: 48, color: '#9aa0a6' }} />}
                description="暂无可视化预览"
              />
            )}
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
            <div
              style={{
                width: 72,
                height: 72,
                borderRadius: 12,
                overflow: 'hidden',
                background: '#fff',
                border: '1px solid #e8e8e8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {canShowImagePreview ? (
                <img
                  src={previewImageUrl}
                  alt={`${detail.title} 缩略图`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <PictureOutlined style={{ fontSize: 24, color: '#b4b9c0' }} />
              )}
            </div>
            <Space direction="vertical" size={0}>
              <Text type="secondary">资源预览</Text>
              <Text strong>{sourceRecord?.file.filename || detail.title}</Text>
              <Text type="secondary">统一 ID：{detail.id}</Text>
            </Space>
          </div>
        </Card>

        <Card bordered={false} bodyStyle={{ padding: 24 }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Space direction="vertical" size={4}>
              <Title level={3} style={{ margin: 0 }}>
                {detail.title}
              </Title>
              <Text type="secondary">{sourceRecord?.structure.summary || '当前资源已接入统一平台目录。'}</Text>
            </Space>

            <Descriptions column={1} size="small" labelStyle={{ width: 96, color: '#8c8c8c' }}>
              <Descriptions.Item label="文物号">
                <Paragraph copyable style={{ marginBottom: 0 }}>
                  {detail.id}
                </Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="来源">{detail.source_label}</Descriptions.Item>
              <Descriptions.Item label="分类">{detail.resource_type}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusColorMap[detail.status] || 'default'}>{detail.status}</Tag>
                {sourceRecord?.status_info.message && (
                  <Text style={{ marginLeft: 8 }}>{sourceRecord.status_info.message}</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="预览">
                {previewEnabled ? '可预览' : '不可预览'}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">{detail.updated_at}</Descriptions.Item>
            </Descriptions>

            <Divider style={{ margin: '8px 0' }} />

            <Space wrap>
              <Button
                type="primary"
                icon={<EyeOutlined />}
                disabled={!previewEnabled || !manifestUrl}
                onClick={() => manifestUrl && onPreview?.(manifestUrl)}
              >
                打开预览
              </Button>
              <Button
                icon={<LinkOutlined />}
                disabled={!manifestUrl}
                onClick={() => manifestUrl && window.open(manifestUrl, '_blank', 'noopener,noreferrer')}
              >
                查看 Manifest
              </Button>
              <Button
                icon={<DownloadOutlined />}
                disabled={!sourceRecord?.outputs.download_url}
                onClick={() => {
                  if (sourceRecord?.outputs.download_url) {
                    window.location.href = sourceRecord.outputs.download_url;
                  }
                }}
              >
                下载原文件
              </Button>
              <Button
                icon={<DownloadOutlined />}
                disabled={!sourceRecord?.outputs.download_bag_url}
                onClick={() => {
                  if (sourceRecord?.outputs.download_bag_url) {
                    window.location.href = sourceRecord.outputs.download_bag_url;
                  }
                }}
              >
                下载 BagIt
              </Button>
              <Button
                icon={<LinkOutlined />}
                disabled={!sourceRecord}
                onClick={() => sourceRecord && onOpenSourceDetail?.(sourceRecord.id)}
              >
                查看源详情
              </Button>
            </Space>
          </Space>
        </Card>
      </div>

      {sourceRecord && (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card bordered={false}>
            <SectionTitle title="生命周期" subtitle="统一平台按源对象的处理轨迹展示。" />
            <List
              bordered
              dataSource={lifecycleItems}
              renderItem={(item: LifecycleEntry) => (
                <List.Item>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space wrap>
                      <Text strong>{item.label}</Text>
                      <Tag color={statusColorMap[item.status] || 'default'}>{item.status_label}</Tag>
                    </Space>
                    <Text type="secondary">{item.description}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>

          <Card bordered={false}>
            <SectionTitle title="结构与文件" subtitle="统一详情只展示平台层摘要，源详情保留完整结构信息。" />
            <Alert type="info" showIcon message={sourceRecord.structure.summary || '暂无结构说明'} style={{ marginBottom: 16 }} />

            <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="主文件">{sourceRecord.structure.primary_file.filename}</Descriptions.Item>
              <Descriptions.Item label="原始文件">{sourceRecord.structure.original_file.filename}</Descriptions.Item>
              <Descriptions.Item label="衍生文件数">{derivativeRecords.length}</Descriptions.Item>
            </Descriptions>

            {derivativeRecords.length > 0 ? (
              <List
                bordered
                dataSource={derivativeRecords}
                renderItem={(item: AssetDetailFileRecord) => (
                  <List.Item>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Text strong>{item.role_label || item.role || '-'}</Text>
                      <Text>文件名：{item.filename || '-'}</Text>
                      <Text>MIME Type：{item.mime_type || '-'}</Text>
                      <Text>文件大小：{formatBytes(item.file_size)}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            ) : (
              <Alert type="warning" showIcon message="当前对象暂无独立衍生文件记录。" />
            )}
          </Card>

          <Card bordered={false}>
            <SectionTitle title="技术元数据" subtitle="保留与影像处理相关的核心字段。" />
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="宽度">{technicalMetadata?.width ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="高度">{technicalMetadata?.height ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="SHA256">
                {technicalMetadata?.fixity_sha256 ? (
                  <Paragraph copyable code style={{ marginBottom: 0 }}>
                    {technicalMetadata.fixity_sha256}
                  </Paragraph>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="入库方式">{technicalMetadata?.ingest_method ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="转换方式">{technicalMetadata?.conversion_method ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="原始文件路径">{technicalMetadata?.original_file_path ?? '-'}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card bordered={false}>
            <SectionTitle title="相关推荐" subtitle="同来源同类型的相近资源。" />
            {relatedLoading ? (
              <Spin tip="正在加载相关推荐..." />
            ) : relatedResources.length > 0 ? (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: 16,
                }}
              >
                {relatedResources.map((item) => (
                  <Card
                    key={item.id}
                    size="small"
                    hoverable
                    onClick={() => onOpenUnifiedResourceDetail?.(item.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Tag color={item.preview_enabled ? 'green' : 'blue'}>
                        {item.preview_enabled ? '可预览' : '不可预览'}
                      </Tag>
                      <Text strong>{item.title}</Text>
                      <Text type="secondary">{item.id}</Text>
                      <Text type="secondary">{item.source_label}</Text>
                      <Button size="small" type="link" style={{ padding: 0 }}>
                        查看详情
                      </Button>
                    </Space>
                  </Card>
                ))}
              </div>
            ) : (
              <Alert type="info" showIcon message="暂无相关推荐。" />
            )}
          </Card>
        </Space>
      )}
    </div>
  );
};

export default UnifiedResourceDetail;
