import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Dropdown,
  Image,
  Input,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  EyeOutlined,
  FileTextOutlined,
  MoreOutlined,
  ReloadOutlined,
  SearchOutlined,
  SyncOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import type {
  ThreeDAssetSummary,
  ThreeDDetailResponse,
  ThreeDObjectGroup,
} from '../types/assets';
import ThreeDViewer from './ThreeDViewer';
import ThreeDTurntablePreview from './ThreeDTurntablePreview';

const { Paragraph, Text } = Typography;

/* ─── 标签常量 ─── */
const WEB_PREVIEW_STATUS_LABELS: Record<string, string> = {
  ready: '已就绪',
  pending: '准备中',
  disabled: '未启用',
};
const STORAGE_TIER_LABELS: Record<string, string> = {
  working: '工作区',
  delivery: '交付区',
  archive: '归档区',
};
const PRESERVATION_STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  preserved: '已保存',
  archived: '已归档',
};
const RECORD_STATUS_LABELS: Record<string, string> = {
  ready: '就绪',
  error: '异常',
  processing: '处理中',
};
const REPRESENTATION_TYPE_LABELS: Record<string, string> = {
  original_master: '原始保存级',
  web_display: 'Web 展示级',
  mobile_lightweight: '移动轻量级',
  research_detail: '高精度研究级',
  derivative: '其他派生',
};

/* ─── 小工具 ─── */
type RepresentationLike = Pick<ThreeDAssetSummary, 'version_label' | 'is_web_preview' | 'web_preview_status'>;

const getRepresentationType = (record: RepresentationLike) => {
  const v = (record.version_label || '').toLowerCase();
  if (v.includes('original') || v.includes('master')) return 'original_master';
  if (v.includes('mobile') || v.includes('light')) return 'mobile_lightweight';
  if (v.includes('detail') || v.includes('research') || v.includes('high')) return 'research_detail';
  if (v.includes('web') || (record.is_web_preview && record.web_preview_status === 'ready')) return 'web_display';
  return 'derivative';
};
const getRepresentationLabel = (r: RepresentationLike) => REPRESENTATION_TYPE_LABELS[getRepresentationType(r)] || getRepresentationType(r);
const getWebPreviewStatusLabel = (v?: string | null) => (!v ? '-' : WEB_PREVIEW_STATUS_LABELS[v] || v);
const getStorageTierLabel = (v?: string | null) => (!v ? '-' : STORAGE_TIER_LABELS[v] || v);
const getPreservationStatusLabel = (v?: string | null) => (!v ? '-' : PRESERVATION_STATUS_LABELS[v] || v);
const getRecordStatusLabel = (v?: string | null) => (!v ? '-' : RECORD_STATUS_LABELS[v] || v);
const getFileExtUpper = (f?: string | null) => (!f ? '?' : f.substring(f.lastIndexOf('.') + 1).toUpperCase().slice(0, 6));
const isImageMime = (m?: string | null) => Boolean(m && m.startsWith('image/'));

const getPreferredDetailVersion = (g: ThreeDObjectGroup) => g.webPreviewVersion ?? g.currentVersion ?? g.latestVersion;

/* ─── 筛选配置 ─── */
const PROFILE_FILTERS = [
  { value: 'model', label: '模型' },
  { value: 'point_cloud', label: '点云' },
  { value: 'oblique_photo', label: '倾斜摄影' },
  { value: 'package', label: '资源包' },
];
const STATUS_FILTERS = [
  { value: 'ready', label: '就绪' },
  { value: 'processing', label: '处理中' },
  { value: 'error', label: '异常' },
];
const STORAGE_TIER_FILTERS = [
  { value: 'working', label: '工作区' },
  { value: 'delivery', label: '交付区' },
  { value: 'archive', label: '归档区' },
];
const WEB_PREVIEW_FILTERS = [
  { value: 'ready', label: '已就绪' },
  { value: 'pending', label: '准备中' },
  { value: 'disabled', label: '未启用' },
];

