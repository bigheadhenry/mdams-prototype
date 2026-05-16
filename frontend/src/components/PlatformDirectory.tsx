import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Image,
  Pagination,
  Row,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import {
  EyeOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import AdvancedSearchPanel from './AdvancedSearchPanel';
import type { ViewMode } from './AdvancedSearchPanel';
import PlatformStatsBar from './PlatformStatsBar';
import ThreeDTurntablePreview from './ThreeDTurntablePreview';
import type {
  AdvancedSearchParams,
  PaginatedUnifiedResourceList,
  UnifiedResourceSourceSummary,
  UnifiedResourceSummary,
} from '../types/assets';

const { Paragraph, Text, Title } = Typography;

const STATUS_COLOR_MAP: Record<string, string> = {
  ready: 'green',
  processing: 'blue',
  error: 'red',
};

const SOURCE_COLORS: Record<string, string> = {
  image_2d: '#1677ff',
  three_d: '#52c41a',
  video: '#fa8c16',
};

interface PlatformDirectoryProps {
  onPreview: (resource: UnifiedResourceSummary) => void;
  onOpenAssetDetail?: (assetId: number) => void;
  onOpenUnifiedResourceDetail?: (sourceSystem: string, sourceId: string) => void;
  onAddToApplication?: (resource: UnifiedResourceSummary) => boolean;
}

const RESOURCE_TYPE_LABELS: Record<string, string> = {
  image_2d_cultural_object: '二维影像',
  three_d_digital_object: '三维数字对象',
  three_d_model: '三维模型',
  three_d_point_cloud: '点云',
  three_d_oblique_photo: '倾斜摄影',
  three_d_package: '三维包',
  video_cultural_object: '文博视频',
};

const TAB_SOURCE_MAP: Record<string, string> = {
  '2d': 'image_2d',
  '3d': 'three_d',
  video: 'video',
};

const SOURCE_LABELS: Record<string, string> = {
  image_2d: '二维资源',
  three_d: '三维数字对象',
  video: '视频资源',
};

const STATUS_LABELS: Record<string, string> = {
  ready: '可申请',
  processing: '处理中',
  error: '异常',
};

const PlatformDirectory: React.FC<PlatformDirectoryProps> = ({
  onPreview,
  onOpenUnifiedResourceDetail,
  onAddToApplication,
}) => {
  const [sources, setSources] = useState<UnifiedResourceSourceSummary[]>([]);
  const [resources, setResources] = useState<UnifiedResourceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('card');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [advancedParams, setAdvancedParams] = useState<AdvancedSearchParams>({});
  const [activeTab, setActiveTab] = useState<string>('2d');

  const fetchDirectory = useCallback(
    async (params: AdvancedSearchParams = {}, page = 1, size = 20) => {
      setLoading(true);
      try {
        const queryParams: Record<string, string | boolean | number> = {};
        if (params.q) queryParams.q = params.q;
        if (params.status) queryParams.status = params.status;
        if (params.preview_enabled) queryParams.preview_enabled = params.preview_enabled === 'true';
        if (params.resource_type) queryParams.resource_type = params.resource_type;
        if (params.profile_key) queryParams.profile_key = params.profile_key;
        queryParams.source_system = TAB_SOURCE_MAP[activeTab];
        if (params.field && params.field_value) {
          queryParams.q = queryParams.q
            ? `${String(queryParams.q)} ${params.field_value}`
            : params.field_value;
        }
        queryParams.skip = (page - 1) * size;
        queryParams.limit = size;

        const [sourcesRes, resourcesRes] = await Promise.all([
          axios.get<UnifiedResourceSourceSummary[]>('/api/platform/sources'),
          axios.get<PaginatedUnifiedResourceList>('/api/platform/resources', {
            params: queryParams,
          }),
        ]);
        setSources(sourcesRes.data);
        setResources(resourcesRes.data.items);
        setTotal(resourcesRes.data.total);
        setCurrentPage(resourcesRes.data.page);
        setPageSize(resourcesRes.data.size);
      } finally {
        setLoading(false);
      }
    },
    [activeTab],
  );

  useEffect(() => {
    void fetchDirectory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = useCallback(
    (params: AdvancedSearchParams) => {
      setAdvancedParams(params);
      void fetchDirectory(params, 1, pageSize);
    },
    [fetchDirectory, pageSize],
  );

  const handleRefresh = useCallback(() => {
    setAdvancedParams({});
    void fetchDirectory({}, 1, pageSize);
  }, [fetchDirectory, pageSize]);

  const handlePageChange = useCallback(
    (page: number, size: number) => {
      setPageSize(size);
      void fetchDirectory(advancedParams, page, size);
    },
    [fetchDirectory, advancedParams],
  );

  const handleTabChange = useCallback((tabKey: string) => {
    setActiveTab(tabKey);
  }, []);

  const activeSourceSystem = TAB_SOURCE_MAP[activeTab];
  const activeSourceLabel = SOURCE_LABELS[activeSourceSystem] || '资源';
  const previewResourceCount = useMemo(
    () => resources.filter((resource) => resource.preview_enabled).length,
    [resources],
  );

  // 标签页切换时重新加载数据（重置到第一页）
  useEffect(() => {
    void fetchDirectory(advancedParams, 1, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const columns = useMemo(
    () => [
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        width: 220,
        render: (value: string, record: UnifiedResourceSummary) => (
          <Paragraph copyable={{ text: record.id }} style={{ marginBottom: 0 }}>
            <Text strong>{value || '(无标题)'}</Text>
          </Paragraph>
        ),
      },
      {
        title: '来源 / 类型',
        key: 'source_type',
        width: 160,
        render: (_: unknown, record: UnifiedResourceSummary) => (
          <Space direction="vertical" size={0}>
            <Text style={{ fontSize: 12 }}>{record.source_label}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {RESOURCE_TYPE_LABELS[record.resource_type] || record.resource_type}
            </Text>
          </Space>
        ),
      },
      {
        title: '状态',
        key: 'status',
        width: 150,
        render: (_: unknown, record: UnifiedResourceSummary) => (
          <Space wrap size={[4, 2]}>
            <Tag
              color={record.preview_enabled ? 'green' : 'blue'}
              style={{ fontSize: 11, margin: 0 }}
            >
              {record.preview_enabled ? '可预览' : '可申请'}
            </Tag>
            <Tag
              color={STATUS_COLOR_MAP[record.status] || 'default'}
              style={{ fontSize: 11, margin: 0 }}
            >
              {STATUS_LABELS[record.status] || record.status}
            </Tag>
            {record.profile_label && (
              <Tag style={{ fontSize: 11, margin: 0 }}>{record.profile_label}</Tag>
            )}
          </Space>
        ),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        width: 150,
        render: (value: string) => (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {value}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'action',
        width: 190,
        render: (_: unknown, record: UnifiedResourceSummary) => (
          <Space size={4} wrap>
            <Button
              data-testid={`platform-preview-${record.source_id}`}
              size="small"
              icon={<EyeOutlined />}
              disabled={!record.preview_enabled}
              onClick={() => onPreview(record)}
            >
              预览
            </Button>
            <Button
              data-testid={`platform-unified-detail-${record.source_id}`}
              size="small"
              type="primary"
              icon={<LinkOutlined />}
              onClick={() =>
                onOpenUnifiedResourceDetail?.(record.source_system, record.source_id)
              }
            >
              详情
            </Button>
            <Button
              data-testid={`platform-apply-${record.source_id}`}
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={() => onAddToApplication?.(record)}
            >
              加入申请车
            </Button>
          </Space>
        ),
      },
    ],
    [onAddToApplication, onOpenUnifiedResourceDetail, onPreview],
  );

  return (
    <Row
      gutter={[16, 16]}
      data-testid="platform-directory"
      style={{ minHeight: 400, width: '100%', margin: 0 }}
    >
      <Col xs={24} xl={6} xxl={5}>
        <PlatformStatsBar
          sources={sources}
          totalResources={total}
          activeSourceSystem={activeSourceSystem}
          previewResourceCount={previewResourceCount}
        />
      </Col>

      <Col xs={24} xl={18} xxl={19} style={{ minWidth: 0 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Title level={4} style={{ margin: 0 }}>
              统一资源目录
            </Title>
            <Text type="secondary">
              {activeSourceLabel} · 共 {total} 条
            </Text>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={(key) => handleTabChange(key)}
            size="large"
            items={[
              { key: '2d', label: '二维' },
              { key: '3d', label: '三维' },
              { key: 'video', label: '视频' },
            ]}
          />

          <AdvancedSearchPanel
            viewMode={viewMode}
            sourceSystem={activeSourceSystem}
            onViewModeChange={setViewMode}
            onSearch={handleSearch}
            onRefresh={handleRefresh}
            loading={loading}
          />

          {viewMode === 'card' ? (
            <>
              <Row gutter={[16, 16]}>
                {resources.map((resource) => (
                  <Col key={resource.id} xxl={6} xl={8} lg={12} md={12} sm={24} xs={24}>
                    <Card
                      hoverable
                      size="small"
                      style={{ height: '100%' }}
                      cover={
                        resource.source_system === 'three_d' ? (
                          <ThreeDTurntablePreview
                            title={resource.title}
                            previewData={resource.preview_data}
                            fallbackUrl={resource.thumbnail_url}
                            height={150}
                          />
                        ) : resource.source_system === 'video' ? (
                          <div
                            style={{
                              height: 150,
                              background: 'linear-gradient(135deg, #18212f 0%, #223b46 100%)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexDirection: 'column',
                              gap: 8,
                            }}
                          >
                            <PlayCircleOutlined style={{ fontSize: 48, color: '#fa8c16' }} />
                            <Text style={{ color: 'rgba(255,255,255,0.65)', fontSize: 12 }}>
                              可播放视频
                            </Text>
                          </div>
                        ) : (
                          <div
                            style={{
                              height: 150,
                              background: '#fafafa',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              overflow: 'hidden',
                            }}
                          >
                            {resource.thumbnail_url ? (
                            <Image
                              src={resource.thumbnail_url}
                              alt={resource.title}
                              style={{
                                maxHeight: '100%',
                                maxWidth: '100%',
                                objectFit: 'cover',
                              }}
                              fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
                              preview={false}
                            />
                            ) : (
                            <PlayCircleOutlined
                              style={{ fontSize: 48, color: '#d9d9d9' }}
                            />
                            )}
                          </div>
                        )
                      }
                      actions={[
                        <Button
                          key="detail"
                          data-testid={`platform-unified-detail-${resource.source_id}`}
                          type="link"
                          size="small"
                          icon={<LinkOutlined />}
                          onClick={() =>
                            onOpenUnifiedResourceDetail?.(
                              resource.source_system,
                              resource.source_id,
                            )
                          }
                        >
                          详情
                        </Button>,
                        <Button
                          key="preview"
                          data-testid={`platform-preview-${resource.source_id}`}
                          type="link"
                          size="small"
                          icon={<EyeOutlined />}
                          disabled={!resource.preview_enabled}
                          onClick={() => onPreview(resource)}
                        >
                          预览
                        </Button>,
                        <Button
                          key="apply"
                          data-testid={`platform-apply-${resource.source_id}`}
                          type="link"
                          size="small"
                          icon={<ShoppingCartOutlined />}
                          onClick={() => onAddToApplication?.(resource)}
                        >
                          申请
                        </Button>,
                      ]}
                    >
                      <Card.Meta
                        title={
                          <Text
                            ellipsis={{ tooltip: resource.title || '无标题' }}
                            strong
                            style={{ fontSize: 13 }}
                          >
                            {resource.title || '(无标题)'}
                          </Text>
                        }
                        description={
                          <Space direction="vertical" size={4} style={{ width: '100%' }}>
                            <Space size={4} wrap>
                              <Tag
                                color={
                                  SOURCE_COLORS[resource.source_system] || 'default'
                                }
                                style={{ fontSize: 11, margin: 0 }}
                              >
                                {resource.source_label}
                              </Tag>
                              <Tag
                                color={resource.preview_enabled ? 'green' : 'default'}
                                style={{ fontSize: 11, margin: 0 }}
                              >
                                {resource.preview_enabled ? '可预览' : '可申请'}
                              </Tag>
                              <Tag
                                color={
                                  STATUS_COLOR_MAP[resource.status] || 'default'
                                }
                                style={{ fontSize: 11, margin: 0 }}
                              >
                                {STATUS_LABELS[resource.status] || resource.status}
                              </Tag>
                              {resource.profile_label && (
                                <Tag style={{ fontSize: 11, margin: 0 }}>
                                  {resource.profile_label}
                                </Tag>
                              )}
                            </Space>
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              {resource.updated_at}
                            </Text>
                          </Space>
                        }
                      />
                    </Card>
                  </Col>
                ))}
              </Row>
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Pagination
                  current={currentPage}
                  pageSize={pageSize}
                  total={total}
                  showSizeChanger
                  showQuickJumper
                  pageSizeOptions={['10', '20', '40', '80']}
                  showTotal={(t) => `共 ${t} 条`}
                  onChange={handlePageChange}
                  disabled={loading}
                />
              </div>
            </>
          ) : (
            <Card size="small">
              <Table
                rowKey="id"
                loading={loading}
                dataSource={resources}
                columns={columns}
                size="small"
                pagination={{
                  current: currentPage,
                  pageSize: pageSize,
                  total: total,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  pageSizeOptions: ['10', '20', '40', '80'],
                  showTotal: (t) => `共 ${t} 条`,
                  onChange: (page, size) => handlePageChange(page, size),
                }}
              />
            </Card>
          )}
        </Space>
      </Col>
    </Row>
  );
};

export default PlatformDirectory;
