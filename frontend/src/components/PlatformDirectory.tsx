import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Image,
  Pagination,
  Row,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import {
  CloseCircleOutlined,
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

const SOURCE_TAB_MAP: Record<string, string> = {
  image_2d: '2d',
  three_d: '3d',
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

type SortKey = 'updated_desc' | 'updated_asc' | 'title_asc' | 'title_desc' | 'status';

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'updated_desc', label: '更新时间 ↓' },
  { value: 'updated_asc', label: '更新时间 ↑' },
  { value: 'title_asc', label: '标题 A-Z' },
  { value: 'title_desc', label: '标题 Z-A' },
  { value: 'status', label: '按状态分组' },
];

const FILTER_LABELS: Record<keyof AdvancedSearchParams, string> = {
  q: '关键词',
  field: '字段',
  field_value: '字段值',
  date_from: '起始日期',
  date_to: '结束日期',
  status: '状态',
  resource_type: '资源类型',
  profile_key: '模板',
  preview_enabled: '预览',
  source_system: '来源',
};

const FILTER_VALUE_TRANSFORM: Partial<Record<keyof AdvancedSearchParams, (value: string) => string>> = {
  status: (value) => STATUS_LABELS[value] || value,
  resource_type: (value) => RESOURCE_TYPE_LABELS[value] || value,
  preview_enabled: (value) => (value === 'true' ? '可预览' : '仅下载'),
};

interface PrimaryStatusBadge {
  text: string;
  color: string;
}

const buildPrimaryStatus = (record: UnifiedResourceSummary): PrimaryStatusBadge => {
  if (record.status === 'error') return { text: '异常', color: 'red' };
  if (record.status === 'processing') return { text: '处理中', color: 'blue' };
  if (record.preview_enabled) return { text: '可预览', color: 'green' };
  return { text: '可申请', color: 'default' };
};

const sortResources = (items: UnifiedResourceSummary[], sortKey: SortKey): UnifiedResourceSummary[] => {
  const arr = [...items];
  const STATUS_ORDER: Record<string, number> = { error: 0, processing: 1, ready: 2 };
  switch (sortKey) {
    case 'updated_desc':
      return arr.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
    case 'updated_asc':
      return arr.sort((a, b) => (a.updated_at || '').localeCompare(b.updated_at || ''));
    case 'title_asc':
      return arr.sort((a, b) => (a.title || '').localeCompare(b.title || '', 'zh-Hans'));
    case 'title_desc':
      return arr.sort((a, b) => (b.title || '').localeCompare(a.title || '', 'zh-Hans'));
    case 'status':
      return arr.sort((a, b) => {
        const av = STATUS_ORDER[a.status] ?? 99;
        const bv = STATUS_ORDER[b.status] ?? 99;
        if (av !== bv) return av - bv;
        return (b.updated_at || '').localeCompare(a.updated_at || '');
      });
    default:
      return arr;
  }
};

// 目录上下文持久化：进入详情页后返回时还原 Tab/页码/排序/筛选/视图
const DIRECTORY_STATE_KEY = 'platform_directory_state';
const DIRECTORY_TAB_HINT_KEY = 'platform_directory_active_tab';

interface PersistedDirectoryState {
  activeTab?: string;
  currentPage?: number;
  pageSize?: number;
  advancedParams?: AdvancedSearchParams;
  sortKey?: SortKey;
  viewMode?: ViewMode;
}

const loadPersistedDirectoryState = (): PersistedDirectoryState => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.sessionStorage.getItem(DIRECTORY_STATE_KEY);
    return raw ? (JSON.parse(raw) as PersistedDirectoryState) : {};
  } catch {
    return {};
  }
};