/* ─── Props ─── */
interface ThreeDCatalogProps {
  groupedItems: ThreeDObjectGroup[];
  loading: boolean;
  onRefresh: () => void;
  onIngest?: () => void;
}

/* ─── 元数据表格(字段化) ─── */
interface MetadataRow {
  key: string;
  field: string;
  value: React.ReactNode;
}
const isRecord = (v: unknown): v is Record<string, unknown> => Boolean(v && typeof v === 'object' && !Array.isArray(v));

const renderMetadataValue = (value: unknown, depth: number = 0): React.ReactNode => {
  if (value === null || value === undefined || value === '') return '-';
  if (Array.isArray(value)) {
    if (!value.length) return '-';
    return (
      <Space wrap>
        {value.map((item, i) => (
          <Tag key={i}>{typeof item === 'object' ? JSON.stringify(item) : String(item)}</Tag>
        ))}
      </Space>
    );
  }
  if (isRecord(value)) {
    if (depth >= 2) return `${Object.keys(value).length} 个字段`;
    const rows: MetadataRow[] = Object.entries(value)
      .filter(([, v]) => v !== null && v !== undefined && v !== '')
      .map(([k, v]) => ({ key: k, field: k, value: renderMetadataValue(v, depth + 1) }));
    return (
      <Table size="small" pagination={false} rowKey="key" dataSource={rows}
        columns={[
          { title: '字段', dataIndex: 'field', key: 'field', width: 180 },
          { title: '值', dataIndex: 'value', key: 'value' },
        ]}
      />
    );
  }
  return String(value);
};

