import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Descriptions, Input, Select, Space, Table, Tag, Typography } from 'antd';
import { EyeOutlined, FileTextOutlined, LinkOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import type { UnifiedResourceSourceSummary, UnifiedResourceSummary } from '../types/assets';

const { Paragraph, Text } = Typography;
const { Search } = Input;

const PROFILE_OPTIONS = [
  { value: 'other', label: '其他' },
  { value: 'movable_artifact', label: '可移动文物' },
  { value: 'immovable_artifact', label: '不可移动文物' },
  { value: 'art_photography', label: '艺术摄影' },
  { value: 'business_activity', label: '业务活动' },
  { value: 'panorama', label: '全景' },
  { value: 'ancient_tree', label: '古树' },
  { value: 'archaeology', label: '考古' },
  { value: 'model', label: '三维模型' },
  { value: 'point_cloud', label: '点云' },
  { value: 'oblique_photo', label: '倾斜摄影图像' },
  { value: 'package', label: '三维资源包' },
];

interface PlatformDirectoryProps {
  onPreview: (manifestUrl: string) => void;
  onOpenAssetDetail?: (assetId: number) => void;
  onOpenUnifiedResourceDetail?: (resourceId: string) => void;
}

const PlatformDirectory: React.FC<PlatformDirectoryProps> = ({
  onPreview,
  onOpenAssetDetail,
  onOpenUnifiedResourceDetail,
}) => {
  const [sources, setSources] = useState<UnifiedResourceSourceSummary[]>([]);
  const [resources, setResources] = useState<UnifiedResourceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<string | undefined>();
  const [previewState, setPreviewState] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [profileKey, setProfileKey] = useState<string | undefined>();

  const fetchDirectory = async (
    nextQuery = query,
    nextStatus = status,
    nextPreview = previewState,
    nextResourceType = resourceType,
    nextProfileKey = profileKey,
  ) => {
    setLoading(true);
    try {
      const params: Record<string, string | boolean> = {};
      if (nextQuery.trim()) params.q = nextQuery.trim();
      if (nextStatus) params.status = nextStatus;
      if (nextPreview === 'true') params.preview_enabled = true;
      if (nextPreview === 'false') params.preview_enabled = false;
      if (nextResourceType) params.resource_type = nextResourceType;
      if (nextProfileKey) params.profile_key = nextProfileKey;

      const [sourcesRes, resourcesRes] = await Promise.all([
        axios.get<UnifiedResourceSourceSummary[]>('/api/platform/sources'),
        axios.get<UnifiedResourceSummary[]>('/api/platform/resources', { params }),
      ]);
      setSources(sourcesRes.data);
      setResources(resourcesRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDirectory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns = [
    {
      title: '统一 ID',
      dataIndex: 'id',
      key: 'id',
      render: (value: string) => <Paragraph copyable style={{ marginBottom: 0 }}>{value}</Paragraph>,
    },
    { title: '来源', dataIndex: 'source_label', key: 'source_label' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'resource_type', key: 'resource_type' },
    {
      title: 'Profile',
      dataIndex: 'profile_label',
      key: 'profile_label',
      render: (value: string | undefined, record: UnifiedResourceSummary) => (
        <Tag>{value || record.profile_key || '其他'}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value: string, record: UnifiedResourceSummary) => (
        <Space wrap>
          <Tag color={record.preview_enabled ? 'green' : 'blue'}>
            {record.preview_enabled ? '可预览' : '不可预览'}
          </Tag>
          <Tag>{value}</Tag>
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (value: string) => <Text type="secondary">{value}</Text>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_value: unknown, record: UnifiedResourceSummary) => (
        <Space wrap>
          <Button icon={<EyeOutlined />} disabled={!record.preview_enabled} onClick={() => onPreview(record.manifest_url)}>
            预览
          </Button>
          <Button icon={<LinkOutlined />} onClick={() => onOpenUnifiedResourceDetail?.(record.id)}>
            统一详情
          </Button>
          <Button
            icon={<FileTextOutlined />}
            onClick={() => {
              const assetId = Number(record.source_id);
              if (!Number.isNaN(assetId) && onOpenAssetDetail) {
                onOpenAssetDetail(assetId);
              }
            }}
          >
            源详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="统一资源目录">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Space wrap style={{ width: '100%' }}>
            <Search
              allowClear
              placeholder="搜索标题、文件名、MIME 或资源 ID"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onSearch={(value) => fetchDirectory(value, status, previewState, resourceType, profileKey)}
              style={{ width: 320 }}
            />
            <Select
              allowClear
              placeholder="状态"
              value={status}
              onChange={(value) => {
                setStatus(value);
                fetchDirectory(query, value, previewState, resourceType, profileKey);
              }}
              style={{ width: 160 }}
              options={[
                { value: 'ready', label: 'ready' },
                { value: 'processing', label: 'processing' },
                { value: 'error', label: 'error' },
              ]}
            />
            <Select
              allowClear
              placeholder="预览状态"
              value={previewState}
              onChange={(value) => {
                setPreviewState(value);
                fetchDirectory(query, status, value, resourceType, profileKey);
              }}
              style={{ width: 160 }}
              options={[
                { value: 'true', label: '可预览' },
                { value: 'false', label: '不可预览' },
              ]}
            />
            <Select
              allowClear
              placeholder="资源类型"
              value={resourceType}
              onChange={(value) => {
                setResourceType(value);
                fetchDirectory(query, status, previewState, value, profileKey);
              }}
              style={{ width: 240 }}
              options={[
                { value: 'image_2d_cultural_object', label: '二维影像' },
                { value: 'three_d_model', label: '三维模型' },
                { value: 'three_d_point_cloud', label: '点云' },
                { value: 'three_d_oblique_photo', label: '倾斜摄影图像' },
                { value: 'three_d_package', label: '三维资源包' },
              ]}
            />
            <Select
              allowClear
              placeholder="Profile"
              value={profileKey}
              onChange={(value) => {
                setProfileKey(value);
                fetchDirectory(query, status, previewState, resourceType, value);
              }}
              style={{ width: 180 }}
              options={PROFILE_OPTIONS}
            />
            <Button icon={<ReloadOutlined />} onClick={() => fetchDirectory()} />
          </Space>

          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="来源数量">{sources.length}</Descriptions.Item>
            <Descriptions.Item label="资源总数">{resources.length}</Descriptions.Item>
          </Descriptions>
        </Space>

        <Alert
          style={{ marginTop: 16 }}
          type="info"
          showIcon
          message="统一目录会持续接入二维影像、三维资源等子系统，并在平台层提供统一检索与统一详情入口。"
        />
      </Card>

      <Card title="来源摘要">
        <Descriptions bordered column={1} size="small">
          {sources.map((source) => (
            <Descriptions.Item key={source.source_system} label={source.source_label}>
              <Space direction="vertical" size={0}>
                <Text>系统标识：{source.source_system}</Text>
                <Text>资源类型：{source.resource_type}</Text>
                <Text>资源数量：{source.resource_count}</Text>
                <Text>接入口：{source.entrypoint}</Text>
                <Text>健康状态：{source.healthy ? '健康' : '异常'}</Text>
              </Space>
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>

      <Card title="统一资源列表">
        <Table
          rowKey="id"
          loading={loading}
          dataSource={resources}
          columns={columns}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </Space>
  );
};

export default PlatformDirectory;