const PlatformDirectory: React.FC<PlatformDirectoryProps> = ({
  onPreview,
  onOpenUnifiedResourceDetail,
  onAddToApplication,
}) => {
  // 一次性读取持久化快照（在 useState lazy initializer 中还原）
  const persistedSnapshot = useMemo(loadPersistedDirectoryState, []);
  const isInitialMountRef = useRef(true);

  const [sources, setSources] = useState<UnifiedResourceSourceSummary[]>([]);
  const [resources, setResources] = useState<UnifiedResourceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>(() =>
    persistedSnapshot.viewMode === 'table' || persistedSnapshot.viewMode === 'card'
      ? persistedSnapshot.viewMode
      : 'card',
  );
  const [currentPage, setCurrentPage] = useState<number>(
    () => persistedSnapshot.currentPage ?? 1,
  );
  const [pageSize, setPageSize] = useState<number>(
    () => persistedSnapshot.pageSize ?? 20,
  );
  const [total, setTotal] = useState(0);
  const [advancedParams, setAdvancedParams] = useState<AdvancedSearchParams>(
    () => persistedSnapshot.advancedParams ?? {},
  );
  const [activeTab, setActiveTab] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      try {
        const hint = window.sessionStorage.getItem(DIRECTORY_TAB_HINT_KEY);
        if (hint && ['2d', '3d', 'video'].includes(hint)) {
          window.sessionStorage.removeItem(DIRECTORY_TAB_HINT_KEY);
          return hint;
        }
      } catch {
        /* ignore storage errors */
      }
    }
    if (
      persistedSnapshot.activeTab &&
      ['2d', '3d', 'video'].includes(persistedSnapshot.activeTab)
    ) {
      return persistedSnapshot.activeTab;
    }
    return '2d';
  });
  const [sortKey, setSortKey] = useState<SortKey>(
    () => persistedSnapshot.sortKey ?? 'updated_desc',
  );
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [statsBarCollapsed, setStatsBarCollapsed] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      try {
        return window.sessionStorage.getItem('platform_stats_bar_collapsed') === '1';
      } catch {
        /* ignore */
      }
    }
    return false;
  });

  const toggleStatsBarCollapsed = useCallback(() => {
    setStatsBarCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') {
        try {
          window.sessionStorage.setItem('platform_stats_bar_collapsed', next ? '1' : '0');
        } catch {
          /* ignore */
        }
      }
      return next;
    });
  }, []);

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
        setSelectedRowKeys([]);
      } finally {
        setLoading(false);
      }
    },
    [activeTab],
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const snapshot: PersistedDirectoryState = {
        activeTab,
        currentPage,
        pageSize,
        advancedParams,
        sortKey,
        viewMode,
      };
      window.sessionStorage.setItem(DIRECTORY_STATE_KEY, JSON.stringify(snapshot));
    } catch {
      /* ignore */
    }
  }, [activeTab, currentPage, pageSize, advancedParams, sortKey, viewMode]);

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

  const handleSwitchSource = useCallback((sourceSystem: string) => {
    const tabKey = SOURCE_TAB_MAP[sourceSystem];
    if (tabKey) setActiveTab(tabKey);
  }, []);

  const handleRemoveFilter = useCallback(
    (filterKey: keyof AdvancedSearchParams) => {
      const next: AdvancedSearchParams = { ...advancedParams };
      delete next[filterKey];
      setAdvancedParams(next);
      void fetchDirectory(next, 1, pageSize);
    },
    [advancedParams, fetchDirectory, pageSize],
  );

  const handleBatchAddToApplication = useCallback(() => {
    if (!onAddToApplication || selectedRowKeys.length === 0) return;
    const selectedSet = new Set(selectedRowKeys.map(String));
    resources
      .filter((r) => selectedSet.has(String(r.id)))
      .forEach((r) => onAddToApplication(r));
    setSelectedRowKeys([]);
  }, [onAddToApplication, resources, selectedRowKeys]);

  const activeSourceSystem = TAB_SOURCE_MAP[activeTab];
  const activeSourceLabel = SOURCE_LABELS[activeSourceSystem] || '资源';
  const previewResourceCount = useMemo(
    () => resources.filter((resource) => resource.preview_enabled).length,
    [resources],
  );
  const sortedResources = useMemo(
    () => sortResources(resources, sortKey),
    [resources, sortKey],
  );
  const activeFilterChips = useMemo(() => {
    return (Object.keys(advancedParams) as Array<keyof AdvancedSearchParams>)
      .filter((key) => {
        const value = advancedParams[key];
        return value !== undefined && value !== null && value !== '';
      })
      .map((key) => {
        const raw = String(advancedParams[key] ?? '');
        const transform = FILTER_VALUE_TRANSFORM[key];
        const display = transform ? transform(raw) : raw;
        return { key, label: FILTER_LABELS[key] || String(key), value: display };
      });
  }, [advancedParams]);

  // 初次挂载：使用还原的页码/筛选拉取；后续切换 Tab：重置到第一页
  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      void fetchDirectory(advancedParams, currentPage, pageSize);
      return;
    }
    void fetchDirectory(advancedParams, 1, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const columns = useMemo(
    () => [
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
        render: (value: string, record: UnifiedResourceSummary) => (
          <Paragraph copyable={{ text: record.id }} style={{ marginBottom: 0 }}>
            <Text strong>{value || '(无标题)'}</Text>
          </Paragraph>
        ),
      },
      {
        title: '来源 / 类型',
        key: 'source_type',
        ellipsis: true,
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
        width: 130,
        render: (_: unknown, record: UnifiedResourceSummary) => {
          const badge = buildPrimaryStatus(record);
          return (
            <Space direction="vertical" size={2}>
              <Tag color={badge.color} style={{ fontSize: 11, margin: 0 }}>
                {badge.text}
              </Tag>
              {record.profile_label && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {record.profile_label}
                </Text>
              )}
            </Space>
          );
        },
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
        width: 170,
        render: (_: unknown, record: UnifiedResourceSummary) => (
          <Space size={4}>
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
            <Tooltip title={record.preview_enabled ? '预览' : '该资源不支持预览'}>
              <Button
                data-testid={`platform-preview-${record.source_id}`}
                size="small"
                icon={<EyeOutlined />}
                disabled={!record.preview_enabled}
                onClick={() => onPreview(record)}
              />
            </Tooltip>
            <Tooltip title="加入申请车">
              <Button
                data-testid={`platform-apply-${record.source_id}`}
                size="small"
                icon={<ShoppingCartOutlined />}
                onClick={() => onAddToApplication?.(record)}
              />
            </Tooltip>
          </Space>
        ),
      },
    ],
    [onAddToApplication, onOpenUnifiedResourceDetail, onPreview],
  );

  const rowSelection = useMemo(
    () => ({
      selectedRowKeys,
      onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
    }),
    [selectedRowKeys],
  );

  return (
    <Row
      gutter={[16, 16]}
      data-testid="platform-directory"
      style={{ minHeight: 400, width: '100%', margin: 0 }}
    >
      <Col
        xs={24}
        xl={statsBarCollapsed ? 2 : 6}
        xxl={statsBarCollapsed ? 1 : 5}
        style={{ transition: 'all 0.2s ease' }}
      >
        <PlatformStatsBar
          sources={sources}
          totalResources={total}
          activeSourceSystem={activeSourceSystem}
          previewResourceCount={previewResourceCount}
          onSwitchSource={handleSwitchSource}
          collapsed={statsBarCollapsed}
          onToggleCollapsed={toggleStatsBarCollapsed}
        />
      </Col>

      <Col
        xs={24}
        xl={statsBarCollapsed ? 22 : 18}
        xxl={statsBarCollapsed ? 23 : 19}
        style={{ minWidth: 0, transition: 'all 0.2s ease' }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 12,
              flexWrap: 'wrap',
            }}
          >
            <Title level={4} style={{ margin: 0 }}>
              统一资源目录
              <Text type="secondary" style={{ fontSize: 13, fontWeight: 400, marginLeft: 8 }}>
                · {activeSourceLabel}
              </Text>
            </Title>
            <Space size={8}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                排序
              </Text>
              <Select
                size="small"
                style={{ minWidth: 140 }}
                value={sortKey}
                options={SORT_OPTIONS}
                onChange={(value) => setSortKey(value as SortKey)}
              />
            </Space>
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

          {activeFilterChips.length > 0 && (
            <Space
              wrap
              size={[6, 6]}
              style={{
                padding: '8px 12px',
                background: '#fafafa',
                border: '1px solid #f0f0f0',
                borderRadius: 6,
              }}
            >
              <Text type="secondary" style={{ fontSize: 12 }}>
                当前筛选：
              </Text>
              {activeFilterChips.map((chip) => (
                <Tag
                  key={chip.key}
                  closable
                  closeIcon={<CloseCircleOutlined />}
                  onClose={(e) => {
                    e.preventDefault();
                    handleRemoveFilter(chip.key);
                  }}
                  style={{ margin: 0 }}
                >
                  {chip.label}：{chip.value}
                </Tag>
              ))}
              <Button type="link" size="small" onClick={handleRefresh}>
                清除全部
              </Button>
            </Space>
          )}

          {viewMode === 'table' && selectedRowKeys.length > 0 && (
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                background: '#e6f4ff',
                border: '1px solid #91caff',
                borderRadius: 6,
              }}
            >
              <Text>已选 {selectedRowKeys.length} 项</Text>
              <Space>
                <Button size="small" onClick={() => setSelectedRowKeys([])}>
                  取消选择
                </Button>
                <Button
                  type="primary"
                  size="small"
                  icon={<ShoppingCartOutlined />}
                  onClick={handleBatchAddToApplication}
                >
                  批量加入申请车
                </Button>
              </Space>
            </div>
          )}

          {viewMode === 'card' ? (
            <>
              <Row gutter={[16, 16]}>
                {sortedResources.map((resource) => {
                  const badge = buildPrimaryStatus(resource);
                  return (
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
                              position: 'relative',
                            }}
                          >
                            <PlayCircleOutlined style={{ fontSize: 48, color: '#fa8c16' }} />
                            <Text style={{ color: 'rgba(255,255,255,0.65)', fontSize: 12 }}>
                              可播放视频
                            </Text>
                            <Tag
                              color="orange"
                              style={{
                                position: 'absolute',
                                left: 8,
                                bottom: 8,
                                margin: 0,
                                fontSize: 11,
                              }}
                            >
                              视频
                            </Tag>
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
                              position: 'relative',
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
                            {resource.preview_enabled && (
                              <Tag
                                color="green"
                                style={{
                                  position: 'absolute',
                                  right: 8,
                                  top: 8,
                                  margin: 0,
                                  fontSize: 11,
                                }}
                              >
                                可预览
                              </Tag>
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
                          <Space
                            align="center"
                            size={6}
                            style={{ width: '100%', justifyContent: 'space-between' }}
                          >
                            <Text
                              ellipsis={{ tooltip: resource.title || '无标题' }}
                              strong
                              style={{ fontSize: 13, flex: 1, minWidth: 0 }}
                            >
                              {resource.title || '(无标题)'}
                            </Text>
                            <Tag
                              color={badge.color}
                              style={{ fontSize: 11, margin: 0, flexShrink: 0 }}
                            >
                              {badge.text}
                            </Tag>
                          </Space>
                        }
                        description={
                          <Text
                            type="secondary"
                            style={{ fontSize: 11, display: 'block' }}
                            ellipsis={{ tooltip: true }}
                          >
                            {resource.source_label}
                            {resource.profile_label ? ` · ${resource.profile_label}` : ''}
                            {' · '}
                            {resource.updated_at}
                          </Text>
                        }
                      />
                    </Card>
                  </Col>
                  );
                })}
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
                rowSelection={rowSelection}
                loading={loading}
                dataSource={sortedResources}
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