/* ═══════════════════════════ 组件 ═══════════════════════════ */
const ThreeDCatalog: React.FC<ThreeDCatalogProps> = ({ groupedItems, loading, onRefresh, onIngest }) => {
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<string | undefined>();
  const [filterProfile, setFilterProfile] = useState<string | undefined>();
  const [filterStorageTier, setFilterStorageTier] = useState<string | undefined>();
  const [filterWebPreview, setFilterWebPreview] = useState<string | undefined>();
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  /* 详情 Drawer */
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detail, setDetail] = useState<ThreeDDetailResponse | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  /* 分页 */
  const [pageSize, setPageSize] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);

  const filteredGroups = useMemo(() => {
    let result = groupedItems;
    if (searchText.trim()) {
      const q = searchText.trim().toLowerCase();
      result = result.filter(
        (g) =>
          g.label.toLowerCase().includes(q) ||
          (g.objectNumber || '').toLowerCase().includes(q) ||
          (g.objectName || '').toLowerCase().includes(q),
      );
    }
    if (filterStatus) result = result.filter((g) => g.versions.some((v) => v.status === filterStatus));
    if (filterProfile) result = result.filter((g) => g.profileLabel?.toLowerCase() === filterProfile);
    if (filterStorageTier) result = result.filter((g) => g.storageTier === filterStorageTier);
    if (filterWebPreview) result = result.filter((g) => g.webPreviewVersion?.web_preview_status === filterWebPreview);
    return result;
  }, [groupedItems, searchText, filterStatus, filterProfile, filterStorageTier, filterWebPreview]);

  const paginatedGroups = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredGroups.slice(start, start + pageSize);
  }, [filteredGroups, currentPage, pageSize]);

  /* 默认展开所有行 —— 数据变化时自动重置 */
  const [expandedRowKeys, setExpandedRowKeys] = useState<readonly React.Key[]>([]);
  const allGroupKeys = useMemo(() => paginatedGroups.map((g) => g.key), [paginatedGroups]);
  useEffect(() => {
    setExpandedRowKeys(allGroupKeys);
  }, [allGroupKeys]);

  /* ─── 详情 ─── */
  const openDetail = async (id: number) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setEditingField(null);
    try {
      const res = await axios.get<ThreeDDetailResponse>(`/api/three-d/resources/${id}`);
      setDetail(res.data);
    } catch {
      message.error('加载详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePatch = async (id: number, field: string, value: unknown) => {
    try {
      await axios.patch(`/api/three-d/resources/${id}`, { [field]: value });
      message.success('更新成功');
      onRefresh();
      const res = await axios.get<ThreeDDetailResponse>(`/api/three-d/resources/${id}`);
      setDetail(res.data);
    } catch {
      message.error('更新失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`/api/three-d/resources/${id}`);
      message.success('已删除');
      setDetailOpen(false);
      setDetail(null);
      onRefresh();
    } catch {
      message.error('删除失败，请重试');
    }
  };

  const handleRegenPreview = async (id: number) => {
    try {
      await axios.post(`/api/three-d/resources/${id}/regenerate-preview`);
      message.success('预览再生已触发');
      onRefresh();
      const res = await axios.get<ThreeDDetailResponse>(`/api/three-d/resources/${id}`);
      setDetail(res.data);
    } catch {
      message.error('预览再生失败');
    }
  };

  /* ─── 批量操作 ─── */
  const batchSetWebPreview = async (enabled: boolean) => {
    let failures = 0;
    for (const key of selectedRowKeys) {
      const group = groupedItems.find((g) => g.key === key);
      if (!group) continue;
      const preferred = getPreferredDetailVersion(group);
      if (!preferred) continue;
      try {
        await axios.patch(`/api/three-d/resources/${preferred.id}`, {
          is_web_preview: enabled,
          web_preview_status: enabled ? 'ready' : 'disabled',
        });
      } catch {
        failures++;
      }
    }
    if (failures > 0) {
      message.warning(`批量更新完成，但有 ${failures} 项失败`);
    } else {
      message.success('批量更新完成');
    }
    setSelectedRowKeys([]);
    onRefresh();
  };

  /* ─── 主表列 ─── */
  const groupColumns: ColumnsType<ThreeDObjectGroup> = [
    {
      title: '数字对象',
      key: 'label',
      sorter: (a, b) => a.label.localeCompare(b.label),
      render: (_, r) => (
        <Space direction="vertical" size={0}>
          <Text strong>{r.label}</Text>
          <Text type="secondary">{r.objectNumber || '未关联藏品号'}{r.objectName ? ` · ${r.objectName}` : ''}</Text>
          <Text type="secondary">{r.profileLabel || '其他'} · {r.resourceType}</Text>
        </Space>
      ),
    },
    {
      title: '预览',
      key: 'turntable',
      width: 140,
      render: (_, r) => (
        <ThreeDTurntablePreview
          title={r.label}
          previewData={getPreferredDetailVersion(r)?.preview_data}
          height={72}
        />
      ),
    },
    {
      title: '表现数', key: 'vc', width: 72, sorter: (a, b) => a.versions.length - b.versions.length,
      render: (_, r) => r.versions.length,
    },
    {
      title: '当前表现', key: 'current', width: 140,
      render: (_, r) => r.currentVersion ? (
        <Space direction="vertical" size={0}>
          <Tag color="blue">{getRepresentationLabel(r.currentVersion)}</Tag>
          <Text type="secondary">{r.currentVersion.version_label || 'v1'}</Text>
        </Space>
      ) : <Tag>未设置</Tag>,
    },
    {
      title: 'Web 展示', key: 'web', width: 140,
      render: (_, r) => r.webPreviewVersion ? (
        <Space direction="vertical" size={0}>
          <Tag color="green">{getRepresentationLabel(r.webPreviewVersion)}</Tag>
          <Text type="secondary">{getWebPreviewStatusLabel(r.webPreviewVersion.web_preview_status)}</Text>
        </Space>
      ) : <Tag color="default">未配置</Tag>,
    },
    {
      title: '保存层', key: 'tier', width: 100,
      render: (_, r) => (
        <Space direction="vertical" size={0}>
          <Tag color={r.storageTier === 'archive' ? 'blue' : r.storageTier === 'delivery' ? 'green' : 'gold'}>
            {getStorageTierLabel(r.storageTier || 'archive')}
          </Tag>
          <Text type="secondary">{getPreservationStatusLabel(r.preservationStatus || 'pending')}</Text>
        </Space>
      ),
    },
    { title: '文件', key: 'files', width: 60, render: (_, r) => r.totalFileCount },
    { title: '更新时间', key: 'updated', width: 140, sorter: (a, b) => (a.updatedAt || '').localeCompare(b.updatedAt || ''),
      render: (_, r) => r.updatedAt ? new Date(r.updatedAt).toLocaleDateString('zh-CN') : '-',
    },
    {
      title: '操作', key: 'action', width: 200, fixed: 'right',
      render: (_, r) => {
        const preferred = getPreferredDetailVersion(r);
        return (
          <Space wrap size={0}>
            <Button size="small" icon={<EyeOutlined />} disabled={!preferred}
              onClick={() => { if (preferred) void openDetail(preferred.id); }}>
              详情
            </Button>
            <Button size="small" icon={<DownloadOutlined />} disabled={!preferred}
              onClick={() => { if (preferred) window.location.href = `/api/three-d/resources/${preferred.id}/download`; }}>
              下载
            </Button>
            <Dropdown menu={{ items: [
              { key: 'set-current', label: '设为当前表现', disabled: !preferred, onClick: () => preferred && handlePatch(preferred.id, 'is_current', true) },
              { key: 'set-web', label: '设为 Web 展示', disabled: !preferred, onClick: () => preferred && handlePatch(preferred.id, 'is_web_preview', true) },
              { key: 'regen', label: '重生成预览', disabled: !preferred, onClick: () => preferred && handleRegenPreview(preferred.id) },
              { type: 'divider' },
              { key: 'delete', label: '删除', danger: true, disabled: !preferred, onClick: () => preferred && handleDelete(preferred.id) },
            ]}}>
              <Button size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  /* ─── 展开行(版本) ─── */
  const versionColumns: ColumnsType<ThreeDAssetSummary> = [
    {
      title: '表现', key: 'vl', width: 180,
      render: (_, r) => (
        <Space direction="vertical" size={0}>
          <Space wrap size={4}>
            <Tag color={r.is_current ? 'blue' : 'default'}>{getRepresentationLabel(r)}</Tag>
            <Tag>{r.version_label || 'v1'}</Tag>
            {r.is_current && <Tag color="gold">当前默认</Tag>}
            {r.is_web_preview && r.web_preview_status === 'ready' && <Tag color="green">Web 展示</Tag>}
          </Space>
          <Text type="secondary">#{r.version_order ?? 0} · {r.title || r.filename}</Text>
        </Space>
      ),
    },
    {
      title: 'Web 展示', key: 'wp', width: 100,
      render: (_, r) => (
        <Space direction="vertical" size={0}>
          <Tag color={r.web_preview_status === 'ready' ? 'green' : r.web_preview_status === 'pending' ? 'gold' : 'default'}>
            {getWebPreviewStatusLabel(r.web_preview_status || 'disabled')}
          </Tag>
          <Switch size="small" checked={r.is_web_preview} onChange={(v) => handlePatch(r.id, 'is_web_preview', v)} />
        </Space>
      ),
    },
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true, render: (v: string | null) => <Text>{v || '-'}</Text> },
    { title: '主文件', dataIndex: 'filename', key: 'fn', ellipsis: true, render: (v: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{v}</Paragraph> },
    { title: '文件数', dataIndex: 'file_count', key: 'fc', width: 60, render: (v: number | undefined) => v ?? 0 },
    {
      title: '状态', dataIndex: 'status', key: 'st', width: 80,
      render: (v: string) => <Tag color={v === 'ready' ? 'green' : v === 'error' ? 'red' : 'blue'}>{getRecordStatusLabel(v)}</Tag>,
    },
    {
      title: '操作', key: 'act', width: 280,
      render: (_, r) => (
        <Space size={0} wrap>
          <Button size="small" type={r.is_current ? 'primary' : 'default'} ghost={!r.is_current}
            onClick={() => handlePatch(r.id, 'is_current', true)}>
            设为当前
          </Button>
          <Button size="small" type={r.is_web_preview ? 'primary' : 'default'} ghost={!r.is_web_preview}
            onClick={() => { handlePatch(r.id, 'is_web_preview', true); handlePatch(r.id, 'web_preview_status', 'ready'); }}>
            设为 Web 展示
          </Button>
          <Button size="small" icon={<EyeOutlined />} onClick={() => void openDetail(r.id)}>详情</Button>
          <Button danger size="small" icon={<DeleteOutlined />} onClick={() => void handleDelete(r.id)} />
        </Space>
      ),
    },
  ];

  /* ─── Detail 快捷动作 ─── */
  const detailActions = detail ? (
    <Space wrap style={{ marginBottom: 16 }}>
      <Button icon={<SyncOutlined />} onClick={() => handleRegenPreview(detail.id)}>重生成预览</Button>
      <Button icon={<EditOutlined />} onClick={() => { setEditingField('title'); setEditValue(detail.title); }}>
        编辑标题
      </Button>
      <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(detail.id)}>删除</Button>
      <Button icon={<DownloadOutlined />} onClick={() => { window.location.href = detail.outputs.download_url; }}>下载资源包</Button>
    </Space>
  ) : null;

  const previewFiles = detail?.structure.files.filter((f) => f.role === 'oblique_photo') ?? [];

  return (
    <div>
      {/* ─── 工具栏 ─── */}
      <Card size="small" bordered={false} style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col flex="auto">
            <Space wrap>
              <Input
                placeholder="搜索数字对象 / 藏品号"
                prefix={<SearchOutlined />}
                allowClear
                style={{ width: 260 }}
                value={searchText}
                onChange={(e) => { setSearchText(e.target.value); setCurrentPage(1); }}
              />
              <Select placeholder="状态" allowClear style={{ width: 110 }} options={STATUS_FILTERS}
                value={filterStatus} onChange={(v) => { setFilterStatus(v); setCurrentPage(1); }} />
              <Select placeholder="模板" allowClear style={{ width: 110 }} options={PROFILE_FILTERS}
                value={filterProfile} onChange={(v) => { setFilterProfile(v); setCurrentPage(1); }} />
              <Select placeholder="保存层" allowClear style={{ width: 110 }} options={STORAGE_TIER_FILTERS}
                value={filterStorageTier} onChange={(v) => { setFilterStorageTier(v); setCurrentPage(1); }} />
              <Select placeholder="Web 展示" allowClear style={{ width: 120 }} options={WEB_PREVIEW_FILTERS}
                value={filterWebPreview} onChange={(v) => { setFilterWebPreview(v); setCurrentPage(1); }} />
            </Space>
          </Col>
          <Col>
            <Space>
              {selectedRowKeys.length > 0 && (
                <Space>
                  <Button size="small" onClick={() => batchSetWebPreview(true)}>批量启用展示</Button>
                  <Button size="small" onClick={() => batchSetWebPreview(false)}>批量停用展示</Button>
                  <Button size="small" onClick={() => setSelectedRowKeys([])}>取消选择</Button>
                </Space>
              )}
              <Button icon={<ReloadOutlined />} onClick={onRefresh}>刷新</Button>
              {onIngest && (
                <Button type="primary" icon={<UploadOutlined />} onClick={onIngest}>
                  入库新对象
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* ─── 异常提示 ─── */}
      {(() => {
        const errorGroups = groupedItems.filter((g) => g.versions.some((v) => v.status === 'error'));
        const missingPrimary = groupedItems.filter((g) => g.versions.length === 0 || !g.versions.some((v) => v.filename));
        if (errorGroups.length + missingPrimary.length === 0) return null;
        return (
          <Alert
            type="warning" showIcon style={{ marginBottom: 16 }}
            message={
              <Space>
                {errorGroups.length > 0 && <Text>{errorGroups.length} 个对象含异常表现</Text>}
                {missingPrimary.length > 0 && <Text>{missingPrimary.length} 个对象缺主文件</Text>}
                <Button size="small" type="link"
                  onClick={() => setFilterStatus('error')}>
                  查看异常
                </Button>
              </Space>
            }
          />
        );
      })()}

      {/* ─── 表格 ─── */}
      <Card title={`数字对象目录（${filteredGroups.length}）`} bordered={false}>
        <Table
          rowKey="key"
          loading={loading}
          dataSource={paginatedGroups}
          columns={groupColumns}
          scroll={{ x: 1200 }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          expandable={{
            expandedRowKeys,
            onExpandedRowsChange: (keys) => setExpandedRowKeys(keys),
            expandedRowRender: (r) => (
              <Table rowKey="id" pagination={false} dataSource={r.versions} columns={versionColumns} size="small" />
            ),
            rowExpandable: () => true,
          }}
          onChange={(pagination: TablePaginationConfig) => {
            if (pagination.current) setCurrentPage(pagination.current);
            if (pagination.pageSize) setPageSize(pagination.pageSize);
          }}
          pagination={{
            current: currentPage,
            pageSize,
            total: filteredGroups.length,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            showTotal: (total) => `共 ${total} 个数字对象`,
          }}
        />
      </Card>

      {/* ═══════ 详情 Drawer ═══════ */}
      <Drawer
        title={detail?.title || '三维资源详情'}
        open={detailOpen}
        onClose={() => { setDetailOpen(false); setDetail(null); setEditingField(null); }}
        width={1080}
      >
        {detailLoading || !detail ? (
          <div>加载中...</div>
        ) : (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {detailActions}

            {/* 编辑标题 */}
            {editingField === 'title' && (
              <Alert type="info" showIcon style={{ marginBottom: 8 }}
                message={
                  <Space>
                    <Input value={editValue} onChange={(e) => setEditValue(e.target.value)} style={{ width: 300 }} />
                    <Button type="primary" size="small" onClick={() => { handlePatch(detail.id, 'title', editValue); setEditingField(null); }}>
                      保存
                    </Button>
                    <Button size="small" onClick={() => setEditingField(null)}>取消</Button>
                  </Space>
                }
              />
            )}

            <Descriptions bordered column={{ xs: 1, sm: 2 }} size="small">
              <Descriptions.Item label="标题">{detail.title}</Descriptions.Item>
              <Descriptions.Item label="资源组">{detail.resource_group || '-'}</Descriptions.Item>
              <Descriptions.Item label="表现">{getRepresentationLabel(detail)}</Descriptions.Item>
              <Descriptions.Item label="版本">{detail.version_label || '原始版'}</Descriptions.Item>
              <Descriptions.Item label="当前表现">
                <Switch size="small" checked={detail.is_current} onChange={(v) => handlePatch(detail.id, 'is_current', v)} />
              </Descriptions.Item>
              <Descriptions.Item label="Web 展示">
                <Switch size="small" checked={detail.is_web_preview} onChange={(v) => { handlePatch(detail.id, 'is_web_preview', v); if (v) handlePatch(detail.id, 'web_preview_status', 'ready'); }} />
              </Descriptions.Item>
              <Descriptions.Item label="Web 状态">
                <Select size="small" style={{ width: 120 }} value={detail.web_preview_status || 'disabled'}
                  options={[
                    { value: 'ready', label: '已就绪' },
                    { value: 'pending', label: '准备中' },
                    { value: 'disabled', label: '未启用' },
                  ]}
                  onChange={(v) => handlePatch(detail.id, 'web_preview_status', v)}
                />
              </Descriptions.Item>
              <Descriptions.Item label="主文件">{detail.file.filename}</Descriptions.Item>
              <Descriptions.Item label="模板">{detail.profile_label || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">{getRecordStatusLabel(detail.status)}</Descriptions.Item>
              <Descriptions.Item label="保存层">{getStorageTierLabel(detail.preservation.storage_tier)}</Descriptions.Item>
              <Descriptions.Item label="保存状态">{getPreservationStatusLabel(detail.preservation.preservation_status)}</Descriptions.Item>
              <Descriptions.Item label="构成">{detail.structure.summary}</Descriptions.Item>
            </Descriptions>

            <Card size="small" title="轻量旋转预览">
              <ThreeDTurntablePreview title={detail.title} previewData={(detail.metadata_layers.raw_metadata as Record<string, unknown> | undefined)?.preview_data as never} height={200} />
            </Card>

            <ThreeDViewer viewer={detail.viewer} title={detail.title} />

            {previewFiles.length > 0 && (
              <Card size="small" title="预览图集">
                <Row gutter={[12, 12]}>
                  {previewFiles.map((f) => {
                    const url = f.preview_url || f.download_url;
                    return (
                      <Col key={`${f.role}-${f.actual_filename}-${f.sort_order ?? 0}`} xs={24} sm={12} md={8}>
                        <Card size="small" bodyStyle={{ padding: 12 }}>
                          {url && isImageMime(f.mime_type) ? (
                            <Image src={url} alt={f.actual_filename} style={{ width: '100%', maxHeight: 180, objectFit: 'cover' }}
                              fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" />
                          ) : (
                            <div style={{ width: '100%', height: 180, background: '#f5f5f5', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRadius: 6 }}>
                              <FileTextOutlined style={{ fontSize: 36, color: '#bfbfbf' }} />
                              <Text type="secondary" style={{ fontSize: 12, fontFamily: 'monospace' }}>{getFileExtUpper(f.actual_filename)}</Text>
                            </div>
                          )}
                          <Space direction="vertical" size={0} style={{ marginTop: 8 }}>
                            <Text strong style={{ fontSize: 12 }}>{f.actual_filename}</Text>
                            <Text type="secondary" style={{ fontSize: 11 }}>{f.role_label}</Text>
                          </Space>
                        </Card>
                      </Col>
                    );
                  })}
                </Row>
              </Card>
            )}

            <Card size="small" title={`文件构成（${detail.structure.files.length}）`}>
              <Table rowKey={(r) => `${r.role}-${r.actual_filename}-${r.sort_order ?? 0}`} pagination={false} size="small"
                columns={[
                  { title: '角色', dataIndex: 'role_label', key: 'rl' },
                  { title: '文件名', dataIndex: 'actual_filename', key: 'fn', render: (v: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{v}</Paragraph> },
                  { title: '大小', dataIndex: 'file_size', key: 'fs', render: (v: number) => `${(v / 1024 / 1024).toFixed(2)} MB` },
                  { title: '主文件', dataIndex: 'is_primary', key: 'ip', render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
                ]}
                dataSource={detail.structure.files}
              />
            </Card>

            <Row gutter={16}>
              <Col xs={24} lg={12}>
                <Card size="small" title="技术元数据">
                  {renderMetadataValue(detail.technical_metadata)}
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title="分层元数据">
                  {renderMetadataValue(detail.metadata_layers)}
                </Card>
              </Col>
            </Row>

            <Card size="small" title="生产链">
              <Table rowKey="id" pagination={false} size="small"
                dataSource={detail.production_records}
                columns={[
                  { title: '阶段', dataIndex: 'stage', key: 'stg' },
                  { title: '事件', dataIndex: 'event_type', key: 'evt' },
                  { title: '状态', dataIndex: 'status', key: 'sta', render: (v: string) => getRecordStatusLabel(v) },
                  { title: '执行人', dataIndex: 'actor', key: 'act', render: (v: string | null) => v || '-' },
                  { title: '时间', dataIndex: 'occurred_at', key: 'time' },
                ]}
              />
            </Card>
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default ThreeDCatalog;
