import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Breadcrumb,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Empty,
  Image,
  List,
  Row,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd';
import {
  ArrowLeftOutlined,
  BlockOutlined,
  DownloadOutlined,
  EyeOutlined,
  LinkOutlined,
  PictureOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import ThreeDViewer from './ThreeDViewer';
import type {
  AssetDetailFileRecord,
  AssetDetailResponse,
  AssetTechnicalMetadata,
  PaginatedUnifiedResourceList,
  ThreeDDigitalObjectDetailResponse,
  ThreeDDetailResponse,
  UnifiedResourceDetail as UnifiedResourceDetailType,
  UnifiedResourceSummary,
} from '../types/assets';
import type { LifecycleEntry } from '../types/assets';

const { Paragraph, Text, Title } = Typography;

interface UnifiedResourceDetailProps {
  sourceSystem: string;
  sourceId: string;
  onBack: () => void;
  onPreview?: (manifestUrl: string) => void;
  onOpenSourceDetail?: (assetId: number) => void;
  onOpenUnifiedResourceDetail?: (sourceSystem: string, sourceId: string) => void;
}

const statusColorMap: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const STATUS_LABELS: Record<string, string> = {
  ready: '就绪',
  processing: '处理中',
  error: '异常',
};

const RESOURCE_TYPE_LABELS: Record<string, string> = {
  image_2d_cultural_object: '二维影像',
  three_d_model: '三维模型',
  three_d_digital_object: '三维数字对象',
  point_cloud: '点云',
  oblique_photography: '倾斜摄影',
  three_d_package: '三维包',
  video_cultural_object: '文博视频',
};

const getStatusLabel = (status?: string | null) => {
  if (!status) return '-';
  return STATUS_LABELS[status] || status;
};

const getResourceTypeLabel = (resourceType?: string | null) => {
  if (!resourceType) return '-';
  return RESOURCE_TYPE_LABELS[resourceType] || resourceType;
};

const formatBytes = (value?: number | null) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} 字节`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const isAssetDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is AssetDetailResponse => Boolean(value && 'lifecycle' in value && 'output_actions' in value);

const isThreeDDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is ThreeDDetailResponse => Boolean(value && 'production_records' in value && 'viewer' in value);

const isThreeDDigitalObjectDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is ThreeDDigitalObjectDetailResponse => Boolean(value && 'representations' in value && 'default_preview' in value);

const looksLikeVideo = (value: UnifiedResourceDetailType['source_record']): boolean =>
  Boolean(value && 'mime_type' in value && !('lifecycle' in value) && !('production_records' in value) && !('representations' in value));

const SectionTitle: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <Space direction="vertical" size={0} style={{ marginBottom: 12 }}>
    <Title level={5} style={{ margin: 0 }}>
      {title}
    </Title>
    {subtitle && <Text type="secondary">{subtitle}</Text>}
  </Space>
);

const UnifiedResourceDetail: React.FC<UnifiedResourceDetailProps> = ({
  sourceSystem,
  sourceId,
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
  const [selectedRepId, setSelectedRepId] = useState<number | null>(null);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get<UnifiedResourceDetailType>(`/api/platform/resources/${sourceSystem}/${sourceId}`);
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
  }, [sourceId, sourceSystem]);

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
        const res = await axios.get<PaginatedUnifiedResourceList>('/api/platform/resources', {
          params: {
            source_system: detail.source_system,
            resource_type: detail.resource_type,
            limit: 4,
          },
        });
        setRelatedResources(
          res.data.items
            .filter((item) => item.id !== detail.id)
            .slice(0, 4),
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
  const assetRecord = isAssetDetailRecord(sourceRecord) ? sourceRecord : null;
  const threeDRecord = isThreeDDetailRecord(sourceRecord) ? sourceRecord : null;
  const threeDObjectRecord = isThreeDDigitalObjectDetailRecord(sourceRecord) ? sourceRecord : null;
  const defaultThreeDRecord = threeDRecord ?? threeDObjectRecord?.default_preview ?? null;

  // 3D 表现选择器：当有多个表现时，构建选项列表并取当前选中表现的 viewer
  const repOptions = useMemo(() => {
    if (!threeDObjectRecord?.representations || threeDObjectRecord.representations.length <= 1) return null;
    return threeDObjectRecord.representations.map((rep) => ({
      value: rep.id,
      label: `${rep.representation_label} · ${rep.version_label}`,
      disabled: !rep.preview_enabled,
    }));
  }, [threeDObjectRecord]);

  const selectedRepViewer = useMemo(() => {
    if (!selectedRepId || !threeDObjectRecord?.representations) return null;
    const rep = threeDObjectRecord.representations.find((r) => r.id === selectedRepId);
    return rep?.viewer ?? null;
  }, [selectedRepId, threeDObjectRecord]);

  // 3D viewer 数据：优先使用选中表示的 viewer，否则用默认
  const activeViewer = repOptions
    ? (selectedRepViewer ?? defaultThreeDRecord?.viewer ?? null)
    : (defaultThreeDRecord?.viewer ?? null);

  // 当详情加载完成后，如果还没选过表现，自动选默认预览表现
  useEffect(() => {
    if (threeDObjectRecord && repOptions && selectedRepId === null) {
      setSelectedRepId(
        threeDObjectRecord.default_preview_representation_id
        ?? threeDObjectRecord.representations[0]?.id
        ?? null,
      );
    }
  }, [threeDObjectRecord, repOptions, selectedRepId]);

  const technicalMetadata: AssetTechnicalMetadata | undefined = assetRecord?.technical_metadata;
  const manifestUrl = detail?.manifest_url;
  const previewEnabled = detail?.preview_enabled ?? false;
  const previewImageUrl = assetRecord?.outputs.download_url || manifestUrl || '';
  const canShowImagePreview = Boolean(
    assetRecord?.file.mime_type?.startsWith('image/') && previewImageUrl,
  );
  const canShowThreeDPreview = Boolean(activeViewer?.enabled);
  const isVideo = looksLikeVideo(sourceRecord) || detail?.resource_type === 'video_cultural_object';
  const canShowVideoPreview = Boolean(isVideo && previewEnabled && manifestUrl);

  const lifecycleItems = useMemo(() => assetRecord?.lifecycle || [], [assetRecord]);
  const derivativeRecords = assetRecord?.structure.derivatives || [];
  const threeDTechnicalItems = useMemo(
    () => Object.entries(defaultThreeDRecord?.technical_metadata || {})
      .filter(([, value]) => value !== null && value !== undefined && value !== '')
      .slice(0, 8),
    [defaultThreeDRecord],
  );
  const displayFilename = assetRecord?.file.filename || defaultThreeDRecord?.file.filename || detail?.title || '-';
  const summaryText = sourceRecord?.structure.summary || '当前资源已接入统一平台目录。';

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
      <Breadcrumb
        style={{ marginBottom: 12 }}
        items={[
          {
            title: (
              <a onClick={onBack} style={{ cursor: 'pointer' }}>
                统一检索
              </a>
            ),
          },
          { title: detail?.title || '资源详情' },
        ]}
      />
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
          {repOptions && (
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>
                选择表现：
              </Text>
              <Select
                size="small"
                style={{ minWidth: 220 }}
                value={selectedRepId ?? undefined}
                onChange={(value) => setSelectedRepId(value)}
                options={repOptions}
              />
            </div>
          )}
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
            {canShowThreeDPreview ? (
              <div style={{ width: '100%' }}>
                <ThreeDViewer viewer={activeViewer ?? undefined} title={detail.title} />
              </div>
            ) : canShowVideoPreview ? (
              <video
                controls
                style={{ width: '100%', maxHeight: 480, borderRadius: 8 }}
                src={manifestUrl}
              >
                您的浏览器不支持视频播放。
              </video>
            ) : canShowImagePreview ? (
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
              {canShowThreeDPreview ? (
                <EyeOutlined style={{ fontSize: 24, color: '#52c41a' }} />
              ) : canShowImagePreview ? (
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
              <Text strong>{displayFilename}</Text>
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
              <Text type="secondary">{summaryText}</Text>
            </Space>

            <Descriptions column={1} size="small" labelStyle={{ width: 96, color: '#8c8c8c' }}>
              <Descriptions.Item label="文物号">
                <Paragraph copyable style={{ marginBottom: 0 }}>
                  {detail.id}
                </Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="来源">{detail.source_label}</Descriptions.Item>
              <Descriptions.Item label="分类">{getResourceTypeLabel(detail.resource_type)}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusColorMap[detail.status] || 'default'}>{getStatusLabel(detail.status)}</Tag>
                {assetRecord?.status_info.message && (
                  <Text style={{ marginLeft: 8 }}>{assetRecord.status_info.message}</Text>
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
                onClick={() => {
                  if (threeDRecord?.viewer?.preview_url) {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    return;
                  }
                  if (manifestUrl) {
                    onPreview?.(manifestUrl);
                  }
                }}
              >
                {defaultThreeDRecord ? '查看三维预览' : '打开预览'}
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
                disabled={!(assetRecord?.outputs.download_url || defaultThreeDRecord?.outputs.download_url)}
                onClick={() => {
                  const downloadUrl = assetRecord?.outputs.download_url || defaultThreeDRecord?.outputs.download_url;
                  if (downloadUrl) {
                    window.location.href = downloadUrl;
                  }
                }}
              >
                {defaultThreeDRecord ? '下载默认资源包' : '下载原文件'}
              </Button>
              <Button
                icon={<DownloadOutlined />}
                disabled={!assetRecord?.outputs.download_bag_url}
                onClick={() => {
                  if (assetRecord?.outputs.download_bag_url) {
                    window.location.href = assetRecord.outputs.download_bag_url;
                  }
                }}
              >
                下载 BagIt
              </Button>
              <Button
                icon={<LinkOutlined />}
                disabled={!sourceRecord}
                onClick={() => {
                  if (!sourceRecord) return;
                  if (assetRecord && onOpenSourceDetail) {
                    onOpenSourceDetail(assetRecord.id);
                    return;
                  }
                  window.open(detail.source_detail_url, '_blank', 'noopener,noreferrer');
                }}
              >
                查看源详情
              </Button>
            </Space>
          </Space>
        </Card>
      </div>

      {sourceRecord && (
        <Space data-testid="unified-resource-detail" direction="vertical" size="large" style={{ width: '100%' }}>
          <Card bordered={false}>
            <SectionTitle title="结构与文件" subtitle="统一详情只展示平台层摘要，源详情保留完整结构信息。" />
            <Alert type="info" showIcon message={sourceRecord.structure.summary || '暂无结构说明'} style={{ marginBottom: 16 }} />

            {assetRecord ? (
              <>
                <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
                  <Descriptions.Item label="主文件">{assetRecord.structure.primary_file.filename}</Descriptions.Item>
                  <Descriptions.Item label="原始文件">{assetRecord.structure.original_file.filename}</Descriptions.Item>
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
                          <Text>MIME 类型：{item.mime_type || '-'}</Text>
                          <Text>文件大小：{formatBytes(item.file_size)}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Alert type="warning" showIcon message="当前对象暂无独立衍生文件记录。" />
                )}
              </>
            ) : threeDObjectRecord ? (
              <List
                bordered
                dataSource={threeDObjectRecord.representations}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Space wrap>
                        <Text strong>{item.representation_label}</Text>
                        <Tag>{item.representation_type}</Tag>
                        <Tag>{item.version_label}</Tag>
                        {item.id === threeDObjectRecord.default_preview_representation_id ? (
                          <Tag color="green">默认预览</Tag>
                        ) : null}
                      </Space>
                      <Text>表现标题：{item.title}</Text>
                      <Text>文件数量：{item.file_count}</Text>
                      <Space wrap>
                        {(item.file_groups || []).map((group) => (
                          <Tag key={`${item.id}-${group.role}`}>
                            {group.role_label} {group.file_count}
                          </Tag>
                        ))}
                      </Space>
                      <Space wrap>
                        <Button
                          size="small"
                          icon={<EyeOutlined />}
                          disabled={!item.preview_enabled}
                          onClick={() => window.open(item.detail_url || `/api/three-d/resources/${item.id}`, '_blank', 'noopener,noreferrer')}
                        >
                          打开表现
                        </Button>
                        <Button
                          size="small"
                          icon={<DownloadOutlined />}
                          disabled={!item.download_url}
                          onClick={() => {
                            if (item.download_url) {
                              window.location.href = item.download_url;
                            }
                          }}
                        >
                          下载资源包
                        </Button>
                      </Space>
                    </Space>
                  </List.Item>
                )}
              />
            ) : isVideo ? (
              <Alert
                type="info"
                showIcon
                message="视频文件"
                description={
                  <Space direction="vertical" size={4}>
                    <Text>文件名：{detail?.title || '-'}</Text>
                    <Text>流媒体地址：{manifestUrl}</Text>
                  </Space>
                }
              />
            ) : (
              <List
                bordered
                dataSource={threeDRecord?.structure.files || []}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Space wrap>
                        <Text strong>{item.role_label || item.role}</Text>
                        {item.is_primary && <Tag color="green">主文件</Tag>}
                      </Space>
                      <Text>文件名：{item.filename || '-'}</Text>
                      <Text>MIME 类型：{item.mime_type || '-'}</Text>
                      <Text>文件大小：{formatBytes(item.file_size)}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>

          <Card bordered={false}>
            <SectionTitle title="技术元数据" subtitle="保留源系统提供的核心技术字段。" />
            {assetRecord ? (
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
            ) : isVideo ? (
              <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="文件名">{detail?.title || '-'}</Descriptions.Item>
                <Descriptions.Item label="MIME 类型">{(sourceRecord as any)?.mime_type as string || '-'}</Descriptions.Item>
                <Descriptions.Item label="文件大小">{formatBytes((sourceRecord as any)?.file_size as number)}</Descriptions.Item>
                <Descriptions.Item label="时长">{(sourceRecord as any)?.duration_seconds != null ? `${(sourceRecord as any).duration_seconds} 秒` : '-'}</Descriptions.Item>
                <Descriptions.Item label="尺寸">{(sourceRecord as any)?.width != null ? `${(sourceRecord as any).width} x ${(sourceRecord as any).height}` : '-'}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Descriptions bordered column={1} size="small">
                {threeDTechnicalItems.map(([key, value]) => (
                  <Descriptions.Item key={key} label={key}>
                    {String(value)}
                  </Descriptions.Item>
                ))}
              </Descriptions>
            )}
          </Card>

          <Card bordered={false}>
            <SectionTitle title="生命周期" subtitle="统一平台按源对象的处理轨迹展示。" />
            {assetRecord ? (
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
            ) : threeDObjectRecord ? (
              <List
                bordered
                dataSource={threeDObjectRecord.representations}
                locale={{ emptyText: '当前三维数字对象暂无模型表现。' }}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Space wrap>
                        <Text strong>{item.representation_label}</Text>
                        <Tag>{item.version_label}</Tag>
                        {item.is_current ? <Tag color="blue">当前</Tag> : null}
                        <Tag color={item.preview_enabled ? 'green' : 'default'}>
                          {item.preview_enabled ? '可预览' : '不可预览'}
                        </Tag>
                      </Space>
                      <Text type="secondary">
                        {item.title} · {item.file_count} 个文件 · 保存层级：{item.preservation?.storage_tier || '-'}
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            ) : isVideo ? (
              <Alert
                type="info"
                showIcon
                message="暂无生产事件记录"
                description="视频资源暂未关联生命周期事件。"
              />
            ) : (
              <List
                bordered
                dataSource={threeDRecord?.production_records || []}
                locale={{ emptyText: '当前三维对象暂无生产事件记录。' }}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <Space wrap>
                        <Text strong>{item.event_type}</Text>
                        <Tag color={statusColorMap[item.status] || 'default'}>{item.stage}</Tag>
                      </Space>
                      <Text type="secondary">{item.description || item.evidence || '-'}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            )}
          </Card>

          <Card bordered={false}>
            <SectionTitle title="相关推荐" subtitle="同来源同类型的相近资源。" />
            {relatedLoading ? (
              <Spin tip="正在加载相关推荐..." />
            ) : relatedResources.length > 0 ? (
              <Row gutter={[16, 16]}>
                {relatedResources.map((item) => (
                  <Col key={item.id} xl={6} lg={8} md={12} sm={24}>
                    <Card
                      hoverable
                      size="small"
                      style={{ height: '100%', cursor: 'pointer' }}
                      onClick={() =>
                        onOpenUnifiedResourceDetail?.(item.source_system, item.source_id)
                      }
                      cover={
                        <div
                          style={{
                            height: 120,
                            background: '#fafafa',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            overflow: 'hidden',
                          }}
                        >
                          {item.thumbnail_url ? (
                            <Image
                              src={item.thumbnail_url}
                              alt={item.title}
                              style={{
                                maxHeight: '100%',
                                maxWidth: '100%',
                                objectFit: 'cover',
                              }}
                              preview={false}
                            />
                          ) : item.source_system === 'three_d' ? (
                            <BlockOutlined
                              style={{ fontSize: 36, color: '#bfbfbf' }}
                            />
                          ) : (
                            <PictureOutlined
                              style={{ fontSize: 36, color: '#d9d9d9' }}
                            />
                          )}
                        </div>
                      }
                    >
                      <Card.Meta
                        title={
                          <Text ellipsis={{ tooltip: item.title }} strong style={{ fontSize: 13 }}>
                            {item.title || '(无标题)'}
                          </Text>
                        }
                        description={
                          <Space direction="vertical" size={4}>
                            <Tag
                              color={item.preview_enabled ? 'green' : 'blue'}
                              style={{ fontSize: 11 }}
                            >
                              {item.preview_enabled ? '可预览' : '不可预览'}
                            </Tag>
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              {item.source_label} · {item.updated_at}
                            </Text>
                          </Space>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
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
