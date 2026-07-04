import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Anchor,
  Breadcrumb,
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Divider,
  Dropdown,
  Empty,
  Image,
  List,
  Row,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Timeline,
  Tooltip,
  Typography,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  ArrowLeftOutlined,
  BlockOutlined,
  DownloadOutlined,
  EyeOutlined,
  LinkOutlined,
  MoreOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  DownOutlined,
  RightOutlined,
  FileOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import ThreeDViewer from './ThreeDViewer';
import ThreeDSourceDetailDrawer from './ThreeDSourceDetailDrawer';
import { getFieldLabel } from '../utils/metadataLabels';
import type {
  AssetDetailFileRecord,
  AssetDetailResponse,
  AssetTechnicalMetadata,
  PaginatedUnifiedResourceList,
  ThreeDDigitalObjectDetailResponse,
  ThreeDDetailResponse,
  UnifiedResourceDetail as UnifiedResourceDetailType,
  UnifiedResourceSummary,
  ThreeDFileRecord,
  RightsDisplay,
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
  onAddToApplication?: (resource: UnifiedResourceDetailType) => boolean;
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

const SOURCE_DIMENSION_LABEL: Record<string, string> = {
  image_2d: '二维',
  three_d: '三维',
  video: '视频',
};

const SOURCE_TAB_KEY: Record<string, string> = {
  image_2d: '2d',
  three_d: '3d',
  video: 'video',
};

const getStatusLabel = (status?: string | null) =>
  !status ? '-' : STATUS_LABELS[status] || status;

const getResourceTypeLabel = (resourceType?: string | null) =>
  !resourceType ? '-' : RESOURCE_TYPE_LABELS[resourceType] || resourceType;

const formatBytes = (value?: number | null) => {
  if (value === undefined || value === null) return '-';
  if (value < 1024) return `${value} 字节`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
};

const formatDuration = (seconds?: number | null) => {
  if (seconds === undefined || seconds === null) return '-';
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes > 0 ? `${minutes}分${String(rest).padStart(2, '0')}秒` : `${rest}秒`;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value && typeof value === 'object' && !Array.isArray(value));

const buildMetadataRows = (metadata?: Record<string, unknown> | null) =>
  Object.entries(metadata || {})
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => ({ key, field: key, value }));

const NestedRecordValue: React.FC<{
  value: Record<string, unknown>;
  depth: number;
}> = ({ value, depth }) => {
  const [expanded, setExpanded] = useState(false);
  const fieldCount = Object.keys(value).length;
  if (fieldCount === 0) return <>-</>;
  if (!expanded) {
    return (
      <Button type="link" size="small" onClick={() => setExpanded(true)} style={{ padding: 0 }}>
        {fieldCount} 个字段 ▸ 展开
      </Button>
    );
  }
  return (
    <Space direction="vertical" size={4} style={{ width: '100%' }}>
      <Button type="link" size="small" onClick={() => setExpanded(false)} style={{ padding: 0 }}>
        ▾ 收起
      </Button>
      <Table
        size="small"
        pagination={false}
        rowKey="key"
        dataSource={buildMetadataRows(value)}
        columns={[
          { title: '字段', dataIndex: 'field', key: 'field', width: 180 },
          {
            title: '值',
            dataIndex: 'value',
            key: 'value',
            render: (v: unknown) => renderMetadataValue(v, depth + 1),
          },
        ]}
      />
    </Space>
  );
};

const renderMetadataValue = (value: unknown, depth = 0): React.ReactNode => {
  if (value === null || value === undefined || value === '') return '-';
  if (Array.isArray(value)) {
    if (!value.length) return '-';
    if (value.every(isRecord)) {
      const columnKeys = Array.from(
        new Set(value.flatMap((item) => Object.keys(item))),
      ).slice(0, 6);
      return (
        <Table
          size="small"
          pagination={false}
          rowKey={(_, index) => String(index)}
          dataSource={value}
          columns={columnKeys.map((key) => ({
            title: key,
            dataIndex: key,
            key,
            render: (cellValue: unknown) => renderMetadataValue(cellValue, depth + 1),
          }))}
        />
      );
    }
    return (
      <Space wrap>
        {value.map((item, index) => (
          <Tag key={`${String(item)}-${index}`}>{renderMetadataValue(item, depth + 1)}</Tag>
        ))}
      </Space>
    );
  }
  if (isRecord(value)) {
    if (depth >= 2) {
      return <NestedRecordValue value={value} depth={depth} />;
    }
    return (
      <Table
        size="small"
        pagination={false}
        rowKey="key"
        dataSource={buildMetadataRows(value)}
        columns={[
          { title: '字段', dataIndex: 'field', key: 'field', width: 180 },
          {
            title: '值',
            dataIndex: 'value',
            key: 'value',
            render: (cellValue: unknown) => renderMetadataValue(cellValue, depth + 1),
          },
        ]}
      />
    );
  }
  return String(value);
};

const MetadataTable: React.FC<{ data?: Record<string, unknown> | null }> = ({ data }) => (
  <Table
    size="small"
    pagination={false}
    rowKey="key"
    dataSource={buildMetadataRows(data)}
    locale={{ emptyText: '暂无技术元数据' }}
    columns={[
      { title: '字段', dataIndex: 'field', key: 'field', width: 220 },
      {
        title: '值',
        dataIndex: 'value',
        key: 'value',
        render: (value: unknown) => renderMetadataValue(value),
      },
    ]}
  />
);

const isAssetDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is AssetDetailResponse =>
  Boolean(value && 'lifecycle' in value && 'output_actions' in value);

const isThreeDDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is ThreeDDetailResponse =>
  Boolean(value && 'production_records' in value && 'viewer' in value);

const isThreeDDigitalObjectDetailRecord = (
  value: UnifiedResourceDetailType['source_record'],
): value is ThreeDDigitalObjectDetailResponse =>
  Boolean(value && 'representations' in value && 'default_preview' in value);

const looksLikeVideo = (value: UnifiedResourceDetailType['source_record']): boolean =>
  Boolean(
    value &&
      'mime_type' in value &&
      !('lifecycle' in value) &&
      !('production_records' in value) &&
      !('representations' in value),
  );

const SectionTitle: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <Space direction="vertical" size={0} style={{ marginBottom: 12 }}>
    <Title level={5} style={{ margin: 0 }}>
      {title}
    </Title>
    {subtitle && <Text type="secondary">{subtitle}</Text>}
  </Space>
);

const renderRightsPanel = (rights?: RightsDisplay | null) => {
  if (!rights) return null;

  const isOpen = rights.copyright_status === '公共领域';

  return (
    <div style={{
      background: isOpen ? '#f6ffed' : '#fffbe6',
      border: `1px solid ${isOpen ? '#b7eb8f' : '#ffe58f'}`,
      borderLeft: `4px solid ${isOpen ? '#52c41a' : '#faad14'}`,
      borderRadius: 8,
      padding: '10px 16px',
      marginBottom: 16,
    }}>
      <div style={{ fontWeight: 500, fontSize: 14, color: isOpen ? '#135200' : '#ad6800', marginBottom: 4 }}>
        {rights.statement}
        {rights.copyright_status && (
          <span style={{
            display: 'inline-block', marginLeft: 8, padding: '1px 6px', borderRadius: 4,
            fontSize: 11, background: isOpen ? 'rgba(82,196,26,0.15)' : 'rgba(250,173,20,0.15)',
          }}>
            {rights.copyright_status}
          </span>
        )}
      </div>
      <Space size="large" wrap style={{ fontSize: 12, color: '#8c8c8c' }}>
        {rights.credit_line && <span>署名：{rights.credit_line}</span>}
        {rights.license && (
          <span>
            许可：
            {rights.license_url ? (
              <a href={rights.license_url} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>
                {rights.license} ↗
              </a>
            ) : (
              <span style={{ color: '#1890ff' }}>{rights.license}</span>
            )}
          </span>
        )}
        {rights.usage_restrictions && <span style={{ color: '#faad14' }}>⚠ {rights.usage_restrictions}</span>}
      </Space>
    </div>
  );
};

const scrollToHero = () => {
  const el = document.querySelector('.unified-resource-hero');
  if (el) (el as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'start' });
};

const persistTabHint = (sourceSystem: string) => {
  const tabKey = SOURCE_TAB_KEY[sourceSystem];
  if (tabKey && typeof window !== 'undefined') {
    try {
      window.sessionStorage.setItem('platform_directory_active_tab', tabKey);
    } catch {
      /* ignore storage errors */
    }
  }
};

const UnifiedResourceDetail: React.FC<UnifiedResourceDetailProps> = ({
  sourceSystem,
  sourceId,
  onBack,
  onPreview,
  onOpenSourceDetail,
  onOpenUnifiedResourceDetail,
  onAddToApplication,
}) => {
  const [detail, setDetail] = useState<UnifiedResourceDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [relatedResources, setRelatedResources] = useState<UnifiedResourceSummary[]>([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [selectedRepId, setSelectedRepId] = useState<number | null>(null);
  const [expandedRepFiles, setExpandedRepFiles] = useState<
    Record<number, ThreeDFileRecord[]>
  >({});
  const [loadingRepFiles, setLoadingRepFiles] = useState<Record<number, boolean>>({});
  const [sourceDetailDrawerOpen, setSourceDetailDrawerOpen] = useState(false);
  const [sourceDetailData, setSourceDetailData] = useState<ThreeDDetailResponse | null>(null);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get<UnifiedResourceDetailType>(
        `/api/platform/resources/${sourceSystem}/${sourceId}`,
      );
      setDetail(res.data);
      setError(null);
    } catch (err: unknown) {
      console.error(err);
      if (axios.isAxiosError(err)) {
        const detailMessage =
          err.response?.data && typeof err.response.data === 'object'
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

  const loadRepFiles = useCallback(
    async (repId: number, detailUrl?: string | null) => {
      if (expandedRepFiles[repId]) {
        setExpandedRepFiles((prev) => {
          const next = { ...prev };
          delete next[repId];
          return next;
        });
        return;
      }
      setLoadingRepFiles((prev) => ({ ...prev, [repId]: true }));
      try {
        const apiUrl = detailUrl || `/api/three-d/resources/${repId}`;
        const res = await axios.get<ThreeDDetailResponse>(apiUrl);
        const files: ThreeDFileRecord[] = (res.data.structure.files || []).map((f) => ({
          id: f.id ?? null,
          filename: f.filename,
          file_path: f.file_path,
          actual_filename: f.actual_filename,
          file_size: f.file_size,
          mime_type: f.mime_type ?? null,
          role: f.role,
          role_label: f.role_label,
          is_primary: Boolean(f.is_primary),
          sort_order: f.sort_order ?? 0,
          download_url: f.download_url ?? null,
          preview_url: f.preview_url ?? null,
        }));
        setExpandedRepFiles((prev) => ({ ...prev, [repId]: files }));
      } catch (err) {
        console.error('Failed to load representation files:', err);
      } finally {
        setLoadingRepFiles((prev) => ({ ...prev, [repId]: false }));
      }
    },
    [expandedRepFiles],
  );

  useEffect(() => {
    void fetchDetail();
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
          res.data.items.filter((item) => item.id !== detail.id).slice(0, 4),
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

  // ── Related by object_number (cross-source) ───────────────────
  const [objNumberRelated, setObjNumberRelated] = useState<UnifiedResourceSummary[]>([]);
  const [objNumberLoading, setObjNumberLoading] = useState(false);

  useEffect(() => {
    const loadObjNumberRelated = async () => {
      if (!detail) {
        setObjNumberRelated([]);
        return;
      }
      // Extract object_number from source_record profile fields
      const record = detail.source_record as Record<string, unknown> | null;
      const profile = (record?.metadata as Record<string, unknown> | null)
        ?? (record?.profile as Record<string, unknown> | null);
      const on = profile?.object_number as string | undefined;
      if (!on) {
        setObjNumberRelated([]);
        return;
      }
      setObjNumberLoading(true);
      try {
        const res = await axios.get<PaginatedUnifiedResourceList>('/api/platform/related', {
          params: {
            object_number: on,
            exclude_source: detail.source_system,
            exclude_id: detail.source_id,
            limit: 6,
          },
        });
        setObjNumberRelated(res.data.items);
      } catch {
        setObjNumberRelated([]);
      } finally {
        setObjNumberLoading(false);
      }
    };
    void loadObjNumberRelated();
  }, [detail]);

  const sourceRecord = detail?.source_record ?? null;
  const sourceRecordAny = sourceRecord as Record<string, unknown> | null;
  const assetRecord = isAssetDetailRecord(sourceRecord) ? sourceRecord : null;
  const threeDRecord = isThreeDDetailRecord(sourceRecord) ? sourceRecord : null;
  const threeDObjectRecord = isThreeDDigitalObjectDetailRecord(sourceRecord)
    ? sourceRecord
    : null;
  const defaultThreeDRecord = threeDRecord ?? threeDObjectRecord?.default_preview ?? null;

  const repOptions = useMemo(() => {
    if (!threeDObjectRecord?.representations || threeDObjectRecord.representations.length <= 1)
      return null;
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

  const activeViewer = repOptions
    ? selectedRepViewer ?? defaultThreeDRecord?.viewer ?? null
    : defaultThreeDRecord?.viewer ?? null;

  useEffect(() => {
    if (threeDObjectRecord && repOptions && selectedRepId === null) {
      setSelectedRepId(
        threeDObjectRecord.default_preview_representation_id ??
          threeDObjectRecord.representations[0]?.id ??
          null,
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
  const isVideo =
    looksLikeVideo(sourceRecord) || detail?.resource_type === 'video_cultural_object';
  const canShowVideoPreview = Boolean(isVideo && previewEnabled && manifestUrl);

  const lifecycleItems = useMemo(() => assetRecord?.lifecycle || [], [assetRecord]);
  const derivativeRecords = assetRecord?.structure.derivatives || [];
  const threeDTechnicalMetadata = useMemo(
    () => defaultThreeDRecord?.technical_metadata || {},
    [defaultThreeDRecord],
  );
  const displayFilename =
    assetRecord?.file.filename || defaultThreeDRecord?.file.filename || detail?.title || '-';
  const summaryText = sourceRecord?.structure?.summary || '当前资源已接入统一平台目录。';

  const dimensionLabel = detail
    ? SOURCE_DIMENSION_LABEL[detail.source_system] || detail.source_system
    : '';

  const handleBackToDimension = useCallback(() => {
    if (detail) persistTabHint(detail.source_system);
    onBack();
  }, [detail, onBack]);

  const productionEvents = useMemo(() => {
    const records = threeDRecord?.production_records ?? threeDObjectRecord?.default_preview?.production_records ?? [];
    return [...records].sort((a, b) =>
      (b.occurred_at || '').localeCompare(a.occurred_at || ''),
    );
  }, [threeDRecord, threeDObjectRecord]);

  // 主操作：根据资源类型动态决定
  const primaryAction = useMemo(() => {
    if (canShowThreeDPreview) {
      return { label: '查看 3D 模型', icon: <BlockOutlined />, onClick: scrollToHero, disabled: false };
    }
    if (canShowVideoPreview) {
      return {
        label: '播放视频',
        icon: <PlayCircleOutlined />,
        onClick: scrollToHero,
        disabled: false,
      };
    }
    if (canShowImagePreview && manifestUrl) {
      return {
        label: '打开 Mirador 预览',
        icon: <EyeOutlined />,
        onClick: () => onPreview?.(manifestUrl),
        disabled: false,
      };
    }
    return {
      label: '暂不支持预览',
      icon: <EyeOutlined />,
      onClick: () => undefined,
      disabled: true,
    };
  }, [canShowThreeDPreview, canShowVideoPreview, canShowImagePreview, manifestUrl, onPreview]);

  const primaryDownloadUrl =
    assetRecord?.outputs.download_url || defaultThreeDRecord?.outputs.download_url;

  const moreMenuItems: MenuProps['items'] = useMemo(() => {
    const items: NonNullable<MenuProps['items']> = [];
    items.push({
      key: 'manifest',
      label: '查看 Manifest',
      icon: <LinkOutlined />,
      disabled: !manifestUrl,
      onClick: () =>
        manifestUrl && window.open(manifestUrl, '_blank', 'noopener,noreferrer'),
    });
    if (assetRecord?.outputs.download_bag_url) {
      items.push({
        key: 'bagit',
        label: '下载 BagIt',
        icon: <DownloadOutlined />,
        onClick: () => {
          if (assetRecord?.outputs.download_bag_url) {
            window.location.href = assetRecord.outputs.download_bag_url;
          }
        },
      });
    }
    items.push({
      key: 'source-detail',
      label: '查看源详情',
      icon: <LinkOutlined />,
      disabled: !sourceRecord,
      onClick: () => {
        if (!sourceRecord) return;
        if (assetRecord && onOpenSourceDetail) {
          onOpenSourceDetail(assetRecord.id);
          return;
        }
        const detailData = threeDRecord ?? threeDObjectRecord?.default_preview ?? null;
        if (detailData) {
          setSourceDetailData(detailData);
          setSourceDetailDrawerOpen(true);
        }
      },
    });
    return items;
  }, [
    assetRecord,
    manifestUrl,
    onOpenSourceDetail,
    sourceRecord,
    threeDObjectRecord,
    threeDRecord,
  ]);

  if (loading) return <Spin tip="正在加载统一资源详情..." />;

  if (error) {
    return (
      <Card>
        <Alert type="error" message="加载失败" description={error} />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
            返回目录
          </Button>
        </div>
      </Card>
    );
  }

  if (!detail) {
    return (
      <Card>
        <Alert type="warning" message="暂无统一资源数据" />
        <div style={{ marginTop: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
            返回目录
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div
      className="unified-resource-detail-page"
      style={{ maxWidth: 1240, margin: '0 auto', paddingBottom: 32 }}
    >
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
          {
            title: dimensionLabel ? (
              <Tooltip title={`返回${dimensionLabel}资源列表`}>
                <a onClick={handleBackToDimension} style={{ cursor: 'pointer' }}>
                  {dimensionLabel}
                </a>
              </Tooltip>
            ) : (
              ''
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

      <div className="unified-resource-hero">
        <Card bordered={false} style={{ background: '#f5f4fb' }} bodyStyle={{ padding: 20 }}>
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
              borderRadius: 8,
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
                width: 64,
                height: 64,
                borderRadius: 10,
                overflow: 'hidden',
                background: '#fff',
                border: '1px solid #e8e8e8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {canShowThreeDPreview ? (
                <BlockOutlined style={{ fontSize: 22, color: '#52c41a' }} />
              ) : canShowImagePreview ? (
                <img
                  src={previewImageUrl}
                  alt={`${detail.title} 缩略图`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <PictureOutlined style={{ fontSize: 22, color: '#b4b9c0' }} />
              )}
            </div>
            <Space direction="vertical" size={0} style={{ minWidth: 0, flex: 1 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                资源主文件
              </Text>
              <Text strong ellipsis={{ tooltip: displayFilename }} style={{ fontSize: 13 }}>
                {displayFilename}
              </Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                统一 ID：{detail.id}
              </Text>
            </Space>
          </div>
        </Card>

        <Card bordered={false} bodyStyle={{ padding: 24 }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 标题 */}
            <Space direction="vertical" size={4}>
              <Title level={3} style={{ margin: 0 }}>
                {detail.title}
              </Title>
              <Text type="secondary">{summaryText}</Text>
            </Space>

            {/* 状态徽标条（独立一行） */}
            <Space wrap size={[6, 6]}>
              <Tag color={statusColorMap[detail.status] || 'default'}>
                {getStatusLabel(detail.status)}
              </Tag>
              <Tag color={previewEnabled ? 'green' : 'default'}>
                {previewEnabled ? '可预览' : '仅下载'}
              </Tag>
              {detail.profile_label && <Tag>{detail.profile_label}</Tag>}
              {assetRecord?.status_info.message && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  · {assetRecord.status_info.message}
                </Text>
              )}
            </Space>

            {/* 元数据双列 */}
            <Descriptions
              column={{ xs: 1, sm: 1, md: 2 }}
              size="small"
              labelStyle={{ width: 84, color: '#8c8c8c' }}
            >
              <Descriptions.Item label="统一 ID">
                <Paragraph copyable style={{ marginBottom: 0, fontSize: 12 }}>
                  {detail.id}
                </Paragraph>
              </Descriptions.Item>
              <Descriptions.Item label="来源 ID">{detail.source_id}</Descriptions.Item>
              <Descriptions.Item label="来源">{detail.source_label}</Descriptions.Item>
              <Descriptions.Item label="分类">
                {getResourceTypeLabel(detail.resource_type)}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">{detail.updated_at}</Descriptions.Item>
              {isVideo && (
                <>
                  <Descriptions.Item label="时长">
                    {formatDuration(sourceRecordAny?.duration_seconds as number | null)}
                  </Descriptions.Item>
                  <Descriptions.Item label="尺寸">
                    {sourceRecordAny?.width != null
                      ? `${sourceRecordAny.width} x ${sourceRecordAny.height}`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="格式">
                    {(sourceRecordAny?.mime_type as string) || '-'}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>

            <Divider style={{ margin: '4px 0' }} />

            {/* 操作分层：1 主操作 + 2 次操作 + 1 更多 Dropdown */}
            <Space wrap size={8}>
              <Button
                type="primary"
                size="middle"
                icon={primaryAction.icon}
                disabled={primaryAction.disabled}
                onClick={primaryAction.onClick}
              >
                {primaryAction.label}
              </Button>
              <Button
                icon={<ShoppingCartOutlined />}
                onClick={() => detail && onAddToApplication?.(detail)}
              >
                加入申请车
              </Button>
              <Button
                icon={<DownloadOutlined />}
                disabled={!primaryDownloadUrl}
                onClick={() => {
                  if (primaryDownloadUrl) window.location.href = primaryDownloadUrl;
                }}
              >
                {defaultThreeDRecord ? '下载资源包' : '下载原文件'}
              </Button>
              <Dropdown menu={{ items: moreMenuItems }} trigger={['click']}>
                <Button icon={<MoreOutlined />}>更多操作</Button>
              </Dropdown>
            </Space>
          </Space>
        </Card>

        {renderRightsPanel(detail.rights_display)}
      </div>

      {/* ── P1: 元数据分组展示（可折叠 Collapse） ── */}
      {/* 提取 management 字段：从 metadata_layers 中获取 */}
      {(() => {
        const metadataLayers = assetRecord?.metadata_layers ?? threeDRecord?.metadata_layers ?? null;
        const managementFields = metadataLayers?.management as Record<string, unknown> | undefined;
        const technicalMeta = metadataLayers?.technical as Record<string, unknown> | undefined;
        const profileSection = metadataLayers?.profile;
        const profileFields = profileSection?.fields as Record<string, unknown> | undefined;

        const managementRows = managementFields
          ? Object.entries(managementFields).filter(
              ([, v]) => v !== null && v !== undefined && v !== '',
            )
          : [];

        const technicalRows = technicalMeta
          ? Object.entries(technicalMeta).filter(
              ([, v]) => v !== null && v !== undefined && v !== '',
            )
          : [];

        const profileRows = profileFields
          ? Object.entries(profileFields).filter(
              ([, v]) => v !== null && v !== undefined && v !== '',
            )
          : [];

        const hasExtra =
          managementRows.length > 0 ||
          technicalRows.length > 0 ||
          profileRows.length > 0 ||
          detail?.format ||
          detail?.resolution;

        if (!hasExtra) return null;

        const renderFieldValue = (value: unknown): React.ReactNode => {
          if (value === null || value === undefined || value === '') return '-';
          if (typeof value === 'boolean') return value ? '是' : '否';
          if (typeof value === 'object') {
            try { return JSON.stringify(value); } catch { return '-'; }
          }
          return String(value);
        };

        const fieldStyle: React.CSSProperties = {
          display: 'flex',
          justifyContent: 'space-between',
          padding: '4px 0',
          borderBottom: '1px solid #f0f0f0',
          fontSize: 13,
        };
        const labelStyle: React.CSSProperties = { color: '#8c8c8c', flexShrink: 0, marginRight: 12 };
        const valueStyle: React.CSSProperties = { textAlign: 'right', wordBreak: 'break-all' };

        return (
          <Card bordered={false} style={{ marginTop: 16, marginBottom: 16 }}>
            <Collapse
              defaultActiveKey={['core']}
              size="small"
              items={[
                {
                  key: 'core',
                  label: '核心元数据 (Core)',
                  children: (
                    <div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>标题</span>
                        <span style={valueStyle}>{detail?.title || '-'}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>资源类型</span>
                        <span style={valueStyle}>{getResourceTypeLabel(detail?.resource_type)}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>来源系统</span>
                        <span style={valueStyle}>{detail?.source_label || detail?.source_system || '-'}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>来源 ID</span>
                        <span style={valueStyle}>{detail?.source_id || '-'}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>统一 ID</span>
                        <span style={valueStyle}>{detail?.id || '-'}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>状态</span>
                        <span style={valueStyle}>{getStatusLabel(detail?.status)}</span>
                      </div>
                      <div style={fieldStyle}>
                        <span style={labelStyle}>Profile</span>
                        <span style={valueStyle}>{detail?.profile_label || detail?.profile_key || '-'}</span>
                      </div>
                      <div style={{ ...fieldStyle, borderBottom: 'none' }}>
                        <span style={labelStyle}>更新时间</span>
                        <span style={valueStyle}>{detail?.updated_at || '-'}</span>
                      </div>
                    </div>
                  ),
                },
                ...(managementRows.length > 0
                  ? [
                      {
                        key: 'management',
                        label: `管理元数据 (Management) · ${managementRows.length} 项`,
                        children: (
                          <div>
                            {managementRows.map(([key, value]) => (
                              <div key={key} style={fieldStyle}>
                                <span style={labelStyle}>{getFieldLabel(key)}</span>
                                <span style={valueStyle}>{renderFieldValue(value)}</span>
                              </div>
                            ))}
                          </div>
                        ),
                      },
                    ]
                  : []),
                ...(technicalRows.length > 0 || detail?.format || detail?.resolution
                  ? [
                      {
                        key: 'technical',
                        label: '技术元数据 (Technical)',
                        children: (
                          <div>
                            {detail?.format && (
                              <div style={fieldStyle}>
                                <span style={labelStyle}>格式</span>
                                <span style={valueStyle}>{detail.format}</span>
                              </div>
                            )}
                            {detail?.resolution && (
                              <div style={fieldStyle}>
                                <span style={labelStyle}>分辨率</span>
                                <span style={valueStyle}>{detail.resolution}</span>
                              </div>
                            )}
                            {(() => {
                              const fileSize = assetRecord?.file?.file_size ?? defaultThreeDRecord?.file?.file_size ?? null;
                              if (!fileSize) return null;
                              return (
                                <div style={fieldStyle}>
                                  <span style={labelStyle}>文件大小</span>
                                  <span style={valueStyle}>{formatBytes(fileSize)}</span>
                                </div>
                              );
                            })()}
                            {technicalRows.map(([key, value]) => {
                              const isLast = key === technicalRows[technicalRows.length - 1]?.[0];
                              return (
                                <div
                                  key={key}
                                  style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    padding: '4px 0',
                                    borderBottom: isLast ? 'none' : '1px solid #f0f0f0',
                                    fontSize: 13,
                                  }}
                                >
                                  <span style={labelStyle}>{getFieldLabel(key)}</span>
                                  <span style={valueStyle}>{renderFieldValue(value)}</span>
                                </div>
                              );
                            })}
                          </div>
                        ),
                      },
                    ]
                  : []),
                ...(profileRows.length > 0
                  ? [
                      {
                        key: 'profile',
                        label: `Profile 字段 · ${profileSection?.label || profileSection?.key || '自定义'} (${profileRows.length} 项)`,
                        children: (
                          <div>
                            {profileRows.map(([key, value]) => {
                              const isLast = key === profileRows[profileRows.length - 1]?.[0];
                              return (
                                <div
                                  key={key}
                                  style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    padding: '4px 0',
                                    borderBottom: isLast ? 'none' : '1px solid #f0f0f0',
                                    fontSize: 13,
                                  }}
                                >
                                  <span style={labelStyle}>{getFieldLabel(key)}</span>
                                  <span style={valueStyle}>{renderFieldValue(value)}</span>
                                </div>
                              );
                            })}
                          </div>
                        ),
                      },
                    ]
                  : []),
              ]}
            />
          </Card>
        );
      })()}

      {sourceRecord && (
        <Row gutter={[16, 16]} data-testid="unified-resource-detail">
          {/* Anchor 锚点（仅大屏显示） */}
          <Col xs={0} xl={4}>
            <div style={{ position: 'sticky', top: 80 }}>
              <Anchor
                affix={false}
                offsetTop={80}
                items={[
                  { key: 'structure', href: '#section-structure', title: '结构与文件' },
                  { key: 'metadata', href: '#section-metadata', title: '技术元数据' },
                  { key: 'lifecycle', href: '#section-lifecycle', title: '生命周期' },
                  { key: 'related', href: '#section-related', title: '相关推荐' },
                ]}
              />
            </div>
          </Col>

          <Col xs={24} xl={20}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* 段落 1：结构与文件 */}
              <Card id="section-structure" bordered={false}>
                <SectionTitle
                  title="结构与文件"
                  subtitle="统一详情只展示平台层摘要，源详情保留完整结构信息。"
                />
                <Alert
                  type="info"
                  showIcon
                  message={sourceRecord.structure?.summary || '暂无结构说明'}
                  style={{ marginBottom: 16 }}
                />

                {assetRecord ? (
                  <>
                    <Descriptions
                      bordered
                      column={{ xs: 1, md: 2 }}
                      size="small"
                      style={{ marginBottom: 16 }}
                    >
                      <Descriptions.Item label="主文件">
                        {assetRecord.structure.primary_file.filename}
                      </Descriptions.Item>
                      <Descriptions.Item label="原始文件">
                        {assetRecord.structure.original_file.filename}
                      </Descriptions.Item>
                      <Descriptions.Item label="衍生文件数">
                        {derivativeRecords.length}
                      </Descriptions.Item>
                    </Descriptions>
                    {derivativeRecords.length > 0 ? (
                      <List
                        bordered
                        dataSource={derivativeRecords}
                        renderItem={(item: AssetDetailFileRecord) => (
                          <List.Item>
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <Text strong>{item.role_label || item.role || '-'}</Text>
                              <Space size="large" wrap>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  文件：{item.filename || '-'}
                                </Text>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  MIME：{item.mime_type || '-'}
                                </Text>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  大小：{formatBytes(item.file_size)}
                                </Text>
                              </Space>
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
                    renderItem={(item) => {
                      const isExpanded = !!expandedRepFiles[item.id];
                      const isLoading = loadingRepFiles[item.id];
                      const files = expandedRepFiles[item.id] || [];
                      return (
                        <List.Item>
                          <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Space wrap>
                              <Text strong>{item.representation_label}</Text>
                              <Tag>{item.representation_type}</Tag>
                              <Tag>{item.version_label}</Tag>
                              {item.id ===
                              threeDObjectRecord.default_preview_representation_id ? (
                                <Tag color="green">默认预览</Tag>
                              ) : null}
                              <Tag color={item.preview_enabled ? 'green' : 'default'}>
                                {item.preview_enabled ? '可预览' : '不可预览'}
                              </Tag>
                            </Space>
                            <Space wrap size={[12, 4]}>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {item.title}
                              </Text>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                · 文件：{item.file_count} 个
                              </Text>
                              {(item.file_groups || []).map((group) => (
                                <Tag key={`${item.id}-${group.role}`} style={{ margin: 0 }}>
                                  {group.role_label} {group.file_count}
                                </Tag>
                              ))}
                            </Space>
                            <Space wrap>
                              <Button
                                size="small"
                                icon={isExpanded ? <DownOutlined /> : <RightOutlined />}
                                onClick={() => void loadRepFiles(item.id, item.detail_url)}
                                loading={isLoading}
                              >
                                {isExpanded ? '收起文件列表' : '查看文件列表'}
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
                            {isExpanded && files.length > 0 && (
                              <Collapse
                                style={{ marginTop: 8, background: '#fafafa' }}
                                defaultActiveKey={['files']}
                                items={[
                                  {
                                    key: 'files',
                                    label: `文件列表 (${files.length} 个文件)`,
                                    children: (
                                      <List
                                        size="small"
                                        dataSource={files}
                                        renderItem={(file: ThreeDFileRecord) => (
                                          <List.Item
                                            actions={[
                                              <Button
                                                key="download"
                                                type="link"
                                                size="small"
                                                icon={<DownloadOutlined />}
                                                onClick={() => {
                                                  const downloadUrl =
                                                    file.download_url ||
                                                    `/api/three-d/resources/${item.id}/files/${file.id}`;
                                                  window.location.href = downloadUrl;
                                                }}
                                              >
                                                下载
                                              </Button>,
                                            ]}
                                          >
                                            <Space
                                              direction="vertical"
                                              size={0}
                                              style={{ width: '100%' }}
                                            >
                                              <Space>
                                                <FileOutlined style={{ color: '#1890ff' }} />
                                                <Text strong>{file.filename}</Text>
                                                {file.is_primary && (
                                                  <Tag color="green">主文件</Tag>
                                                )}
                                              </Space>
                                              <Space size="large" wrap>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                  类型：{file.role_label || file.role}
                                                </Text>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                  MIME：{file.mime_type || '-'}
                                                </Text>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                  大小：{formatBytes(file.file_size)}
                                                </Text>
                                              </Space>
                                            </Space>
                                          </List.Item>
                                        )}
                                      />
                                    ),
                                  },
                                ]}
                              />
                            )}
                          </Space>
                        </List.Item>
                      );
                    }}
                  />
                ) : isVideo ? (
                  <Descriptions bordered column={{ xs: 1, md: 2 }} size="small">
                    <Descriptions.Item label="主文件">
                      {(sourceRecordAny?.filename as string) || detail?.title || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="文件大小">
                      {formatBytes(sourceRecordAny?.file_size as number)}
                    </Descriptions.Item>
                    <Descriptions.Item label="播放地址" span={2}>
                      {manifestUrl ? (
                        <Paragraph copyable style={{ marginBottom: 0 }}>
                          {manifestUrl}
                        </Paragraph>
                      ) : (
                        '-'
                      )}
                    </Descriptions.Item>
                    <Descriptions.Item label="可申请状态">
                      <Tag color={previewEnabled ? 'green' : 'default'}>
                        {previewEnabled ? '可预览、可申请' : '可申请'}
                      </Tag>
                    </Descriptions.Item>
                  </Descriptions>
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
                          <Space size="large" wrap>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              文件：{item.filename || '-'}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              MIME：{item.mime_type || '-'}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              大小：{formatBytes(item.file_size)}
                            </Text>
                          </Space>
                        </Space>
                      </List.Item>
                    )}
                  />
                )}
              </Card>

              {/* 段落 2：技术元数据 */}
              <Card id="section-metadata" bordered={false}>
                <SectionTitle title="技术元数据" subtitle="保留源系统提供的核心技术字段。" />
                {assetRecord ? (
                  <Descriptions bordered column={{ xs: 1, md: 2 }} size="small">
                    <Descriptions.Item label="宽度">{technicalMetadata?.width ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="高度">{technicalMetadata?.height ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="入库方式">
                      {technicalMetadata?.ingest_method ?? '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="转换方式">
                      {technicalMetadata?.conversion_method ?? '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="SHA256" span={2}>
                      {technicalMetadata?.fixity_sha256 ? (
                        <Paragraph copyable code style={{ marginBottom: 0 }}>
                          {technicalMetadata.fixity_sha256}
                        </Paragraph>
                      ) : (
                        '-'
                      )}
                    </Descriptions.Item>
                    <Descriptions.Item label="原始文件路径" span={2}>
                      {technicalMetadata?.original_file_path ?? '-'}
                    </Descriptions.Item>
                  </Descriptions>
                ) : isVideo ? (
                  <Descriptions bordered column={{ xs: 1, md: 2 }} size="small">
                    <Descriptions.Item label="文件名">{detail?.title || '-'}</Descriptions.Item>
                    <Descriptions.Item label="MIME 类型">
                      {(sourceRecordAny?.mime_type as string) || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="文件大小">
                      {formatBytes(sourceRecordAny?.file_size as number)}
                    </Descriptions.Item>
                    <Descriptions.Item label="时长">
                      {formatDuration(sourceRecordAny?.duration_seconds as number | null)}
                    </Descriptions.Item>
                    <Descriptions.Item label="尺寸">
                      {sourceRecordAny?.width != null
                        ? `${sourceRecordAny.width} x ${sourceRecordAny.height}`
                        : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="版权/授权">
                      {(sourceRecordAny?.rights_label as string) ||
                        (sourceRecordAny?.license_label as string) ||
                        '待补充'}
                    </Descriptions.Item>
                  </Descriptions>
                ) : (
                  <MetadataTable data={threeDTechnicalMetadata as Record<string, unknown>} />
                )}
              </Card>

              {/* 段落 3：生命周期 Timeline */}
              <Card id="section-lifecycle" bordered={false}>
                <SectionTitle
                  title="生命周期"
                  subtitle="按源对象的处理轨迹/生产事件，按时间倒序展示。"
                />
                {assetRecord && lifecycleItems.length > 0 ? (
                  <Timeline
                    mode="left"
                    items={lifecycleItems.map((item: LifecycleEntry, idx) => ({
                      color: statusColorMap[item.status] || 'gray',
                      label: item.timestamp || `阶段 ${idx + 1}`,
                      children: (
                        <Space direction="vertical" size={2}>
                          <Space wrap>
                            <Text strong>{item.label}</Text>
                            <Tag color={statusColorMap[item.status] || 'default'}>
                              {item.status_label}
                            </Tag>
                          </Space>
                          <Text type="secondary">{item.description}</Text>
                          {item.evidence && (
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              佐证：{item.evidence}
                            </Text>
                          )}
                        </Space>
                      ),
                    }))}
                  />
                ) : productionEvents.length > 0 ? (
                  <Timeline
                    mode="left"
                    items={productionEvents.map((record) => ({
                      color: statusColorMap[record.status] || 'gray',
                      label: record.occurred_at,
                      children: (
                        <Space direction="vertical" size={2}>
                          <Space wrap>
                            <Text strong>{record.event_type}</Text>
                            <Tag color={statusColorMap[record.status] || 'default'}>
                              {record.stage}
                            </Tag>
                            {record.actor && (
                              <Text type="secondary">· {record.actor}</Text>
                            )}
                          </Space>
                          <Text type="secondary">
                            {record.description || record.evidence || '-'}
                          </Text>
                        </Space>
                      ),
                    }))}
                  />
                ) : (
                  <Alert
                    type="info"
                    showIcon
                    message="暂无生命周期/生产事件记录"
                    description={
                      isVideo
                        ? '视频资源暂未关联生命周期事件。'
                        : '当前对象暂无可展示的生产链事件。'
                    }
                  />
                )}
              </Card>

              {/* 段落 4：相关推荐（附匹配理由） */}
              <Card id="section-related" bordered={false}>
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
                                <BlockOutlined style={{ fontSize: 36, color: '#bfbfbf' }} />
                              ) : (
                                <PictureOutlined style={{ fontSize: 36, color: '#d9d9d9' }} />
                              )}
                            </div>
                          }
                        >
                          <Card.Meta
                            title={
                              <Text
                                ellipsis={{ tooltip: item.title }}
                                strong
                                style={{ fontSize: 13 }}
                              >
                                {item.title || '(无标题)'}
                              </Text>
                            }
                            description={
                              <Space direction="vertical" size={2}>
                                <Tag
                                  color={item.preview_enabled ? 'green' : 'default'}
                                  style={{ fontSize: 11 }}
                                >
                                  {item.preview_enabled ? '可预览' : '仅下载'}
                                </Tag>
                                <Text type="secondary" style={{ fontSize: 11 }}>
                                  匹配：同来源 · 同类型
                                </Text>
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

              {/* 段落 5：同一文物号的其他资源 */}
              {objNumberRelated.length > 0 && (
                <Card id="section-obj-related" bordered={false}>
                  <SectionTitle
                    title="同一文物号的其他资源"
                    subtitle={`${objNumberRelated.length} 件跨来源资源。`}
                  />
                  {objNumberLoading ? (
                    <Spin tip="正在加载..." />
                  ) : (
                    <Row gutter={[16, 16]}>
                      {objNumberRelated.map((item) => (
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
                                  <BlockOutlined style={{ fontSize: 36, color: '#bfbfbf' }} />
                                ) : (
                                  <FileOutlined style={{ fontSize: 36, color: '#bfbfbf' }} />
                                )}
                              </div>
                            }
                          >
                            <Card.Meta
                              title={
                                <Text strong style={{ fontSize: 13 }}>
                                  {item.title || '(无标题)'}
                                </Text>
                              }
                              description={
                                <Space direction="vertical" size={2}>
                                  <Tag>{item.source_label}</Tag>
                                  <Text type="secondary" style={{ fontSize: 11 }}>
                                    {item.resource_type} · 同一文物号
                                  </Text>
                                </Space>
                              }
                            />
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  )}
                </Card>
              )}

            </Space>
          </Col>
        </Row>
      )}

      {/* 三维源详情 Drawer（独立组件） */}
      <ThreeDSourceDetailDrawer
        open={sourceDetailDrawerOpen}
        data={sourceDetailData}
        onClose={() => {
          setSourceDetailDrawerOpen(false);
          setSourceDetailData(null);
        }}
      />
    </div>
  );
};

export default UnifiedResourceDetail;
